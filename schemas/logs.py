"""Log Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class QueryLogResponse(BaseModel):
    """Schema for query log response"""
    id: UUID
    conversation_id: UUID
    user_role: str
    query_text: str
    intent: str
    confidence: float
    routed_endpoint: Optional[str]
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class QueryLogFilter(BaseModel):
    """Schema for filtering query logs"""
    conversation_id: Optional[UUID] = None
    user_role: Optional[str] = None
    intent: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
