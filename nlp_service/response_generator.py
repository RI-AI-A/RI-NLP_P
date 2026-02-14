"""Response Generator with RAG-lite + Core Backend Fetch (MVP)"""
from typing import List, Dict, Any, Tuple, Optional
from .retrieval import get_retrieval_system, Document
from .config import nlp_config
import httpx
import structlog

logger = structlog.get_logger()


class ResponseGenerator:
    """Generate responses using retrieved context + optional core backend facts"""

    def __init__(self):
        self.config = nlp_config

        # NOTE: all generators are async now (because we may call core backend)
        self.response_templates = {
            "kpi_query": self._generate_kpi_response,
            "branch_status": self._generate_branch_status_response,
            "task_management": self._generate_task_response,
            "event_query": self._generate_event_response,
            "promotion_query": self._generate_promotion_response,
            "chitchat": self._generate_chitchat_response,
            "performance_analysis": self._generate_performance_response,
            "unknown": self._generate_unknown_response
        }

    async def generate(
        self,
        query: str,
        intent: str,
        slots: Dict[str, Any],
        routed_endpoint: str
    ) -> Tuple[str, List[str]]:
        """
        Generate response with retrieved context.

        If routed_endpoint points to your CORE backend (like /api/v1/kpis?...),
        we will fetch it and include a short summary in the answer.
        """
        try:
            # 1) Retrieve relevant context (RAG-lite)
            retrieval_system = await get_retrieval_system()
            contexts = await retrieval_system.search(query, top_k=3)

            # 2) Optional: fetch facts from core backend (if endpoint looks like a path)
            core_facts = await self._fetch_core_json(routed_endpoint)

            # 3) Generate response using template
            generator_func = self.response_templates.get(intent, self._generate_unknown_response)
            response_text = await generator_func(query, slots, contexts, routed_endpoint, core_facts)

            # 4) Extract sources
            sources = list(
                set([ctx[0].metadata.get("source", "unknown") for ctx in contexts])
            )

            # If we successfully called core backend, add a source tag
            if core_facts is not None:
                sources.append("core_backend")
                sources = list(set(sources))

            logger.info(
                "Response generated",
                intent=intent,
                sources=sources,
                context_count=len(contexts),
                core_facts_attached=core_facts is not None
            )

            return response_text, sources

        except Exception as e:
            logger.error("Response generation failed", error=str(e), exc_info=True)
            return "I apologize, but I encountered an error processing your request.", []

    # -------------------------
    # Core backend integration
    # -------------------------
    async def _fetch_core_json(self, endpoint: str) -> Optional[Any]:
        """
        Fetch JSON from core backend if endpoint looks like a core path.
        Returns parsed JSON (dict/list) or None if not fetched.
        """
        if not endpoint or not isinstance(endpoint, str):
            return None

        # QueryRouter should return something like "/api/v1/kpis?..."
        if not endpoint.startswith("/"):
            return None

        base_url = (self.config.core_api_base_url or "").rstrip("/")
        if not base_url:
            logger.warning("CORE_API_BASE_URL is missing; skipping core fetch")
            return None

        url = f"{base_url}{endpoint}"

        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.get(url)

            if resp.status_code >= 400:
                logger.warning(
                    "Core backend returned error",
                    url=url,
                    status_code=resp.status_code,
                    body=resp.text[:300]
                )
                return {"_core_error": f"HTTP {resp.status_code}", "_core_url": url}

            # Try JSON
            try:
                return resp.json()
            except Exception:
                logger.warning("Core backend response was not JSON", url=url)
                return {"_core_error": "Non-JSON response", "_core_url": url}

        except Exception as e:
            logger.warning("Core backend fetch failed", url=url, error=str(e))
            return {"_core_error": str(e), "_core_url": url}

    def _format_core_summary(self, core_facts: Any) -> str:
        """
        Make a short human-readable summary of whatever JSON came back.
        MVP: keep it safe and small.
        """
        if core_facts is None:
            return ""

        # If we returned an error wrapper
        if isinstance(core_facts, dict) and "_core_error" in core_facts:
            return f"Core backend fetch issue: {core_facts.get('_core_error')} (url: {core_facts.get('_core_url')})"

        # Common shapes
        if isinstance(core_facts, dict):
            # Show a few keys only
            keys = list(core_facts.keys())
            preview_keys = keys[:8]
            preview = {k: core_facts.get(k) for k in preview_keys}
            return f"Core data (preview): {preview}"

        if isinstance(core_facts, list):
            if not core_facts:
                return "Core data: []"
            # Show first item only
            first = core_facts[0]
            return f"Core data (first item): {first}"

        return f"Core data: {str(core_facts)[:300]}"

    # -------------------------
    # Response templates (async)
    # -------------------------
    async def _generate_kpi_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        branch_id = slots.get("branch_id", "the specified branch")
        time_range = slots.get("time_range", "the requested period")
        kpi_type = slots.get("kpi_type", "general")

        # Find relevant KPI explanation
        kpi_context = ""
        for doc, _score in contexts:
            if doc.metadata.get("type") == "kpi_explanation":
                if kpi_type in doc.text.lower() or doc.metadata.get("kpi") == kpi_type:
                    kpi_context = doc.text
                    break

        response = f"I'll retrieve the {kpi_type} KPI data for {branch_id} during {time_range}."

        if kpi_context:
            response += f"\n\nContext: {kpi_context}"

        # Attach real core backend facts if available
        core_summary = self._format_core_summary(core_facts)
        if core_summary:
            response += f"\n\n{core_summary}"

        response += f"\n\nCore endpoint used: {endpoint}"
        return response

    async def _generate_branch_status_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        branch_id = slots.get("branch_id", "the specified branch")

        response = f"I'll check the current status of {branch_id}. This includes occupancy levels, staff on duty, and any operational alerts."

        core_summary = self._format_core_summary(core_facts)
        if core_summary:
            response += f"\n\n{core_summary}"

        response += f"\n\nCore endpoint used: {endpoint}"
        return response

    async def _generate_task_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        employee_name = slots.get("employee_name")

        if employee_name:
            response = f"I'll retrieve tasks assigned to {employee_name}."
        else:
            response = "I'll retrieve the task list."

        # Add context about task management
        for doc, _score in contexts:
            if doc.metadata.get("source") == "task_docs":
                response += f"\n\n{doc.text}"
                break

        core_summary = self._format_core_summary(core_facts)
        if core_summary:
            response += f"\n\n{core_summary}"

        response += f"\n\nCore endpoint used: {endpoint}"
        return response

    async def _generate_event_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        event_type = slots.get("event_type", "all")
        time_range = slots.get("time_range", "recent")

        response = f"I'll retrieve {event_type} events from {time_range}."

        core_summary = self._format_core_summary(core_facts)
        if core_summary:
            response += f"\n\n{core_summary}"

        response += f"\n\nCore endpoint used: {endpoint}"
        return response

    async def _generate_promotion_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        product_name = slots.get("product_name")

        if product_name:
            response = f"I'll check for promotions related to {product_name}."
        else:
            response = "I'll retrieve current promotions."

        # Add business rules context
        for doc, _score in contexts:
            if doc.metadata.get("source") == "business_rules" and "promotion" in doc.text.lower():
                response += f"\n\nNote: {doc.text}"
                break

        core_summary = self._format_core_summary(core_facts)
        if core_summary:
            response += f"\n\n{core_summary}"

        response += f"\n\nCore endpoint used: {endpoint}"
        return response

    async def _generate_chitchat_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        query_lower = query.lower()

        if any(greeting in query_lower for greeting in ["hello", "hi", "hey"]):
            return "Hello! I'm here to help you with retail analytics queries. You can ask me about KPIs, branch status, tasks, events, or promotions."
        elif any(word in query_lower for word in ["how are you", "how's it going"]):
            return "I'm functioning well, thank you! How can I assist you with your retail analytics needs today?"
        elif any(word in query_lower for word in ["thank", "thanks"]):
            return "You're welcome! Let me know if you need anything else."
        elif any(word in query_lower for word in ["bye", "goodbye"]):
            return "Goodbye! Feel free to return if you have more questions."
        else:
            return "I'm here to help with retail analytics. You can ask about KPIs, branch performance, tasks, events, or promotions."

    async def _generate_performance_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        branch_id = slots.get("branch_id", "the branch")
        response = f"I've analyzed the performance of {branch_id}."

        # Add context from retrieval
        if contexts:
            relevant_context = ""
            for doc, _score in contexts:
                text_lower = doc.text.lower()
                if any(term in text_lower for term in ["performance", "issue", "problem", "recommendation", "traffic", "underperforming"]):
                    relevant_context = doc.text
                    break

            if relevant_context:
                response += f"\n\nContext: {relevant_context}"

        core_summary = self._format_core_summary(core_facts)
        if core_summary:
            response += f"\n\n{core_summary}"

        response += f"\n\nCore endpoint used: {endpoint}"
        return response

    async def _generate_unknown_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str,
        core_facts: Any
    ) -> str:
        response = "I'm not sure I understand your request. I can help you with:\n"
        response += "• KPI queries (e.g., 'Show me sales for shelf_zone_1')\n"
        response += "• Branch status (e.g., 'How busy is shelf_zone_2?')\n"
        response += "• Task management (e.g., 'What tasks are assigned to John?')\n"
        response += "• Events (e.g., 'Any incidents today?')\n"
        response += "• Promotions (e.g., 'Current promotions?')\n"

        if contexts:
            response += f"\n\nYou might find this helpful: {contexts[0][0].text}"

        return response


# Singleton instance
_response_generator = None


def get_response_generator() -> ResponseGenerator:
    """Get or create response generator singleton"""
    global _response_generator
    if _response_generator is None:
        _response_generator = ResponseGenerator()
    return _response_generator
