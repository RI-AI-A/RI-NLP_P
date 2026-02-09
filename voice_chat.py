"""Voice-enabled chat with LLM using speech recognition and TTS"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, '/home/ahmad-alshomaree/Desktop/Retail Intligence Chatbot/retail-intel-nlp-backend')

from nlp_service.llm_service import get_llm_service
from nlp_service.config import nlp_config

# Voice libraries
import speech_recognition as sr
import edge_tts
from pydub import AudioSegment
from pydub.playback import play
import tempfile


class VoiceChat:
    """Voice-enabled chat with LLM"""
    
    def __init__(self):
        self.llm_service = None
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.voice = "en-US-AndrewNeural"  # Male voice
        # self.voice = "en-US-AriaNeural"  # Female voice alternative
        self.temp_dir = tempfile.mkdtemp()
        
    async def initialize(self):
        """Initialize LLM service"""
        print("🔧 Initializing LLM service...")
        self.llm_service = get_llm_service()
        print("✓ LLM service ready")
        
        # Adjust for ambient noise
        print("🎤 Calibrating microphone for ambient noise...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✓ Microphone calibrated")
    
    def listen(self) -> str:
        """Listen to user's voice input"""
        print("\n🎤 Listening... (speak now)")
        
        with self.microphone as source:
            try:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                print("🔄 Processing speech...")
                
                # Recognize speech using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                
                return text
                
            except sr.WaitTimeoutError:
                print("⏱️  No speech detected (timeout)")
                return None
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
                return None
    
    async def speak(self, text: str):
        """Convert text to speech and play it"""
        try:
            # Generate speech file
            output_file = os.path.join(self.temp_dir, "response.mp3")
            
            # Use edge-tts to generate speech
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_file)
            
            # Play the audio
            print("🔊 Playing response...")
            audio = AudioSegment.from_mp3(output_file)
            play(audio)
            
            # Clean up
            os.remove(output_file)
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            print(f"📝 Text response: {text}")
    
    async def chat(self):
        """Main voice chat loop"""
        print("=" * 60)
        print("🎙️  Voice Chat with LLM")
        print("=" * 60)
        print(f"\nModel: {nlp_config.llm_model}")
        print(f"Provider: {nlp_config.llm_provider}")
        print(f"Voice: {self.voice}")
        print("\n📢 Commands:")
        print("  - Say 'exit' or 'quit' to end")
        print("  - Say 'clear' to start new conversation")
        print("  - Press Ctrl+C to interrupt")
        print("=" * 60)
        
        await self.initialize()
        
        # Conversation history
        conversation_history = []
        
        system_prompt = """You are a helpful voice assistant for a retail intelligence system. 
You help users understand their retail analytics data, KPIs, and business metrics.
Keep responses concise and natural for voice conversation (2-3 sentences max unless asked for details).
Be professional and helpful."""
        
        # Welcome message
        welcome = "Hello! I'm your retail intelligence assistant. How can I help you today?"
        print(f"\n🤖 Assistant: {welcome}")
        await self.speak(welcome)
        
        while True:
            try:
                # Listen to user
                user_input = self.listen()
                
                if user_input is None:
                    continue
                
                print(f"🧑 You said: {user_input}")
                
                # Check for exit commands
                if any(word in user_input.lower() for word in ['exit', 'quit', 'goodbye', 'bye']):
                    farewell = "Goodbye! Have a great day!"
                    print(f"\n🤖 Assistant: {farewell}")
                    await self.speak(farewell)
                    break
                
                # Check for clear command
                if 'clear' in user_input.lower() or 'reset' in user_input.lower():
                    conversation_history = []
                    response = "Conversation cleared. What would you like to know?"
                    print(f"\n🤖 Assistant: {response}")
                    await self.speak(response)
                    continue
                
                # Add to history
                conversation_history.append(f"User: {user_input}")
                
                # Build context from history
                context = "\n".join(conversation_history[-6:])  # Last 3 exchanges
                
                # Generate response
                print("🤔 Thinking...")
                
                response = await self.llm_service.generate(
                    prompt=f"{context}\nAssistant:",
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=150  # Shorter for voice
                )
                
                assistant_response = response.content.strip()
                
                # Clean up response (remove markdown, etc.)
                assistant_response = assistant_response.replace('*', '').replace('#', '')
                
                print(f"\n🤖 Assistant: {assistant_response}")
                
                # Add to history
                conversation_history.append(f"Assistant: {assistant_response}")
                
                # Speak the response
                await self.speak(assistant_response)
                
                # Show stats
                print(f"📊 [Tokens: {response.tokens_used}, Latency: {response.latency_ms/1000:.1f}s]")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


async def main():
    """Main entry point"""
    print("\n🚀 Starting Voice Chat...")
    print("📋 Requirements:")
    print("  - Microphone connected")
    print("  - Speakers/headphones for audio output")
    print("  - Internet connection (for speech recognition)")
    print("  - Ollama running (ollama serve)")
    print()
    
    voice_chat = VoiceChat()
    
    try:
        await voice_chat.chat()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
