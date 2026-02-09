"""NLP Router - Main NLP query endpoint"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.nlp_request import NLPRequest
from schemas.nlp_response import NLPResponse, NLPErrorResponse
from api_service.deps import get_database, get_orchestration
from api_service.services.orchestration_service import OrchestrationService
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/nlp", tags=["NLP"])


@router.post("/query", response_model=NLPResponse)
async def process_nlp_query(
    request: NLPRequest,
    db: AsyncSession = Depends(get_database),
    orchestration: OrchestrationService = Depends(get_orchestration)
):
    """
    Process a natural language query
    
    This endpoint:
    1. Classifies the intent
    2. Extracts slots/entities
    3. Routes to appropriate API endpoint
    4. Generates an explainable response
    5. Applies guardrails
    6. Logs the query
    
    Returns structured response with intent, slots, routing info, and generated text.
    """
    try:
        result = await orchestration.process_query(
            query=request.query,
            conversation_id=request.conversation_id,
            user_role=request.user_role,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Query processing failed")
            )
        
        return result["data"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in NLP query endpoint", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your query"
        )
