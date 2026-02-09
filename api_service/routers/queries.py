"""Queries Router - Query log management"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from schemas.logs import QueryLogResponse, QueryLogFilter
from db.models import NLPQueryLog
from api_service.deps import get_database
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/nlp", tags=["Query Logs"])


@router.get("/logs", response_model=List[QueryLogResponse])
async def get_query_logs(
    conversation_id: Optional[UUID] = Query(None, description="Filter by conversation ID"),
    user_role: Optional[str] = Query(None, description="Filter by user role"),
    intent: Optional[str] = Query(None, description="Filter by intent"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_database)
):
    """
    Retrieve query logs with optional filtering
    
    Supports filtering by:
    - conversation_id: Get all queries from a specific conversation
    - user_role: Filter by user role (manager, analyst, staff)
    - intent: Filter by predicted intent
    - start_date/end_date: Filter by date range
    
    Includes pagination via limit and offset.
    """
    try:
        # Build query
        query_stmt = select(NLPQueryLog)
        
        # Apply filters
        if conversation_id:
            query_stmt = query_stmt.where(NLPQueryLog.conversation_id == conversation_id)
        if user_role:
            query_stmt = query_stmt.where(NLPQueryLog.user_role == user_role)
        if intent:
            query_stmt = query_stmt.where(NLPQueryLog.intent == intent)
        if start_date:
            query_stmt = query_stmt.where(NLPQueryLog.created_at >= start_date)
        if end_date:
            query_stmt = query_stmt.where(NLPQueryLog.created_at <= end_date)
        
        # Order by created_at descending
        query_stmt = query_stmt.order_by(NLPQueryLog.created_at.desc())
        
        # Apply pagination
        query_stmt = query_stmt.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query_stmt)
        logs = result.scalars().all()
        
        logger.info("Query logs retrieved", count=len(logs))
        
        return logs
        
    except Exception as e:
        logger.error("Failed to retrieve query logs", error=str(e), exc_info=True)
        raise
