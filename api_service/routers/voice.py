"""Voice Router - Handles voice-based NLP queries"""
import base64
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.nlp_response import NLPResponse
from api_service.deps import get_database, get_orchestration
from api_service.services.orchestration_service import OrchestrationService
from nlp_service.voice_service import get_voice_service, VoiceService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/nlp/voice", tags=["Voice NLP"])

@router.post("/query")
async def process_voice_query(
    audio: UploadFile = File(...),
    conversation_id: UUID = Form(...),
    user_role: str = Form(...),
    db: AsyncSession = Depends(get_database),
    orchestration: OrchestrationService = Depends(get_orchestration),
    voice_service: VoiceService = Depends(get_voice_service)
):
    """
    Process a voice-based natural language query
    
    1. Transcribes audio to text (Whisper)
    2. Processes text query through NLP pipeline
    3. Synthesizes response back to audio (edge-tts)
    """
    try:
        # Read audio data
        audio_content = await audio.read()
        if not audio_content:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Step 1: Transcribe
        logger.info("Transcribing voice query...", filename=audio.filename)
        query_text = await voice_service.transcribe(audio_content)
        
        if not query_text:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        # Step 2: Process Query through normal pipeline
        result = await orchestration.process_query(
            query=query_text,
            conversation_id=conversation_id,
            user_role=user_role,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Query processing failed")
            )
        
        nlp_data = result["data"]
        response_text = nlp_data.get("response_text", "")
        
        # Step 3: Synthesize Response
        audio_response_bytes = await voice_service.synthesize(response_text)
        
        # Base64 encode the response audio for JSON transport
        audio_base64 = base64.b64encode(audio_response_bytes).decode("utf-8")
        
        return {
            "transcription": query_text,
            "nlp_data": nlp_data,
            "audio_response": audio_base64,
            "audio_format": "mp3"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in voice query endpoint", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your voice query"
        )
