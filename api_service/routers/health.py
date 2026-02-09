"""Health Router - Service health checks"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel
from typing import Dict, Any
from api_service.deps import get_database
from nlp_service.intent_classifier import get_intent_classifier
from nlp_service.retrieval import get_retrieval_system
import structlog

logger = structlog.get_logger()

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    details: Dict[str, Any]


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_database)):
    """
    Comprehensive health check
    
    Checks:
    - API service status
    - Database connectivity
    - NLP models loaded
    - FAISS index status
    
    Returns detailed health information for monitoring.
    """
    health_details = {
        "api": "healthy",
        "database": "unknown",
        "intent_classifier": "unknown",
        "retrieval_system": "unknown"
    }
    
    overall_status = "healthy"
    
    try:
        # Check database
        try:
            await db.execute(text("SELECT 1"))
            health_details["database"] = "healthy"
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            health_details["database"] = f"unhealthy: {str(e)}"
            overall_status = "degraded"
        
        # Check intent classifier
        try:
            classifier = get_intent_classifier()
            if classifier.zero_shot_classifier is not None:
                health_details["intent_classifier"] = "healthy"
            else:
                health_details["intent_classifier"] = "degraded: no model loaded"
                overall_status = "degraded"
        except Exception as e:
            logger.error("Intent classifier health check failed", error=str(e))
            health_details["intent_classifier"] = f"unhealthy: {str(e)}"
            overall_status = "degraded"
        
        # Check retrieval system
        try:
            retrieval = await get_retrieval_system()
            if retrieval.index is not None and retrieval.index.ntotal > 0:
                health_details["retrieval_system"] = f"healthy ({retrieval.index.ntotal} documents)"
            else:
                health_details["retrieval_system"] = "degraded: empty index"
                overall_status = "degraded"
        except Exception as e:
            logger.error("Retrieval system health check failed", error=str(e))
            health_details["retrieval_system"] = f"unhealthy: {str(e)}"
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            details=health_details
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e), exc_info=True)
        return HealthResponse(
            status="unhealthy",
            details={
                "error": str(e),
                **health_details
            }
        )
