"""Tests for Intent Classifier"""
import pytest
import asyncio
from nlp_service.intent_classifier import IntentClassifier


@pytest.fixture
def intent_classifier():
    """Create intent classifier instance"""
    return IntentClassifier()


@pytest.mark.asyncio
async def test_kpi_query_intent(intent_classifier):
    """Test KPI query intent classification"""
    query = "Show me sales for branch A last week"
    intent, confidence = await intent_classifier.predict(query)
    
    assert intent == "kpi_query"
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_branch_status_intent(intent_classifier):
    """Test branch status intent classification"""
    query = "How busy is branch B right now?"
    intent, confidence = await intent_classifier.predict(query)
    
    assert intent in ["branch_status", "kpi_query"]  # Could be either
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_task_management_intent(intent_classifier):
    """Test task management intent classification"""
    query = "What tasks are assigned to John?"
    intent, confidence = await intent_classifier.predict(query)
    
    assert intent == "task_management"
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_event_query_intent(intent_classifier):
    """Test event query intent classification"""
    query = "Were there any incidents yesterday?"
    intent, confidence = await intent_classifier.predict(query)
    
    assert intent == "event_query"
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_promotion_query_intent(intent_classifier):
    """Test promotion query intent classification"""
    query = "What promotions are running this month?"
    intent, confidence = await intent_classifier.predict(query)
    
    assert intent == "promotion_query"
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_chitchat_intent(intent_classifier):
    """Test chitchat intent classification"""
    query = "Hello, how are you?"
    intent, confidence = await intent_classifier.predict(query)
    
    assert intent == "chitchat"
    assert confidence > 0.5


@pytest.mark.asyncio
async def test_unknown_intent(intent_classifier):
    """Test unknown intent classification"""
    query = "What's the weather like today?"
    intent, confidence = await intent_classifier.predict(query)
    
    # Should be unknown or have low confidence
    assert intent == "unknown" or confidence < 0.6


@pytest.mark.asyncio
async def test_low_confidence_threshold(intent_classifier):
    """Test that low confidence queries are marked as unknown"""
    query = "asdfghjkl qwerty"  # Nonsense query
    intent, confidence = await intent_classifier.predict(query)
    
    # Should be unknown due to low confidence
    assert intent == "unknown" or confidence < 0.6


@pytest.mark.asyncio
async def test_intent_description():
    """Test intent description retrieval"""
    classifier = IntentClassifier()
    
    description = classifier.get_intent_description("kpi_query")
    assert "KPI" in description or "performance" in description.lower()
    
    description = classifier.get_intent_description("unknown")
    assert "unknown" in description.lower() or "not" in description.lower()
