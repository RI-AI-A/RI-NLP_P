"""Slot Filling Module using spaCy NER and regex patterns"""
import re
from typing import Dict, Any, Optional
import spacy
from datetime import datetime, timedelta
from .config import nlp_config
import structlog

logger = structlog.get_logger()


class SlotFiller:
    """Extract entities and slots from user queries"""

    def __init__(self):
        self.config = nlp_config
        self.nlp = None
        self._load_models()
        self._compile_patterns()

    def _load_models(self):
        """Load spaCy model (optional). If not available, fall back to regex-only."""
        try:
            logger.info("Loading spaCy model (optional)", model=self.config.spacy_model)
            self.nlp = spacy.load(self.config.spacy_model)
            logger.info("spaCy model loaded successfully")
        except Exception as e:
            # IMPORTANT: do not crash the whole API if the model isn't installed.
            self.nlp = None
            logger.warning(
                "spaCy model not available; using regex-only slot filling",
                model=self.config.spacy_model,
                error=str(e),
            )

    def _compile_patterns(self):
        """Compile regex patterns for slot extraction"""

        # Time range patterns
        self.time_patterns = [
            (r"\b(yesterday)\b", "yesterday"),
            (r"\b(today)\b", "today"),
            (r"\b(last\s+week)\b", "last_week"),
            (r"\b(this\s+week)\b", "this_week"),
            (r"\b(last\s+month)\b", "last_month"),
            (r"\b(this\s+month)\b", "this_month"),
            (r"\b(last\s+quarter)\b", "last_quarter"),
            (r"\b(Q[1-4]\s+\d{4})\b", None),          # Q1 2024
            (r"\b(\d{4}-\d{2}-\d{2})\b", None),       # 2024-01-15
            (r"\b(\d{1,2}/\d{1,2}/\d{4})\b", None),   # 01/15/2024
        ]

        # Branch / Shelf-zone patterns
        # NOTE: In your project, "branch" means shelf/zone, so we support shelf_zone_1 directly.
        self.branch_patterns = [
            (r"\bbranch\s+([A-Z0-9_]+)\b", 1),
            (r"\bstore\s+([A-Z0-9_]+)\b", 1),
            (r"\blocation\s+([A-Z0-9_]+)\b", 1),
            (r"\boutlet\s+([A-Z0-9_]+)\b", 1),

            # NEW: shelf zone / zone identifiers
            (r"\b(shelf[_\s-]*zone[_\s-]*\d+)\b", 1),   # shelf_zone_1 / shelf zone 1 / shelf-zone-1
            (r"\b(zone[_\s-]*\d+)\b", 1),               # zone_1 / zone 1
        ]

        # KPI type patterns
        self.kpi_patterns = [
            (r"\b(traffic|footfall|foot\s+traffic)\b", "traffic"),
            (r"\b(sales|revenue)\b", "sales"),
            (r"\b(conversion|conversion\s+rate)\b", "conversion"),
            (r"\b(dwell\s+time|time\s+spent)\b", "dwell_time"),
            (r"\b(basket\s+size|average\s+basket)\b", "basket_size"),
            (r"\b(busy|busyness|occupancy)\b", "traffic"),
            (r"\b(kpi|kpis|metrics)\b", "general"),
        ]

        # Event type patterns
        self.event_patterns = [
            (r"\b(incident|accident|emergency)\b", "incident"),
            (r"\b(maintenance|repair)\b", "maintenance"),
            (r"\b(delivery|shipment)\b", "delivery"),
            (r"\b(meeting|conference)\b", "meeting"),
        ]

        # NEW: Situation type patterns (for /situations)
        self.situation_patterns = [
            (r"\b(crowding|congestion|overcrowd|too\s+busy|packed)\b", "CROWDING"),
            (r"\b(queue|long\s+line|waiting)\b", "QUEUE"),
            (r"\b(stockout|out\s+of\s+stock|missing\s+items)\b", "STOCKOUT"),
        ]

    async def extract_slots(self, query: str, intent: str) -> Dict[str, Any]:
        """
        Extract slots from query based on intent

        Args:
            query: User query text
            intent: Predicted intent

        Returns:
            Dictionary of extracted slots
        """
        slots: Dict[str, Any] = {}

        try:
            # spaCy NER (if available)
            if self.nlp is not None:
                doc = self.nlp(query)

                for ent in doc.ents:
                    if ent.label_ == "ORG" and "branch_id" not in slots:
                        slots["branch_id"] = ent.text
                    elif ent.label_ == "PERSON" and "employee_name" not in slots:
                        slots["employee_name"] = ent.text
                    elif ent.label_ == "DATE" and "time_range" not in slots:
                        slots["time_range"] = self._normalize_date(ent.text)

            # Regex extraction (always)
            slots.update(self._extract_time_range(query))
            slots.update(self._extract_branch_id(query))
            slots.update(self._extract_kpi_type(query))
            slots.update(self._extract_event_type(query))
            slots.update(self._extract_situation_type(query))

            # Intent-specific defaults
            if intent == "kpi_query":
                slots.setdefault("kpi_type", "general")

            logger.info("Slots extracted", slots=slots, intent=intent)

        except Exception as e:
            logger.error("Slot extraction failed", error=str(e), query=query)

        return slots

    def _extract_time_range(self, query: str) -> Dict[str, str]:
        query_lower = query.lower()
        for pattern, normalized in self.time_patterns:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                value = normalized if normalized else match.group(1)
                return {"time_range": value}
        return {}

    def _extract_branch_id(self, query: str) -> Dict[str, str]:
        for pattern, group_idx in self.branch_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                raw = match.group(group_idx)

                # Normalize formats like "shelf zone 1" -> "shelf_zone_1"
                normalized = re.sub(r"[\s-]+", "_", raw.strip().lower())

                return {"branch_id": normalized}
        return {}

    def _extract_kpi_type(self, query: str) -> Dict[str, str]:
        query_lower = query.lower()
        for pattern, normalized in self.kpi_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"kpi_type": normalized}
        return {}

    def _extract_event_type(self, query: str) -> Dict[str, str]:
        query_lower = query.lower()
        for pattern, normalized in self.event_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"event_type": normalized}
        return {}

    def _extract_situation_type(self, query: str) -> Dict[str, str]:
        query_lower = query.lower()
        for pattern, normalized in self.situation_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"situation_type": normalized}
        return {}

    def _normalize_date(self, date_str: str) -> str:
        date_str_lower = date_str.lower()

        if "yesterday" in date_str_lower:
            date = datetime.now() - timedelta(days=1)
            return date.strftime("%Y-%m-%d")
        if "today" in date_str_lower:
            return datetime.now().strftime("%Y-%m-%d")
        if "last week" in date_str_lower:
            return "last_week"
        if "this week" in date_str_lower:
            return "this_week"

        return date_str

    def validate_slots(self, slots: Dict[str, Any], intent: str) -> bool:
        required_slots = {
            "kpi_query": ["branch_id"],
            "branch_status": ["branch_id"],
            "performance_analysis": ["branch_id"],
            "task_management": [],
            "event_query": [],
            "promotion_query": [],
            "chitchat": [],
            "unknown": [],
        }
        required = required_slots.get(intent, [])
        return all(slot in slots for slot in required)


_slot_filler = None


def get_slot_filler() -> SlotFiller:
    global _slot_filler
    if _slot_filler is None:
        _slot_filler = SlotFiller()
    return _slot_filler
