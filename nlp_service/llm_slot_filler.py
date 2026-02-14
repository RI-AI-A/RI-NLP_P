"""LLM-powered Slot Filling"""
from typing import Dict, Any, Optional
import re
import structlog

from .llm_service import get_llm_service
from .prompts import format_slot_filling_prompt
from .config import nlp_config

logger = structlog.get_logger()


class LLMSlotFiller:
    """Slot filling using LLM"""

    def __init__(self):
        self.config = nlp_config
        self.llm_service = get_llm_service()

        # Heuristics: in your project "branch" can be a shelf/zone id
        # Examples: shelf_zone_1, shelfzone1, zone_12, aisle_3, section_A
        self._zone_like_patterns = [
            re.compile(r"^shelf[_-]?zone[_-]?\w+$", re.IGNORECASE),
            re.compile(r"^zone[_-]?\w+$", re.IGNORECASE),
            re.compile(r"^aisle[_-]?\w+$", re.IGNORECASE),
            re.compile(r"^section[_-]?\w+$", re.IGNORECASE),
            re.compile(r"^branch[_-]?\w+$", re.IGNORECASE),
            re.compile(r"^[A-Z]\d*$"),  # A, B, A1, B2 etc.
        ]

    async def extract_slots(self, query: str, intent: str) -> Dict[str, Any]:
        """
        Extract slots from query using LLM

        Args:
            query: User query text
            intent: Predicted intent (for context)

        Returns:
            Dictionary of extracted slots
        """
        try:
            logger.info("Extracting slots with LLM", query=query[:100], intent=intent)

            # Add a small intent hint without touching prompts.py
            # This improves consistency (branch_id vs product_name) for KPI/status intents.
            intent_hint = (
                "System hint: In this retail system, 'branch_id' may refer to a shelf/zone id "
                "like 'shelf_zone_1'. If the user mentions a shelf zone, put it in branch_id.\n\n"
            )

            prompt = intent_hint + format_slot_filling_prompt(query)

            response = await self.llm_service.generate_structured(
                prompt=prompt,
                temperature=0.2  # low temp for extraction stability
            )

            if not isinstance(response, dict):
                logger.warning("LLM structured response is not a dict", response_type=str(type(response)))
                return {}

            # 1) Keep only allowed slot keys (avoid hallucinated keys)
            allowed = set(self.config.slot_entities)
            slots_raw = {k: v for k, v in response.items() if k in allowed and v is not None}

            # 2) Normalize time_range if present
            if "time_range" in slots_raw and isinstance(slots_raw["time_range"], str):
                slots_raw["time_range"] = self.normalize_time_range(slots_raw["time_range"])

            # 3) Normalize KPI type
            slots_raw["kpi_type"] = self._normalize_kpi_type(slots_raw.get("kpi_type"))

            # 4) Fix common confusion: shelf_zone_x goes to branch_id (not product_name)
            slots = self._fix_branch_vs_product(slots_raw, intent=intent)

            logger.info("Slots extracted with LLM", slots=slots)
            return slots

        except Exception as e:
            logger.error("LLM slot extraction failed", error=str(e), query=query)
            return {}

    def _normalize_kpi_type(self, kpi_type: Optional[Any]) -> str:
        """
        Normalize kpi_type into something your router/core API can understand.
        - If missing/empty -> "general"
        - If LLM returns "KPIs" or "kpi" -> "general"
        - If value matches known KPI types -> keep it
        """
        if not kpi_type:
            return "general"

        if not isinstance(kpi_type, str):
            return "general"

        val = kpi_type.strip().lower()

        if val in {"kpi", "kpis", "all", "overall", "general"}:
            return "general"

        # Map synonyms to your configured KPI types
        synonym_map = {
            "foot traffic": "traffic",
            "footfall": "traffic",
            "traffic index": "traffic",
            "revenue": "sales",  # if your core API treats revenue under sales, keep this mapping
        }
        if val in synonym_map:
            val = synonym_map[val]

        # Keep only known KPI types; otherwise fallback to general
        known = {k.lower() for k in self.config.kpi_types}
        return val if val in known else "general"

    def _looks_like_zone_or_branch(self, text: str) -> bool:
        """Return True if text looks like a shelf/zone/branch identifier."""
        if not text or not isinstance(text, str):
            return False
        t = text.strip()
        return any(p.match(t) for p in self._zone_like_patterns)

    def _fix_branch_vs_product(self, slots: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """
        For KPI / status intents, treat shelf_zone_x as branch_id.
        """
        intent = (intent or "").strip().lower()

        intents_that_need_branch = {"kpi_query", "branch_status", "performance_analysis"}

        branch_id = slots.get("branch_id")
        product_name = slots.get("product_name")

        # If branch_id is missing but product_name looks like a zone id, move it.
        if intent in intents_that_need_branch:
            if (not branch_id) and isinstance(product_name, str) and self._looks_like_zone_or_branch(product_name):
                slots["branch_id"] = product_name.strip()
                slots.pop("product_name", None)
                logger.info("Moved product_name to branch_id (zone-like id)", branch_id=slots["branch_id"])

        # If BOTH exist and are identical, keep branch_id only
        if branch_id and product_name and isinstance(branch_id, str) and isinstance(product_name, str):
            if branch_id.strip().lower() == product_name.strip().lower():
                slots.pop("product_name", None)

        return slots

    def normalize_time_range(self, time_range: str) -> str:
        """Normalize time range expressions (optional enhancement)"""
        normalizations = {
            "today": "today",
            "yesterday": "yesterday",
            "last week": "last_week",
            "this week": "this_week",
            "last month": "last_month",
            "this month": "this_month",
        }
        return normalizations.get(time_range.lower().strip(), time_range)


# Singleton instance
_llm_slot_filler = None


def get_llm_slot_filler() -> LLMSlotFiller:
    """Get or create LLM slot filler singleton"""
    global _llm_slot_filler
    if _llm_slot_filler is None:
        _llm_slot_filler = LLMSlotFiller()
    return _llm_slot_filler
