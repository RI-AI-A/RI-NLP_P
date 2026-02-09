"""LLM-powered Intent Classification"""
from typing import Tuple
import structlog

from .llm_service import get_llm_service
from .prompts import format_intent_prompt, INTENT_SCHEMA
from .config import nlp_config

logger = structlog.get_logger()


class LLMIntentClassifier:
    """Intent classification using LLM"""
    
    def __init__(self):
        self.config = nlp_config
        self.llm_service = get_llm_service()
    
    async def predict(self, query: str) -> Tuple[str, float]:
        """
        Predict intent for a query using LLM
        
        Args:
            query: User query text
            
        Returns:
            Tuple of (intent, confidence)
        """
        try:
            logger.info("Classifying intent with LLM", query=query[:100])
            
            # Format prompt
            prompt = format_intent_prompt(query)
            
            # Get structured response from LLM
            response = await self.llm_service.generate_structured(
                prompt=prompt,
                temperature=0.3  # Lower temperature for classification
            )
            
            # Extract intent and confidence
            intent = response.get("intent", "unknown")
            confidence = response.get("confidence", 0.0)
            reasoning = response.get("reasoning", "")
            
            # Apply confidence threshold
            if confidence < self.config.intent_confidence_threshold:
                logger.warning("Low confidence intent", 
                             intent=intent, 
                             confidence=confidence,
                             threshold=self.config.intent_confidence_threshold)
                intent = "unknown"
            
            logger.info("Intent classified with LLM", 
                       intent=intent, 
                       confidence=confidence,
                       reasoning=reasoning)
            
            return intent, confidence
            
        except Exception as e:
            logger.error("LLM intent classification failed", error=str(e), query=query)
            # Return unknown with low confidence on error
            return "unknown", 0.0
    
    def get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent"""
        descriptions = {
            "kpi_query": "Query about Key Performance Indicators",
            "branch_status": "Query about branch status or information",
            "performance_analysis": "Performance comparison or analysis request",
            "task_management": "Task creation, assignment, or retrieval",
            "event_query": "Query about events or incidents",
            "promotion_query": "Query about promotions or offers",
            "chitchat": "Casual conversation",
            "unknown": "Intent could not be determined"
        }
        return descriptions.get(intent, "Unknown intent")


# Singleton instance
_llm_intent_classifier = None


def get_llm_intent_classifier() -> LLMIntentClassifier:
    """Get or create LLM intent classifier singleton"""
    global _llm_intent_classifier
    if _llm_intent_classifier is None:
        _llm_intent_classifier = LLMIntentClassifier()
    return _llm_intent_classifier
