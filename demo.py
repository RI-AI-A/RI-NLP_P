"""Simple Demo Script - Test NLP Service Without Heavy Dependencies"""
import asyncio
import json
from uuid import uuid4

# Simple mock implementations for demo
class SimpleMockIntentClassifier:
    """Mock intent classifier for demo"""
    async def predict(self, query: str):
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["kpi", "sales", "revenue", "traffic", "busy"]):
            return "kpi_query", 0.89
        elif any(word in query_lower for word in ["branch", "store", "status"]):
            return "branch_status", 0.85
        elif any(word in query_lower for word in ["task", "assigned", "todo"]):
            return "task_management", 0.82
        elif any(word in query_lower for word in ["event", "incident", "accident"]):
            return "event_query", 0.87
        elif any(word in query_lower for word in ["promotion", "offer", "deal"]):
            return "promotion_query", 0.84
        elif any(word in query_lower for word in ["hello", "hi", "hey", "thanks"]):
            return "chitchat", 0.95
        else:
            return "unknown", 0.45

class SimpleMockSlotFiller:
    """Mock slot filler for demo"""
    async def extract_slots(self, query: str, intent: str):
        import re
        slots = {}
        
        # Extract branch ID
        branch_match = re.search(r'branch\s+([A-Z0-9]+)', query, re.IGNORECASE)
        if branch_match:
            slots["branch_id"] = branch_match.group(1).upper()
        
        # Extract time range
        if "yesterday" in query.lower():
            slots["time_range"] = "yesterday"
        elif "today" in query.lower():
            slots["time_range"] = "today"
        elif "last week" in query.lower():
            slots["time_range"] = "last_week"
        
        # Extract KPI type
        if "traffic" in query.lower() or "busy" in query.lower():
            slots["kpi_type"] = "traffic"
        elif "sales" in query.lower() or "revenue" in query.lower():
            slots["kpi_type"] = "sales"
        
        return slots

class SimpleMockRouter:
    """Mock query router for demo"""
    async def route(self, intent: str, slots: dict):
        if intent == "kpi_query":
            branch = slots.get("branch_id", "unknown")
            time_range = slots.get("time_range", "today")
            kpi_type = slots.get("kpi_type", "general")
            return f"/kpis/branch/{branch}?date={time_range}&kpi_type={kpi_type}"
        elif intent == "branch_status":
            branch = slots.get("branch_id", "unknown")
            return f"/branches/{branch}"
        elif intent == "task_management":
            return "/tasks"
        elif intent == "event_query":
            return "/events"
        elif intent == "promotion_query":
            return "/promotions"
        else:
            return "/unknown"

class SimpleMockResponseGenerator:
    """Mock response generator for demo"""
    async def generate(self, query: str, intent: str, slots: dict, endpoint: str):
        responses = {
            "kpi_query": f"I'll retrieve the KPI data for {slots.get('branch_id', 'the branch')}. Access at: {endpoint}",
            "branch_status": f"Checking status of {slots.get('branch_id', 'the branch')}. Access at: {endpoint}",
            "task_management": f"Retrieving tasks. Access at: {endpoint}",
            "event_query": f"Checking for events. Access at: {endpoint}",
            "promotion_query": f"Retrieving current promotions. Access at: {endpoint}",
            "chitchat": "Hello! I'm here to help with retail analytics queries.",
            "unknown": "I'm not sure I understand. I can help with KPIs, branch status, tasks, events, and promotions."
        }
        return responses.get(intent, "Unable to process query."), ["demo_docs"]

async def demo_nlp_pipeline(query: str):
    """Demonstrate the NLP pipeline"""
    print(f"\n{'='*80}")
    print(f"QUERY: {query}")
    print(f"{'='*80}\n")
    
    # Initialize components
    intent_classifier = SimpleMockIntentClassifier()
    slot_filler = SimpleMockSlotFiller()
    router = SimpleMockRouter()
    response_generator = SimpleMockResponseGenerator()
    
    # Step 1: Intent Classification
    intent, confidence = await intent_classifier.predict(query)
    print(f"✓ Intent Classification:")
    print(f"  Intent: {intent}")
    print(f"  Confidence: {confidence:.2f}\n")
    
    # Step 2: Slot Filling
    slots = await slot_filler.extract_slots(query, intent)
    print(f"✓ Slot Extraction:")
    print(f"  Slots: {json.dumps(slots, indent=4)}\n")
    
    # Step 3: Query Routing
    endpoint = await router.route(intent, slots)
    print(f"✓ Query Routing:")
    print(f"  Endpoint: {endpoint}\n")
    
    # Step 4: Response Generation
    response_text, sources = await response_generator.generate(query, intent, slots, endpoint)
    print(f"✓ Response Generation:")
    print(f"  Response: {response_text}")
    print(f"  Sources: {sources}\n")
    
    # Final result
    result = {
        "intent": intent,
        "slots": slots,
        "routed_endpoint": endpoint,
        "response_text": response_text,
        "confidence": confidence,
        "sources": sources
    }
    
    print(f"{'='*80}")
    print("FINAL RESULT:")
    print(f"{'='*80}")
    print(json.dumps(result, indent=2))
    print()
    
    return result

async def main():
    """Run demo with sample queries"""
    print("\n" + "="*80)
    print("NLP MICROSERVICE DEMO")
    print("="*80)
    
    sample_queries = [
        "How busy was branch A yesterday?",
        "What's the status of branch B?",
        "Show me tasks assigned to John",
        "Any incidents today?",
        "What promotions are running this month?",
        "Hello, how are you?",
    ]
    
    for query in sample_queries:
        await demo_nlp_pipeline(query)
        await asyncio.sleep(0.5)
    
    print("\n" + "="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print("\nThis demo shows the NLP pipeline structure.")
    print("The full implementation uses:")
    print("  - BERT/DistilBERT for intent classification")
    print("  - spaCy NER + regex for slot extraction")
    print("  - FAISS vector search for RAG-lite retrieval")
    print("  - Comprehensive guardrails (profanity, PII, hallucination)")
    print("  - FastAPI backend with PostgreSQL logging")
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
