"""Query Router - Maps intents and slots to API endpoints"""
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import structlog

logger = structlog.get_logger()


class QueryRouter:
    """Route queries to appropriate API endpoints based on intent and slots"""
    
    def __init__(self):
        self.route_templates = {
            "kpi_query": self._route_kpi_query,
            "branch_status": self._route_branch_status,
            "task_management": self._route_task_management,
            "event_query": self._route_event_query,
            "promotion_query": self._route_promotion_query,
            "chitchat": self._route_chitchat,
            "performance_analysis": self._route_performance_analysis,
            "unknown": self._route_unknown
        }
    
    async def route(self, intent: str, slots: Dict[str, Any]) -> str:
        """
        Generate API endpoint based on intent and slots
        
        Args:
            intent: Predicted intent
            slots: Extracted slots
            
        Returns:
            API endpoint URL
        """
        try:
            router_func = self.route_templates.get(intent, self._route_unknown)
            endpoint = router_func(slots)
            
            logger.info("Query routed", 
                       intent=intent, 
                       slots=slots, 
                       endpoint=endpoint)
            
            return endpoint
            
        except Exception as e:
            logger.error("Routing failed", error=str(e), intent=intent)
            return "/error"
    
    def _route_kpi_query(self, slots: Dict[str, Any]) -> str:
        """Route KPI queries"""
        branch_id = slots.get("branch_id", "unknown")
        time_range = slots.get("time_range", "today")
        kpi_type = slots.get("kpi_type", "general")
        
        # Build query parameters
        params = {
            "date": time_range,
            "kpi_type": kpi_type
        }
        
        query_string = urlencode(params)
        return f"/kpis/branch/{branch_id}?{query_string}"
    
    def _route_branch_status(self, slots: Dict[str, Any]) -> str:
        """Route branch status queries"""
        branch_id = slots.get("branch_id", "unknown")
        return f"/recommendations/{branch_id}"
    
    def _route_task_management(self, slots: Dict[str, Any]) -> str:
        """Route task management queries"""
        # Determine if it's a creation or retrieval based on context
        # For now, default to GET (retrieval)
        employee_name = slots.get("employee_name")
        
        if employee_name:
            params = {"assigned_to": employee_name}
            query_string = urlencode(params)
            return f"/tasks?{query_string}"
        
        return "/tasks"
    
    def _route_event_query(self, slots: Dict[str, Any]) -> str:
        """Route event queries"""
        event_type = slots.get("event_type")
        time_range = slots.get("time_range")
        
        params = {}
        if event_type:
            params["type"] = event_type
        if time_range:
            params["date"] = time_range
        
        if params:
            query_string = urlencode(params)
            return f"/events?{query_string}"
        
        return "/events"
    
    def _route_promotion_query(self, slots: Dict[str, Any]) -> str:
        """Route promotion queries"""
        product_name = slots.get("product_name")
        time_range = slots.get("time_range")
        
        params = {}
        if product_name:
            params["product"] = product_name
        if time_range:
            params["date"] = time_range
        
        if params:
            query_string = urlencode(params)
            return f"/promotions?{query_string}"
        
        return "/promotions"
    
    def _route_chitchat(self, slots: Dict[str, Any]) -> str:
        """Route chitchat queries"""
        return "/chitchat"
    
    def _route_performance_analysis(self, slots: Dict[str, Any]) -> str:
        """Route performance analysis queries"""
        branch_id = slots.get("branch_id", "unknown")
        return f"/recommendations/{branch_id}"
    
    def _route_unknown(self, slots: Dict[str, Any]) -> str:
        """Route unknown queries"""
        return "/unknown"
    
    def get_http_method(self, intent: str, slots: Dict[str, Any]) -> str:
        """
        Determine HTTP method based on intent
        
        Args:
            intent: Predicted intent
            slots: Extracted slots
            
        Returns:
            HTTP method (GET, POST, PUT, DELETE)
        """
        # Most queries are GET
        # POST for task creation (would need additional context)
        method_map = {
            "kpi_query": "GET",
            "branch_status": "GET",
            "task_management": "GET",  # Could be POST based on context
            "event_query": "GET",
            "promotion_query": "GET",
            "chitchat": "GET",
            "performance_analysis": "GET",
            "unknown": "GET"
        }
        
        return method_map.get(intent, "GET")


# Singleton instance
_query_router = None


def get_query_router() -> QueryRouter:
    """Get or create query router singleton"""
    global _query_router
    if _query_router is None:
        _query_router = QueryRouter()
    return _query_router
