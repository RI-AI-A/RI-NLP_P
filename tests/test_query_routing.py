"""Tests for Query Routing"""
import pytest
import asyncio
from nlp_service.query_router import QueryRouter


@pytest.fixture
def query_router():
    """Create query router instance"""
    return QueryRouter()


@pytest.mark.asyncio
async def test_kpi_query_routing(query_router):
    """Test KPI query routing"""
    intent = "kpi_query"
    slots = {
        "branch_id": "A",
        "time_range": "yesterday",
        "kpi_type": "traffic"
    }
    
    endpoint = await query_router.route(intent, slots)
    
    assert "/kpis/branch/A" in endpoint
    assert "date=yesterday" in endpoint
    assert "kpi_type=traffic" in endpoint


@pytest.mark.asyncio
async def test_branch_status_routing(query_router):
    """Test branch status routing"""
    intent = "branch_status"
    slots = {"branch_id": "B"}
    
    endpoint = await query_router.route(intent, slots)
    
    assert endpoint == "/branches/B"


@pytest.mark.asyncio
async def test_task_management_routing(query_router):
    """Test task management routing"""
    intent = "task_management"
    slots = {"employee_name": "John"}
    
    endpoint = await query_router.route(intent, slots)
    
    assert "/tasks" in endpoint
    assert "assigned_to=John" in endpoint


@pytest.mark.asyncio
async def test_task_management_routing_no_employee(query_router):
    """Test task management routing without employee"""
    intent = "task_management"
    slots = {}
    
    endpoint = await query_router.route(intent, slots)
    
    assert endpoint == "/tasks"


@pytest.mark.asyncio
async def test_event_query_routing(query_router):
    """Test event query routing"""
    intent = "event_query"
    slots = {
        "event_type": "incident",
        "time_range": "today"
    }
    
    endpoint = await query_router.route(intent, slots)
    
    assert "/events" in endpoint
    assert "type=incident" in endpoint
    assert "date=today" in endpoint


@pytest.mark.asyncio
async def test_promotion_query_routing(query_router):
    """Test promotion query routing"""
    intent = "promotion_query"
    slots = {"product_name": "shoes"}
    
    endpoint = await query_router.route(intent, slots)
    
    assert "/promotions" in endpoint
    assert "product=shoes" in endpoint


@pytest.mark.asyncio
async def test_chitchat_routing(query_router):
    """Test chitchat routing"""
    intent = "chitchat"
    slots = {}
    
    endpoint = await query_router.route(intent, slots)
    
    assert endpoint == "/chitchat"


@pytest.mark.asyncio
async def test_unknown_routing(query_router):
    """Test unknown intent routing"""
    intent = "unknown"
    slots = {}
    
    endpoint = await query_router.route(intent, slots)
    
    assert endpoint == "/unknown"


@pytest.mark.asyncio
async def test_missing_required_slots(query_router):
    """Test routing with missing required slots"""
    intent = "kpi_query"
    slots = {}  # Missing branch_id
    
    endpoint = await query_router.route(intent, slots)
    
    # Should still generate endpoint with "unknown" for missing slots
    assert "/kpis/branch/unknown" in endpoint


def test_http_method_determination(query_router):
    """Test HTTP method determination"""
    assert query_router.get_http_method("kpi_query", {}) == "GET"
    assert query_router.get_http_method("task_management", {}) == "GET"
    assert query_router.get_http_method("branch_status", {}) == "GET"
