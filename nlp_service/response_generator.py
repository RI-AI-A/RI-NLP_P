"""Response Generator with RAG-lite"""
from typing import List, Dict, Any, Tuple
from .retrieval import get_retrieval_system, Document
import structlog

logger = structlog.get_logger()


class ResponseGenerator:
    """Generate responses using retrieved context"""
    
    def __init__(self):
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
        Generate response with retrieved context
        
        Args:
            query: Original user query
            intent: Predicted intent
            slots: Extracted slots
            routed_endpoint: Routed API endpoint
            
        Returns:
            Tuple of (response_text, sources)
        """
        try:
            # Retrieve relevant context
            retrieval_system = await get_retrieval_system()
            contexts = await retrieval_system.search(query, top_k=3)
            
            # Generate response using template
            generator_func = self.response_templates.get(
                intent,
                self._generate_unknown_response
            )
            
            response_text = generator_func(query, slots, contexts, routed_endpoint)
            
            # Extract sources
            sources = list(set([ctx[0].metadata.get("source", "unknown") 
                              for ctx in contexts]))
            
            logger.info("Response generated",
                       intent=intent,
                       sources=sources,
                       context_count=len(contexts))
            
            return response_text, sources
            
        except Exception as e:
            logger.error("Response generation failed", error=str(e))
            return "I apologize, but I encountered an error processing your request.", []
    
    def _generate_kpi_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate KPI query response"""
        branch_id = slots.get("branch_id", "the specified branch")
        time_range = slots.get("time_range", "the requested period")
        kpi_type = slots.get("kpi_type", "general")
        
        # Find relevant KPI explanation
        kpi_context = ""
        for doc, score in contexts:
            if doc.metadata.get("type") == "kpi_explanation":
                if kpi_type in doc.text.lower() or doc.metadata.get("kpi") == kpi_type:
                    kpi_context = doc.text
                    break
        
        response = f"I'll retrieve the {kpi_type} KPI data for {branch_id} during {time_range}. "
        
        if kpi_context:
            response += f"\n\nContext: {kpi_context}"
        
        response += f"\n\nYou can access the detailed data at: {endpoint}"
        
        return response
    
    def _generate_branch_status_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate branch status response"""
        branch_id = slots.get("branch_id", "the specified branch")
        
        response = f"I'll check the current status of {branch_id}. "
        response += "This includes occupancy levels, staff on duty, and any operational alerts."
        response += f"\n\nAccess the full status at: {endpoint}"
        
        return response
    
    def _generate_task_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate task management response"""
        employee_name = slots.get("employee_name")
        
        if employee_name:
            response = f"I'll retrieve tasks assigned to {employee_name}. "
        else:
            response = "I'll retrieve the task list. "
        
        # Add context about task management
        for doc, score in contexts:
            if doc.metadata.get("source") == "task_docs":
                response += f"\n\n{doc.text}"
                break
        
        response += f"\n\nAccess tasks at: {endpoint}"
        
        return response
    
    def _generate_event_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate event query response"""
        event_type = slots.get("event_type", "all")
        time_range = slots.get("time_range", "recent")
        
        response = f"I'll retrieve {event_type} events from {time_range}. "
        response += f"\n\nAccess event details at: {endpoint}"
        
        return response
    
    def _generate_promotion_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate promotion query response"""
        product_name = slots.get("product_name")
        
        if product_name:
            response = f"I'll check for promotions related to {product_name}. "
        else:
            response = "I'll retrieve current promotions. "
        
        # Add business rules context
        for doc, score in contexts:
            if doc.metadata.get("source") == "business_rules" and "promotion" in doc.text.lower():
                response += f"\n\nNote: {doc.text}"
                break
        
        response += f"\n\nAccess promotions at: {endpoint}"
        
        return response
    
    def _generate_chitchat_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate chitchat response"""
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

    def _generate_performance_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate performance analysis response"""
        branch_id = slots.get("branch_id", "the branch")
        
        response = f"I've analyzed the performance of {branch_id}. "
        
        # Add context from retrieval
        if contexts:
            # Prioritize contexts about performance, issues, or recommendations
            relevant_context = ""
            for doc, score in contexts:
                text_lower = doc.text.lower()
                if any(term in text_lower for term in ["performance", "issue", "problem", "recommendation", "traffic", "underperforming"]):
                    relevant_context = doc.text
                    break
            
            if relevant_context:
                response += f"\n\nContext: {relevant_context}"
        
        response += f"\n\nYou can view the full diagnostic report and recommendations at: {endpoint}"
        
        return response
    
    def _generate_unknown_response(
        self,
        query: str,
        slots: Dict[str, Any],
        contexts: List[Tuple[Document, float]],
        endpoint: str
    ) -> str:
        """Generate response for unknown intent"""
        response = "I'm not sure I understand your request. "
        response += "I can help you with:\n"
        response += "• KPI queries (e.g., 'Show me sales for branch A')\n"
        response += "• Branch status (e.g., 'How busy is branch B?')\n"
        response += "• Task management (e.g., 'What tasks are assigned to John?')\n"
        response += "• Events (e.g., 'Any incidents today?')\n"
        response += "• Promotions (e.g., 'Current promotions?')\n"
        
        # Add most relevant context if available
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
