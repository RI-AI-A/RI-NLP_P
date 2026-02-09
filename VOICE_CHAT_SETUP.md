# Voice Chat Setup Guide

## Quick Start

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio ffmpeg
```

**macOS:**
```bash
brew install portaudio ffmpeg
```

**Fedora/RHEL:**
```bash
sudo dnf install portaudio-devel ffmpeg
```

### 2. Install Python Dependencies

```bash
cd /home/ahmad-alshomaree/Desktop/Retail\ Intligence\ Chatbot/retail-intel-nlp-backend
source venv/bin/activate
pip install SpeechRecognition PyAudio
```

### 3. Test Your Microphone

```bash
# Test if microphone is detected
python -c "import speech_recognition as sr; print('Microphones:', sr.Microphone.list_microphone_names())"
```

### 4. Run Voice Chat

```bash
python voice_chat.py
```

---

## How It Works

### Speech Recognition (Input)
- **Library**: Google Speech Recognition API
- **Process**: 
  1. Listens to your microphone
  2. Captures audio (10s timeout, 15s max phrase)
  3. Sends to Google for transcription
  4. Returns text to LLM

### Text-to-Speech (Output)
- **Library**: Edge TTS (Microsoft Edge's TTS engine)
- **Voice**: Andrew (Male, US English)
- **Process**:
  1. LLM generates text response
  2. Edge TTS converts to MP3
  3. Plays audio through speakers

---

## Voice Commands

| Command | Action |
|---------|--------|
| "exit" / "quit" / "goodbye" | End conversation |
| "clear" / "reset" | Start new conversation |
| Ctrl+C | Force quit |

---

## Usage Example

```
🎙️  Voice Chat with LLM
============================================================

Model: mistral:latest
Provider: ollama
Voice: en-US-AndrewNeural

📢 Commands:
  - Say 'exit' or 'quit' to end
  - Say 'clear' to start new conversation
  - Press Ctrl+C to interrupt
============================================================

🔧 Initializing LLM service...
✓ LLM service ready
🎤 Calibrating microphone for ambient noise...
✓ Microphone calibrated

🤖 Assistant: Hello! I'm your retail intelligence assistant. How can I help you today?
🔊 Playing response...

🎤 Listening... (speak now)
🔄 Processing speech...
🧑 You said: What is a conversion rate?

🤔 Thinking...

🤖 Assistant: Conversion rate is the percentage of visitors who make a purchase. It's calculated by dividing the number of transactions by total visitors and multiplying by 100. For example, if 50 out of 1000 visitors buy something, your conversion rate is 5%.

🔊 Playing response...
📊 [Tokens: 78, Latency: 12.3s]
```

---

## Features

✅ **Natural Voice Conversation**
- Speak naturally to the LLM
- Hear responses in natural voice
- Maintains conversation context

✅ **Automatic Speech Recognition**
- Uses Google's speech recognition
- Handles ambient noise
- 10-second timeout for silence

✅ **High-Quality TTS**
- Microsoft Edge TTS engine
- Natural-sounding voice
- No API key required

✅ **Smart Response Length**
- Responses limited to 150 tokens for voice
- Concise, voice-friendly answers
- Can ask for more details

---

## Troubleshooting

### Microphone Not Detected

```bash
# List available microphones
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"

# Test microphone
arecord -l  # Linux
```

### PyAudio Installation Failed

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev
pip install PyAudio
```

**macOS:**
```bash
brew install portaudio
pip install PyAudio
```

**Alternative (if PyAudio fails):**
```bash
# Use sounddevice instead
pip install sounddevice soundfile
```

### No Audio Output

```bash
# Test speakers
speaker-test -t wav -c 2  # Linux

# Check ffmpeg
ffmpeg -version

# Install if missing
sudo apt-get install ffmpeg  # Ubuntu
brew install ffmpeg          # macOS
```

### Speech Recognition Errors

- **"No speech detected"**: Speak louder or closer to mic
- **"Could not understand"**: Speak more clearly
- **"Request error"**: Check internet connection (Google API requires internet)

---

## Configuration Options

### Change Voice

Edit `voice_chat.py`:

```python
# Male voices
self.voice = "en-US-AndrewNeural"  # Default
self.voice = "en-US-GuyNeural"

# Female voices
self.voice = "en-US-AriaNeural"
self.voice = "en-US-JennyNeural"

# British English
self.voice = "en-GB-RyanNeural"    # Male
self.voice = "en-GB-SoniaNeural"   # Female
```

### Adjust Timeouts

```python
# In listen() method
audio = self.recognizer.listen(
    source, 
    timeout=10,        # Wait 10s for speech to start
    phrase_time_limit=15  # Max 15s per phrase
)
```

### Response Length

```python
# In chat() method
response = await self.llm_service.generate(
    prompt=f"{context}\nAssistant:",
    system_prompt=system_prompt,
    temperature=0.7,
    max_tokens=150  # Adjust for longer/shorter responses
)
```

---

## Advanced Usage

### Offline Speech Recognition

For offline use, replace Google Speech Recognition with Vosk:

```bash
pip install vosk
# Download model from https://alphacephei.com/vosk/models
```

### Custom Wake Word

Add wake word detection before listening:

```bash
pip install pvporcupine  # Picovoice wake word
```

---

## Requirements

- **Microphone**: Any USB or built-in microphone
- **Speakers**: For audio output
- **Internet**: Required for Google Speech Recognition
- **Ollama**: Running locally (`ollama serve`)

---

## Performance

- **Speech Recognition**: ~1-2 seconds
- **LLM Response**: 30-60 seconds (Mistral 7B on CPU)
- **TTS Generation**: ~2-3 seconds
- **Total Latency**: ~35-65 seconds per exchange

**Optimization Tips**:
- Use smaller LLM model (llama3.2:3b)
- Enable GPU for faster LLM inference
- Use local TTS for faster audio generation

---

## Next Steps

1. **Test the voice chat**: `python voice_chat.py`
2. **Adjust voice settings**: Change voice in the script
3. **Optimize for your use case**: Adjust timeouts and response length
4. **Integrate with your app**: Use as a module in your application

Enjoy your voice-powered retail intelligence assistant! 🎙️🤖
