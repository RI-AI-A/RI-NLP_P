"""Demo Voice Script - Test Voice Integration"""
import asyncio
import base64
import httpx
import os
import edge_tts
from uuid import uuid4

# Configuration
API_URL = "http://localhost:8000/nlp/voice/query"
SAMPLE_AUDIO_PATH = "sample_query.mp3"
RESPONSE_AUDIO_PATH = "response_audio.mp3"

async def create_sample_audio(text: str, path: str):
    """Create a sample audio file for testing"""
    print(f"Creating sample audio: '{text}' -> {path}")
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural")
    await communicate.save(path)

async def test_voice_query():
    """Test the voice query endpoint"""
    print("\nStarting Voice Query Test")
    print("-" * 30)
    
    # Check if API is running
    async with httpx.AsyncClient() as client:
        try:
            health = await client.get("http://localhost:8000/health")
            if health.status_code != 200:
                print("❌ API health check failed. Is the server running?")
                return
        except Exception as e:
            print(f"❌ Could not connect to API: {e}")
            print("Please run the server first: uvicorn api_service.main:app --reload")
            return

    # 1. Create sample audio
    sample_text = "How busy was branch A yesterday?"
    await create_sample_audio(sample_text, SAMPLE_AUDIO_PATH)
    
    # 2. Send to API
    print(f"Sending audio to API: {API_URL}")
    
    files = {
        "audio": (SAMPLE_AUDIO_PATH, open(SAMPLE_AUDIO_PATH, "rb"), "audio/mpeg")
    }
    data = {
        "conversation_id": str(uuid4()),
        "user_role": "manager"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(API_URL, data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ SUCCESS!")
                print(f"Transcription: {result['transcription']}")
                print(f"Intent: {result['nlp_data']['intent']}")
                print(f"Response Text: {result['nlp_data']['response_text']}")
                
                # 3. Save response audio
                audio_base64 = result['audio_response']
                audio_bytes = base64.b64decode(audio_base64)
                
                with open(RESPONSE_AUDIO_PATH, "wb") as f:
                    f.write(audio_bytes)
                print(f"Response audio saved to: {RESPONSE_AUDIO_PATH}")
                
            else:
                print(f"\n❌ FAILED: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error during request: {e}")
        finally:
            # Cleanup sample file
            if os.path.exists(SAMPLE_AUDIO_PATH):
                os.remove(SAMPLE_AUDIO_PATH)

if __name__ == "__main__":
    asyncio.run(test_voice_query())
