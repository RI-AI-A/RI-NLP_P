"""LLM-powered Intent Classification (with rule overrides for MVP stability)"""
import re
from typing import Tuple
import structlog

from .config import nlp_config
from .llm_service import get_llm_service

logger = structlog.get_logger()


class LLMIntentClassifier:
    """
    We keep Ollama ON, but we prevent it from misclassifying critical operational queries.

    Rule overrides (first) -> LLM (second)
    """

    def __init__(self):
        self.config = nlp_config
        self.llm = get_llm_service()
        self._compile_rules()

    def _compile_rules(self) -> None:
        # Order matters: first match wins
        self.rules: list[tuple[str, re.Pattern]] = [
            # Situations / crowding / congestion MUST go to branch_status (or situations)
            ("branch_status", re.compile(r"\b(situation|situations|status)\b", re.I)),
            ("branch_status", re.compile(r"\b(crowding|crowded|congestion|overcrowd|too\s+busy)\b", re.I)),

            # KPI queries
            ("kpi_query", re.compile(r"\b(kpi|kpis|metric|metrics)\b", re.I)),
            ("kpi_query", re.compile(r"\b(traffic|footfall|sales|revenue|conversion|dwell|basket)\b", re.I)),

            # Tasks
            ("task_management", re.compile(r"\b(task|tasks|assign|assigned|todo|to\s+do|overdue|priority)\b", re.I)),

            # Promotions
            ("promotion_query", re.compile(r"\b(promo|promotion|discount|offer|deal)\b", re.I)),

            # Events (operational events only — not crowding)
            ("event_query", re.compile(r"\b(incident|accident|emergency|maintenance|repair|delivery|shipment|meeting)\b", re.I)),
        ]

    def _rule_intent(self, query: str) -> Tuple[str, float] | None:
        q = query.strip()
        if not q:
            return ("unknown", 0.0)

        for intent, pattern in self.rules:
            if pattern.search(q):
                return (intent, 0.95)
        return None

    async def predict(self, query: str) -> Tuple[str, float]:
        """
        Return (intent, confidence)
        """
        # 1) Rule override
        hit = self._rule_intent(query)
        if hit is not None:
            intent, conf = hit
            logger.info("Intent classified (rule override)", intent=intent, confidence=conf, query=query[:120])
            return intent, conf

        # 2) LLM fallback
        try:
            logger.info("Intent classified (LLM)", query=query[:120])

            prompt = f"""
You are an intent classifier for a retail analytics system.
Return ONLY JSON with keys: intent, confidence

Allowed intents:
{self.config.intent_classes}

Rules:
- If user asks about crowding/congestion/situations/status -> intent MUST be "branch_status"
- If user asks about KPIs/metrics (traffic, sales, conversion, dwell, basket) -> "kpi_query"
- If user asks about tasks -> "task_management"
- If user asks about promotions -> "promotion_query"
- If user asks about incidents/maintenance/delivery -> "event_query"

User query: {query}
"""

            out = await self.llm.generate_structured(
                prompt=prompt,
                temperature=0.0
            )

            intent = out.get("intent", "unknown")
            confidence = float(out.get("confidence", 0.0))

            if intent not in self.config.intent_classes:
                intent, confidence = "unknown", 0.0

            return intent, confidence

        except Exception as e:
            logger.error("LLM intent classification failed", error=str(e))
            return "unknown", 0.0


# Singleton
_llm_intent_classifier = None


def get_llm_intent_classifier() -> LLMIntentClassifier:
    global _llm_intent_classifier
    if _llm_intent_classifier is None:
        _llm_intent_classifier = LLMIntentClassifier()
    return _llm_intent_classifier
