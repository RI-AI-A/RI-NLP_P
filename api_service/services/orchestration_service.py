"""
Orchestration Service - Coordinates all NLP components
Now includes: Core Backend fetch (CORE_API_BASE_URL) to return real KPI values.
"""
from __future__ import annotations

from typing import Dict, Any, Tuple, Optional
from uuid import UUID

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

# Rule-based components
from nlp_service.intent_classifier import get_intent_classifier
from nlp_service.slot_filling import get_slot_filler
from nlp_service.query_router import get_query_router
from nlp_service.response_generator import get_response_generator

# LLM-powered components
from nlp_service.llm_intent_classifier import get_llm_intent_classifier
from nlp_service.llm_slot_filler import get_llm_slot_filler
from nlp_service.llm_response_generator import get_llm_response_generator

# Shared components
from nlp_service.guardrails import get_guardrails
from nlp_service.config import nlp_config
from db.models import NLPQueryLog
from schemas.nlp_response import NLPResponse

logger = structlog.get_logger()


class OrchestrationService:
    """Orchestrates the NLP pipeline with LLM or rule-based components"""

    def __init__(self):
        self.config = nlp_config

        # Rule-based fallback components
        self.intent_classifier = get_intent_classifier()
        self.slot_filler = get_slot_filler()
        self.response_generator = get_response_generator()

        # Initialize LLM components if enabled
        if self.config.use_llm:
            try:
                self.llm_intent_classifier = get_llm_intent_classifier()
                self.llm_slot_filler = get_llm_slot_filler()
                self.llm_response_generator = get_llm_response_generator()
                logger.info("LLM components initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize LLM components", error=str(e))
                if not self.config.llm_fallback_to_rules:
                    raise
                logger.warning("LLM initialization failed, will use rule-based fallback")

        # Shared components
        self.query_router = get_query_router()
        self.guardrails = get_guardrails()

        # Core backend base URL (you already added this to .env)
        # Example: CORE_API_BASE_URL=http://127.0.0.1:8000
        self.core_api_base_url: str = getattr(self.config, "core_api_base_url", "http://127.0.0.1:8000").rstrip("/")

    async def process_query(
        self,
        query: str,
        conversation_id: UUID,
        user_role: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Process a user query through the NLP pipeline and fetch from Core Backend if possible.
        """
        try:
            logger.info(
                "Processing query",
                query=query[:200],
                conversation_id=str(conversation_id),
                user_role=user_role,
                use_llm=self.config.use_llm
            )

            # Determine which pipeline to use
            use_llm = self.config.use_llm and hasattr(self, "llm_intent_classifier")

            # Step 1: Intent Classification
            intent, confidence = await self._classify_intent(query, use_llm)

            # Step 2: Slot Filling
            slots = await self._fill_slots(query, intent, use_llm)

            # Step 3: Query Routing
            routed_endpoint = await self.query_router.route(intent, slots)
            logger.info("Query routed", endpoint=routed_endpoint)

            # Step 4: Fetch Core Backend facts (REAL KPI values etc.)
            core_data = await self._fetch_core_data(routed_endpoint)

            # Step 5: Response Generation (use core_data if available)
            response_text, sources = await self._generate_response(
                query=query,
                intent=intent,
                slots=slots,
                routed_endpoint=routed_endpoint,
                use_llm=use_llm,
                core_data=core_data
            )

            # Step 6: Guardrails Check
            guardrail_result = await self.guardrails.check_all(
                query, intent, confidence, response_text
            )

            if not guardrail_result.passed:
                logger.warning("Guardrail check failed", reason=guardrail_result.reason)

                # Log rejected query (don’t crash if db fails)
                try:
                    await self._log_query(
                        db, conversation_id, user_role, query,
                        "rejected", confidence, None
                    )
                except Exception:
                    pass

                return {
                    "success": False,
                    "error": guardrail_result.reason
                }

            # Step 7: Log Query
            query_log = await self._log_query(
                db, conversation_id, user_role, query,
                intent, confidence, routed_endpoint
            )

            # Step 8: Build Response
            # Add "core_backend" as a source if we actually fetched core_data
            if core_data is not None:
                sources = list(set((sources or []) + ["core_backend"]))

            response = NLPResponse(
                intent=intent,
                slots=slots,
                routed_endpoint=routed_endpoint,
                response_text=response_text,
                confidence=confidence,
                sources=sources or []
            )

            logger.info(
                "Query processed successfully",
                query_id=str(query_log.id),
                intent=intent
            )

            return {
                "success": True,
                "data": response.model_dump(),
                "query_id": str(query_log.id)
            }

        except Exception as e:
            logger.error("Query processing failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": "An error occurred while processing your query. Please try again."
            }

    # -------------------------
    # Internal helpers
    # -------------------------

    async def _classify_intent(self, query: str, use_llm: bool) -> Tuple[str, float]:
        if use_llm:
            try:
                intent, confidence = await self.llm_intent_classifier.predict(query)
                logger.info("Intent classified (LLM)", intent=intent, confidence=confidence)
                return intent, float(confidence)
            except Exception as e:
                if self.config.llm_fallback_to_rules:
                    logger.warning("LLM intent classification failed, using fallback", error=str(e))
                else:
                    raise

        intent, confidence = await self.intent_classifier.predict(query)
        logger.info("Intent classified (rule-based/fallback)", intent=intent, confidence=confidence)
        return intent, float(confidence)

    async def _fill_slots(self, query: str, intent: str, use_llm: bool) -> Dict[str, Any]:
        if use_llm:
            try:
                slots = await self.llm_slot_filler.extract_slots(query, intent)
                logger.info("Slots extracted (LLM)", slots=slots)
                return slots
            except Exception as e:
                if self.config.llm_fallback_to_rules:
                    logger.warning("LLM slot extraction failed, using fallback", error=str(e))
                else:
                    raise

        slots = await self.slot_filler.extract_slots(query, intent)
        logger.info("Slots extracted (rule-based/fallback)", slots=slots)
        return slots

    async def _generate_response(
        self,
        query: str,
        intent: str,
        slots: Dict[str, Any],
        routed_endpoint: str,
        use_llm: bool,
        core_data: Optional[Dict[str, Any]]
    ) -> Tuple[str, list]:
        """
        If core_data exists, produce a concrete response with actual KPI values.
        Otherwise fallback to existing response generators.
        """
        # If we got real data from Core, prefer a deterministic formatted response
        if core_data is not None:
            text = self._format_core_response(intent=intent, slots=slots, routed_endpoint=routed_endpoint, core_data=core_data)
            return text, ["core_backend"]

        # Otherwise: normal behavior (LLM or rule-based generator)
        if use_llm:
            try:
                response_text, sources = await self.llm_response_generator.generate(
                    query, intent, slots, routed_endpoint
                )
                logger.info("Response generated (LLM)", sources=sources)
                return response_text, sources
            except Exception as e:
                if self.config.llm_fallback_to_rules:
                    logger.warning("LLM response generation failed, using fallback", error=str(e))
                else:
                    raise

        response_text, sources = await self.response_generator.generate(
            query, intent, slots, routed_endpoint
        )
        logger.info("Response generated (rule-based/fallback)", sources=sources)
        return response_text, sources

    async def _fetch_core_data(self, routed_endpoint: str) -> Optional[Dict[str, Any]]:
        """
        Calls Core Backend if the endpoint looks like a Core route.
        Expected core routes start with /api/v1/...
        """
        if not routed_endpoint or not isinstance(routed_endpoint, str):
            return None

        if not routed_endpoint.startswith("/api/"):
            # It's not a core endpoint (could be /unknown, /tasks, etc.)
            return None

        url = f"{self.core_api_base_url}{routed_endpoint}"
        logger.info("Fetching core backend data", url=url)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                logger.info("Core backend data fetched", keys=list(data.keys()) if isinstance(data, dict) else type(data).__name__)
                return data if isinstance(data, dict) else {"value": data}
        except Exception as e:
            logger.warning("Core backend fetch failed", url=url, error=str(e))
            return None

    def _format_core_response(
        self,
        intent: str,
        slots: Dict[str, Any],
        routed_endpoint: str,
        core_data: Dict[str, Any]
    ) -> str:
        """
        Turns core backend JSON into readable output.
        Specifically supports /api/v1/kpis response structure you showed:
        { "value": [ { ... }, ... ], "Count": 3 }
        """
        if intent == "kpi_query":
            branch_id = slots.get("branch_id", "unknown")
            kpi_type = slots.get("kpi_type", "general")

            items = core_data.get("value", [])
            count = core_data.get("Count", len(items) if isinstance(items, list) else 0)

            if not items:
                return (
                    f"I called the core KPIs endpoint but got no KPI rows back.\n"
                    f"- Branch: {branch_id}\n"
                    f"- KPI type: {kpi_type}\n"
                    f"- Endpoint used: {routed_endpoint}"
                )

            # show the first window (often they’re repeated while testing)
            first = items[0] if isinstance(items, list) else items

            # pick common fields that exist in your payload
            tw_start = first.get("time_window_start")
            tw_end = first.get("time_window_end")

            traffic_index = first.get("traffic_index")
            conversion_proxy = first.get("conversion_proxy")
            avg_dwell_time = first.get("avg_dwell_time")
            congestion_level = first.get("congestion_level")
            utilization_ratio = first.get("utilization_ratio")

            return (
                f"Here are the KPIs for **{branch_id}** (type: **{kpi_type}**) from Core Backend:\n\n"
                f"- Time window: {tw_start} → {tw_end}\n"
                f"- traffic_index: {traffic_index}\n"
                f"- conversion_proxy: {conversion_proxy}\n"
                f"- avg_dwell_time: {avg_dwell_time}\n"
                f"- congestion_level: {congestion_level}\n"
                f"- utilization_ratio: {utilization_ratio}\n\n"
                f"Rows returned: {count}\n"
                f"Endpoint used: {routed_endpoint}"
            )

        # Default formatting for other intents
        return (
            f"I fetched data from Core Backend.\n"
            f"Endpoint used: {routed_endpoint}\n"
            f"Raw keys: {list(core_data.keys())}"
        )

    async def _log_query(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        user_role: str,
        query_text: str,
        intent: str,
        confidence: float,
        routed_endpoint: Optional[str]
    ) -> NLPQueryLog:
        """Log query to database"""
        query_log = NLPQueryLog(
            conversation_id=conversation_id,
            user_role=user_role,
            query_text=query_text,
            intent=intent,
            confidence=confidence,
            routed_endpoint=routed_endpoint
        )

        db.add(query_log)
        await db.commit()
        await db.refresh(query_log)

        logger.debug("Query logged", query_id=str(query_log.id))
        return query_log


# Singleton instance
_orchestration_service = None


def get_orchestration_service() -> OrchestrationService:
    """Get or create orchestration service singleton"""
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = OrchestrationService()
    return _orchestration_service
