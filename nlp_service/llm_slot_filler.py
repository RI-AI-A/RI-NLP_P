"""LLM-powered Slot Filling"""
from typing import Dict, Any
import structlog

from .llm_service import get_llm_service
from .prompts import format_slot_filling_prompt, SLOT_SCHEMA
from .config import nlp_config

logger = structlog.get_logger()


class LLMSlotFiller:
    """Slot filling using LLM"""
    
    def __init__(self):
        self.config = nlp_config
        self.llm_service = get_llm_service()
    
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
            
            # Format prompt with few-shot examples
            prompt = format_slot_filling_prompt(query)
            
            # Get structured response from LLM
            response = await self.llm_service.generate_structured(
                prompt=prompt,
                temperature=0.2  # Very low temperature for extraction
            )
            
            # Filter out None values for cleaner output
            slots = {k: v for k, v in response.items() if v is not None}
            
            logger.info("Slots extracted with LLM", slots=slots)
            
            return slots
            
        except Exception as e:
            logger.error("LLM slot extraction failed", error=str(e), query=query)
            # Return empty slots on error
            return {}
    
    def normalize_time_range(self, time_range: str) -> str:
        """Normalize time range expressions (optional enhancement)"""
        # This could be expanded with more sophisticated normalization
        normalizations = {
            "today": "today",
            "yesterday": "yesterday",
            "last week": "last_week",
            "this week": "this_week",
            "last month": "last_month",
            "this month": "this_month",
        }
        return normalizations.get(time_range.lower(), time_range)


# Singleton instance
_llm_slot_filler = None


def get_llm_slot_filler() -> LLMSlotFiller:
    """Get or create LLM slot filler singleton"""
    global _llm_slot_filler
    if _llm_slot_filler is None:
        _llm_slot_filler = LLMSlotFiller()
    return _llm_slot_filler
