"""Test script for LLM integration"""
import asyncio
import sys
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, '/home/ahmad-alshomaree/Desktop/Retail Intligence Chatbot/retail-intel-nlp-backend')

from nlp_service.llm_intent_classifier import get_llm_intent_classifier
from nlp_service.llm_slot_filler import get_llm_slot_filler
from nlp_service.llm_response_generator import get_llm_response_generator
from nlp_service.config import nlp_config


async def test_llm_components():
    """Test all LLM components"""
    
    print("=" * 60)
    print("LLM Integration Test")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Provider: {nlp_config.llm_provider}")
    print(f"  Model: {nlp_config.llm_model}")
    print(f"  Base URL: {nlp_config.llm_base_url}")
    print(f"  Use LLM: {nlp_config.use_llm}")
    print()
    
    # Test queries
    test_queries = [
        "What were the sales yesterday?",
        "How busy was branch A last week?",
        "Show me the conversion rate for all branches this month",
        "Create a task for John to check inventory",
        "Hello, how are you?"
    ]
    
    # Initialize components
    print("Initializing LLM components...")
    intent_classifier = get_llm_intent_classifier()
    slot_filler = get_llm_slot_filler()
    response_generator = get_llm_response_generator()
    print("✓ Components initialized\n")
    
    # Test each query
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}/{len(test_queries)}: {query}")
        print('=' * 60)
        
        try:
            # Test intent classification
            print("\n1. Intent Classification:")
            intent, confidence = await intent_classifier.predict(query)
            print(f"   Intent: {intent}")
            print(f"   Confidence: {confidence:.2f}")
            
            # Test slot filling
            print("\n2. Slot Extraction:")
            slots = await slot_filler.extract_slots(query, intent)
            if slots:
                for key, value in slots.items():
                    print(f"   {key}: {value}")
            else:
                print("   No slots extracted")
            
            # Test response generation
            print("\n3. Response Generation:")
            routed_endpoint = f"/api/{intent}"  # Mock endpoint
            response_text, sources = await response_generator.generate(
                query, intent, slots, routed_endpoint
            )
            print(f"   Response: {response_text}")
            print(f"   Sources: {sources}")
            
            print("\n✓ Test passed")
            
        except Exception as e:
            print(f"\n✗ Test failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nMake sure Ollama is running: ollama serve")
    print("And the model is pulled: ollama pull llama3.2:3b\n")
    
    try:
        asyncio.run(test_llm_components())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
