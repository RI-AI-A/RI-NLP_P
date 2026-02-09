"""LLM-powered Response Generation"""
from typing import List, Dict, Any, Tuple
import structlog

from .llm_service import get_llm_service
from .prompts import format_response_prompt
from .retrieval import get_retrieval_system, Document

logger = structlog.get_logger()


class LLMResponseGenerator:
    """Generate responses using LLM with RAG"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
        self.retrieval_system = None  # Will be initialized on first use
    
    async def _ensure_retrieval_system(self):
        """Lazy initialization of retrieval system"""
        if self.retrieval_system is None:
            self.retrieval_system = await get_retrieval_system()
    
    async def generate(
        self,
        query: str,
        intent: str,
        slots: Dict[str, Any],
        routed_endpoint: str
    ) -> Tuple[str, List[str]]:
        """
        Generate response using LLM with retrieved context
        
        Args:
            query: Original user query
            intent: Predicted intent
            slots: Extracted slots
            routed_endpoint: Routed API endpoint
            
        Returns:
            Tuple of (response_text, sources)
        """
        try:
            logger.info("Generating response with LLM", 
                       intent=intent, 
                       endpoint=routed_endpoint)
            
            # Ensure retrieval system is initialized
            await self._ensure_retrieval_system()
            
            # Retrieve relevant context
            contexts = await self.retrieval_system.search(query, top_k=3)
            
            # Extract document texts and sources (note: Document uses .text not .content)
            context_texts = [doc.text for doc, score in contexts]
            sources = list(set([doc.metadata.get("source", "knowledge_base") 
                              for doc, score in contexts]))
            
            # Format prompt with context
            prompt = format_response_prompt(
                query=query,
                intent=intent,
                slots=slots,
                routed_endpoint=routed_endpoint,
                context_docs=context_texts
            )
            
            # Generate response
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.7  # Moderate temperature for natural responses
            )
            
            response_text = response.content.strip()
            
            logger.info("Response generated with LLM", 
                       length=len(response_text),
                       sources=sources)
            
            return response_text, sources
            
        except Exception as e:
            logger.error("LLM response generation failed", error=str(e))
            
            # Fallback to simple template-based response
            fallback_response = self._generate_fallback_response(
                intent, slots, routed_endpoint
            )
            return fallback_response, ["fallback"]
    
    def _generate_fallback_response(
        self,
        intent: str,
        slots: Dict[str, Any],
        endpoint: str
    ) -> str:
        """Generate simple fallback response if LLM fails"""
        if intent == "kpi_query":
            return f"I'll retrieve the KPI data from {endpoint}."
        elif intent == "branch_status":
            return f"I'll check the branch status using {endpoint}."
        elif intent == "performance_analysis":
            return f"I'll analyze the performance data from {endpoint}."
        elif intent == "task_management":
            return f"I'll handle the task request via {endpoint}."
        elif intent == "event_query":
            return f"I'll retrieve event information from {endpoint}."
        elif intent == "promotion_query":
            return f"I'll get promotion details from {endpoint}."
        elif intent == "chitchat":
            return "I'm here to help with your retail analytics questions!"
        else:
            return "I'll process your request and retrieve the relevant information."


# Singleton instance
_llm_response_generator = None


def get_llm_response_generator() -> LLMResponseGenerator:
    """Get or create LLM response generator singleton"""
    global _llm_response_generator
    if _llm_response_generator is None:
        _llm_response_generator = LLMResponseGenerator()
    return _llm_response_generator
