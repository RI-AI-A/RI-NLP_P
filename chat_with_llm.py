"""Interactive chat with the LLM"""
import asyncio
import sys

# Add parent directory to path
sys.path.insert(0, '/home/ahmad-alshomaree/Desktop/Retail Intligence Chatbot/retail-intel-nlp-backend')

from nlp_service.llm_service import get_llm_service
from nlp_service.config import nlp_config


async def chat():
    """Interactive chat with LLM"""
    
    print("=" * 60)
    print("Interactive LLM Chat")
    print("=" * 60)
    print(f"\nModel: {nlp_config.llm_model}")
    print(f"Provider: {nlp_config.llm_provider}")
    print(f"Base URL: {nlp_config.llm_base_url}")
    print("\nType 'exit' or 'quit' to end the conversation")
    print("Type 'clear' to start a new conversation")
    print("=" * 60)
    print()
    
    # Initialize LLM service
    llm_service = get_llm_service()
    
    # Conversation history
    conversation_history = []
    
    system_prompt = """You are a helpful assistant for a retail intelligence system. 
You help users understand their retail analytics data, KPIs, and business metrics.
Be concise, professional, and helpful."""
    
    while True:
        try:
            # Get user input
            user_input = input("\n🧑 You: ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            # Check for clear command
            if user_input.lower() == 'clear':
                conversation_history = []
                print("\n🔄 Conversation cleared!")
                continue
            
            # Add to history
            conversation_history.append(f"User: {user_input}")
            
            # Build context from history
            context = "\n".join(conversation_history[-6:])  # Last 3 exchanges
            
            # Generate response
            print("\n🤖 Assistant: ", end="", flush=True)
            
            response = await llm_service.generate(
                prompt=f"{context}\nAssistant:",
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=300
            )
            
            assistant_response = response.content.strip()
            print(assistant_response)
            
            # Add to history
            conversation_history.append(f"Assistant: {assistant_response}")
            
            # Show stats
            print(f"\n📊 [Tokens: {response.tokens_used}, Latency: {response.latency_ms/1000:.1f}s, Cached: {response.cached}]")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n🚀 Starting LLM chat...")
    print("Make sure Ollama is running: ollama serve\n")
    
    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
