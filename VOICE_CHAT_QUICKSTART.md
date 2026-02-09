# Voice Chat Feature - Quick Start

## ✅ Installation Complete!

All dependencies have been successfully installed:
- ✅ portaudio19-dev (audio I/O library)
- ✅ python3-dev (Python headers)
- ✅ ffmpeg (audio processing)
- ✅ SpeechRecognition (Google Speech API)
- ✅ PyAudio (microphone access)
- ✅ edge-tts (Microsoft TTS)

## 🎤 Detected Microphones

Your system has **12 audio devices** available:
- HDA Intel PCH: CX8200 Analog (default microphone)
- HDMI outputs
- System default audio
- PipeWire audio

## 🚀 Start Voice Chat

```bash
cd /home/ahmad-alshomaree/Desktop/Retail\ Intligence\ Chatbot/retail-intel-nlp-backend
source venv/bin/activate
python voice_chat.py
```

## 🎙️ How to Use

1. **Start the script** - It will initialize and calibrate your microphone
2. **Wait for the prompt** - You'll hear "Hello! I'm your retail intelligence assistant..."
3. **Speak naturally** - The system will listen and transcribe your speech
4. **Get voice response** - The LLM will respond and speak back to you

## 💬 Voice Commands

| Say this | What happens |
|----------|--------------|
| "What is a conversion rate?" | LLM explains conversion rate |
| "How do I check sales data?" | LLM provides guidance |
| "exit" / "quit" / "goodbye" | Ends conversation |
| "clear" / "reset" | Starts new conversation |

## 🔧 How It Works

```
You speak → Google Speech Recognition → Text → LLM (Mistral) → Response Text → Edge TTS → Voice Output
```

**Technologies:**
- **Input**: Google Speech Recognition API (requires internet)
- **Processing**: Ollama + Mistral LLM (local)
- **Output**: Microsoft Edge TTS (free, no API key needed)

## ⚡ Performance

- **Speech Recognition**: ~1-2 seconds
- **LLM Processing**: ~30-60 seconds (Mistral 7B on CPU)
- **TTS Generation**: ~2-3 seconds
- **Total per exchange**: ~35-65 seconds

## 🎯 Example Conversation

```
🤖 Assistant: Hello! I'm your retail intelligence assistant. How can I help you today?
🔊 [Voice plays]

🎤 Listening... (speak now)

🧑 You said: What is a conversion rate?

🤔 Thinking...

🤖 Assistant: Conversion rate is the percentage of visitors who make a purchase. 
It's calculated by dividing the number of transactions by total visitors and 
multiplying by 100. For example, if 50 out of 1000 visitors buy something, 
your conversion rate is 5%.

🔊 [Voice plays]
📊 [Tokens: 78, Latency: 12.3s]
```

## 📚 Full Documentation

See [`VOICE_CHAT_SETUP.md`](file:///home/ahmad-alshomaree/Desktop/Retail%20Intligence%20Chatbot/retail-intel-nlp-backend/VOICE_CHAT_SETUP.md) for:
- Detailed setup instructions
- Troubleshooting guide
- Configuration options
- Voice customization
- Advanced features

## 🎨 Customization

### Change Voice

Edit `voice_chat.py` line 23:

```python
# Male voices
self.voice = "en-US-AndrewNeural"  # Default
self.voice = "en-US-GuyNeural"

# Female voices  
self.voice = "en-US-AriaNeural"
self.voice = "en-US-JennyNeural"
```

### Adjust Response Length

Edit line 138:

```python
max_tokens=150  # Shorter for voice (change to 200-300 for longer responses)
```

## ✨ Features

✅ **Natural Conversation**
- Speak naturally, no commands needed
- Maintains conversation context
- Understands follow-up questions

✅ **Hands-Free**
- Completely voice-driven
- No typing required
- Perfect for accessibility

✅ **Intelligent**
- Powered by Mistral 7B LLM
- Context-aware responses
- Professional retail assistant

✅ **Privacy-Focused**
- LLM runs locally (Ollama)
- Only speech recognition uses cloud (Google)
- TTS is free and doesn't require API keys

## 🎉 Ready to Try!

Your voice chat is fully configured and ready to use. Just run:

```bash
python voice_chat.py
```

Enjoy your voice-powered retail intelligence assistant! 🎙️🤖
