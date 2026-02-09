"""Feedback Router - User feedback collection"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.feedback import FeedbackCreate, FeedbackResponse
from db.models import NLPFeedback, NLPQueryLog
from api_service.deps import get_database
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/nlp", tags=["Feedback"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: AsyncSession = Depends(get_database)
):
    """
    Submit user feedback for a query
    
    Allows users to rate NLP responses on a scale of 1-5 and provide optional comments.
    This feedback is used to improve the model and track user satisfaction.
    
    The query_id must reference a valid query from the nlp_queries_log table.
    """
    try:
        # Verify query exists
        query_stmt = select(NLPQueryLog).where(NLPQueryLog.id == feedback.query_id)
        result = await db.execute(query_stmt)
        query_log = result.scalar_one_or_none()
        
        if not query_log:
            raise HTTPException(
                status_code=404,
                detail=f"Query with ID {feedback.query_id} not found"
            )
        
        # Create feedback
        db_feedback = NLPFeedback(
            query_id=feedback.query_id,
            rating=feedback.rating,
            comment=feedback.comment
        )
        
        db.add(db_feedback)
        await db.commit()
        await db.refresh(db_feedback)
        
        logger.info("Feedback submitted", 
                   feedback_id=str(db_feedback.id),
                   query_id=str(feedback.query_id),
                   rating=feedback.rating)
        
        return db_feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to submit feedback", error=str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )
