"""Query Router - Maps intents and slots to Core Backend API endpoints"""
from typing import Dict, Any
from urllib.parse import urlencode
import structlog

logger = structlog.get_logger()


class QueryRouter:
    """Route queries to appropriate Core Backend endpoints based on intent and slots"""

    def __init__(self):
        self.route_templates = {
            "kpi_query": self._route_kpi_query,

            # Branch status -> situations (what is happening now)
            "branch_status": self._route_situations,

            # Performance analysis -> recommendations (why + what to do)
            "performance_analysis": self._route_recommendations,

            "task_management": self._route_task_management,
            "event_query": self._route_event_query,
            "promotion_query": self._route_promotion_query,
            "chitchat": self._route_chitchat,
            "unknown": self._route_unknown,
        }

    async def route(self, intent: str, slots: Dict[str, Any]) -> str:
        try:
            router_func = self.route_templates.get(intent, self._route_unknown)
            endpoint = router_func(slots)

            logger.info("Query routed", intent=intent, slots=slots, endpoint=endpoint)
            return endpoint

        except Exception as e:
            logger.error("Routing failed", error=str(e), intent=intent)
            return "UNKNOWN"

    def _route_kpi_query(self, slots: Dict[str, Any]) -> str:
        branch_id = slots.get("branch_id", "unknown")
        kpi_type = slots.get("kpi_type", "general")
        params = {"branch_id": branch_id, "kpi_type": kpi_type}
        return f"/api/v1/kpis?{urlencode(params)}"

    def _route_situations(self, slots: Dict[str, Any]) -> str:
        branch_id = slots.get("branch_id", "unknown")
        params = {"branch_id": branch_id}

        # Optional filters if you want to support them later
        if slots.get("time_range"):
            params["time_range"] = slots["time_range"]
        if slots.get("situation_type"):
            params["situation_type"] = slots["situation_type"]

        return f"/api/v1/situations?{urlencode(params)}"

    def _route_recommendations(self, slots: Dict[str, Any]) -> str:
        branch_id = slots.get("branch_id", "unknown")
        params = {"branch_id": branch_id}
        return f"/api/v1/recommendations?{urlencode(params)}"

    def _route_task_management(self, slots: Dict[str, Any]) -> str:
        # Placeholder until your core backend supports tasks
        employee_name = slots.get("employee_name")
        if employee_name:
            return f"/tasks?{urlencode({'assigned_to': employee_name})}"
        return "/tasks"

    def _route_event_query(self, slots: Dict[str, Any]) -> str:
        params = {}
        if slots.get("event_type"):
            params["type"] = slots["event_type"]
        if slots.get("time_range"):
            params["date"] = slots["time_range"]

        if params:
            return f"/api/v1/events?{urlencode(params)}"
        return "/api/v1/events"

    def _route_promotion_query(self, slots: Dict[str, Any]) -> str:
        # Placeholder until promotions exist in core backend
        params = {}
        if slots.get("product_name"):
            params["product"] = slots["product_name"]
        if slots.get("time_range"):
            params["date"] = slots["time_range"]

        if params:
            return f"/promotions?{urlencode(params)}"
        return "/promotions"

    def _route_chitchat(self, slots: Dict[str, Any]) -> str:
        return "/chitchat"

    def _route_unknown(self, slots: Dict[str, Any]) -> str:
        return "UNKNOWN"

    def get_http_method(self, intent: str, slots: Dict[str, Any]) -> str:
        # Everything we do now is GET
        return "GET"


_query_router = None


def get_query_router() -> QueryRouter:
    global _query_router
    if _query_router is None:
        _query_router = QueryRouter()
    return _query_router
