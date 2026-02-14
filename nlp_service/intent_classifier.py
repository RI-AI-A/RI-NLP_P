"""Intent Classification Module"""
import os
import re
from typing import Dict, Tuple, Optional
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline
)
from .config import nlp_config
import structlog

logger = structlog.get_logger()


class IntentClassifier:
    """
    Intent classification with:
      1) lightweight rule-based routing for MVP stability (FAST + deterministic)
      2) fine-tuned model if available
      3) optional zero-shot fallback (if enabled / available)

    Why this change:
      - Your query "Show situations for shelf_zone_1" was classified as "chitchat".
      - For operational systems, some keywords MUST deterministically map to intents
        (e.g., "crowding", "congestion", "situations") to avoid LLM randomness.
    """

    def __init__(self):
        self.config = nlp_config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.zero_shot_classifier = None

        # Rule patterns compiled once
        self._compile_rules()
        self._load_models()

    def _compile_rules(self) -> None:
        """Compile regex rules for stable MVP intent detection."""
        # NOTE: order matters (first match wins)
        self._rules: list[tuple[str, re.Pattern]] = [
            # Situations / crowding / congestion should NEVER become chitchat/events
            ("branch_status", re.compile(r"\b(situation|situations|status)\b", re.I)),
            ("branch_status", re.compile(r"\b(crowding|crowded|congestion|overcrowd|packed|too\s+busy)\b", re.I)),

            # KPI queries
            ("kpi_query", re.compile(r"\b(kpi|kpis|metric|metrics|traffic|footfall|sales|revenue|conversion|dwell|basket)\b", re.I)),
            ("kpi_query", re.compile(r"\b(show|get|give|what\s+is|what\s+are)\b.*\b(kpi|kpis|traffic|sales|revenue|conversion|dwell|basket)\b", re.I)),

            # Recommendations / performance analysis
            ("performance_analysis", re.compile(r"\b(why|analy[sz]e|analysis|diagnos|insight|recommend|improve|underperform|performance)\b", re.I)),

            # Tasks
            ("task_management", re.compile(r"\b(task|tasks|assign|assigned|to\s+do|todo|overdue|priority)\b", re.I)),

            # Events (ONLY real operational events, not "crowding")
            ("event_query", re.compile(r"\b(incident|accident|emergency|maintenance|repair|delivery|shipment|meeting)\b", re.I)),

            # Promotions
            ("promotion_query", re.compile(r"\b(promo|promotion|discount|offer|deal)\b", re.I)),

            # Chitchat (keep last so it doesn’t steal real intents)
            ("chitchat", re.compile(r"^\s*(hi|hello|hey|thanks|thank\s+you|bye|goodbye)\b", re.I)),
        ]

    def _load_models(self):
        """Load intent classification models"""
        try:
            # Try to load fine-tuned model if exists
            if os.path.exists(self.config.intent_model_path):
                logger.info(
                    "Loading fine-tuned intent classifier",
                    path=self.config.intent_model_path
                )
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.config.intent_model_path
                )
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.config.intent_model_path
                ).to(self.device)
            else:
                logger.warning(
                    "Fine-tuned model not found; MVP will use rules first and optional zero-shot second",
                    path=self.config.intent_model_path
                )

            # Optional zero-shot classifier
            # If you want it: set env USE_ZERO_SHOT_INTENT=true
            use_zero_shot = os.getenv("USE_ZERO_SHOT_INTENT", "false").lower() == "true"
            if use_zero_shot:
                logger.info("Loading zero-shot classifier")
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli",
                    device=0 if self.device == "cuda" else -1
                )
                logger.info("Zero-shot classifier loaded")
            else:
                logger.info("Zero-shot classifier disabled (USE_ZERO_SHOT_INTENT=false)")

            logger.info("Intent classifier initialized successfully")

        except Exception as e:
            logger.error("Failed to load intent classifier", error=str(e))
            raise

    async def predict(self, query: str) -> Tuple[str, float]:
        """
        Predict intent for a query

        Priority:
          1) Rules (stable)
          2) Fine-tuned model (if exists)
          3) Zero-shot (if enabled)
          4) Unknown
        """
        try:
            # 1) RULES
            rule_intent = self._predict_rules(query)
            if rule_intent is not None:
                # high confidence because deterministic
                logger.info("Intent predicted (rules)", intent=rule_intent, confidence=0.95)
                return rule_intent, 0.95

            # 2) Fine-tuned model if available
            if self.model is not None and self.tokenizer is not None:
                return await self._predict_finetuned(query)

            # 3) Zero-shot if enabled
            if self.zero_shot_classifier is not None:
                return await self._predict_zero_shot(query)

            # 4) fallback
            return "unknown", 0.0

        except Exception as e:
            logger.error("Intent prediction failed", error=str(e), query=query)
            return "unknown", 0.0

    def _predict_rules(self, query: str) -> Optional[str]:
        q = query.strip()
        if not q:
            return "unknown"

        for intent, pattern in self._rules:
            if pattern.search(q):
                return intent
        return None

    async def _predict_finetuned(self, query: str) -> Tuple[str, float]:
        """Predict using fine-tuned model"""
        inputs = self.tokenizer(
            query,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            confidence, predicted_idx = torch.max(probs, dim=-1)

        intent = self.config.intent_classes[predicted_idx.item()]
        confidence_score = float(confidence.item())

        # Apply confidence threshold
        if confidence_score < self.config.intent_confidence_threshold:
            intent = "unknown"

        logger.info("Intent predicted (fine-tuned)", intent=intent, confidence=confidence_score)
        return intent, confidence_score

    async def _predict_zero_shot(self, query: str) -> Tuple[str, float]:
        """Predict using zero-shot classifier"""
        result = self.zero_shot_classifier(
            query,
            candidate_labels=self.config.intent_classes,
            multi_label=False
        )

        intent = result["labels"][0]
        confidence = float(result["scores"][0])

        if confidence < self.config.intent_confidence_threshold:
            intent = "unknown"

        logger.info("Intent predicted (zero-shot)", intent=intent, confidence=confidence)
        return intent, confidence

    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            "kpi_query": "Query about Key Performance Indicators",
            "branch_status": "Query about branch status / situations / congestion",
            "performance_analysis": "Performance diagnostics and recommendations",
            "task_management": "Task creation, assignment, or retrieval",
            "event_query": "Query about incidents, maintenance, deliveries, meetings",
            "promotion_query": "Query about promotions or offers",
            "chitchat": "Casual conversation",
            "unknown": "Intent could not be determined"
        }
        return descriptions.get(intent, "Unknown intent")


# Singleton instance
_intent_classifier = None


def get_intent_classifier() -> IntentClassifier:
    """Get or create intent classifier singleton"""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
