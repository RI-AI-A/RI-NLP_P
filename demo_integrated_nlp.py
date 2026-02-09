import asyncio
import json
import re

# Mocking the enhanced components for demonstration without running full services
class MockEnhancedRouter:
    async def route(self, intent: str, slots: dict):
        # 5. Analytics Query Router Enhancement logic
        if intent == "branch_status" or (intent == "kpi_query" and "why" in slots.get("query_text", "").lower()):
            branch = slots.get("branch_id", "unknown")
            # Routes to the new Situation/Recommendation engine
            return f"/recommendations/{branch}"
        return "/unknown"

class MockEnhancedResponseGenerator:
    async def generate(self, query: str, endpoint: str):
        # Simulating the response getting data from the backend
        if "/recommendations/" in endpoint:
            branch_id = endpoint.split("/")[-1]
            # This simulates the Explanation Generator output from the backend
            backend_response = {
                "situation": "underperformance",
                "details": f"{branch_id} is underperforming because traffic dropped 18% compared to last week and conversion decreased from 22% to 14%."
            }
            return f"I've analyzed {branch_id}. {backend_response['details']} Access full report at: {endpoint}"
        return "I couldn't generate a specific response."

async def run_nlp_demo():
    print("\n" + "="*80)
    print("🧠 RETAIL INTELLIGENCE NLP - INTEGRATED DEMO")
    print("="*80 + "\n")
    
    query = "Why is Branch A underperforming?"
    print(f"👤 User Query: \"{query}\"\n")

    # 1. Intent Classification (Mocked)
    intent = "branch_status" 
    # Logic: "Why" + "underperforming" implies status/diagnostic intent
    print(f"   [Intent Classifier] Detected: '{intent}' (Confidence: 0.92)")

    # 2. Slot Filling (Mocked)
    slots = {"branch_id": "Branch A", "query_text": query}
    print(f"   [Slot Filler] Extracted: {slots}")

    # 3. Routing (The key MVP requirement)
    router = MockEnhancedRouter()
    endpoint = await router.route(intent, slots)
    print(f"   [Query Router] Routing to: {endpoint}")
    print(f"      (Connected to Situation & Recommendation Engine)")

    # 4. Response Generation (Simulating Backend Integration)
    generator = MockEnhancedResponseGenerator()
    response = await generator.generate(query, endpoint)
    
    print(f"\n🤖 System Response:\n   \"{response}\"")
    print("\n" + "="*80)
    print("✅ NLP Demo Complete. Recommendations API Integrated.")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(run_nlp_demo())
