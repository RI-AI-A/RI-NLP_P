"""Voice Service - Handles STT (Whisper) and TTS (edge-tts)"""
import os
import io
import asyncio
import base64
import whisper
import edge_tts
from pydub import AudioSegment
from nlp_service.config import nlp_config
import structlog

logger = structlog.get_logger()

class VoiceService:
    """Handles speech-to-text and text-to-speech conversion"""
    
    def __init__(self):
        self.whisper_model = None
        self.model_name = nlp_config.whisper_model_name
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Ensure audio directories exist"""
        os.makedirs(nlp_config.audio_output_dir, exist_ok=True)
    
    def _load_model(self):
        """Lazy load Whisper model"""
        if self.whisper_model is None:
            logger.info("Loading Whisper model...", model_name=self.model_name)
            self.whisper_model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded")
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text using Whisper
        
        Args:
            audio_bytes: Raw audio data
            
        Returns:
            Transcribed text
        """
        try:
            # Load model if needed
            self._load_model()
            
            # Save temporary file for whisper (it expects a path or ndarray)
            temp_path = os.path.join(nlp_config.audio_output_dir, f"temp_{os.getpid()}.wav")
            
            # Convert audio to wav using pydub to ensure compatibility
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
            audio.export(temp_path, format="wav")
            
            # Transcribe
            logger.info("Transcribing audio...")
            result = self.whisper_model.transcribe(temp_path)
            text = result.get("text", "").strip()
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            logger.info("Transcription complete", text_length=len(text))
            return text
            
        except Exception as e:
            logger.error("Transcription failed", error=str(e))
            raise
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to audio bytes using edge-tts
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio bytes (mp3)
        """
        try:
            logger.info("Synthesizing speech...", text_length=len(text))
            
            communicate = edge_tts.Communicate(text, nlp_config.tts_voice)
            
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            logger.info("Synthesis complete", audio_size=len(audio_data))
            return audio_data
            
        except Exception as e:
            logger.error("Speech synthesis failed", error=str(e))
            raise


# Singleton instance
_voice_service = None

def get_voice_service() -> VoiceService:
    """Get or create voice service singleton"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
