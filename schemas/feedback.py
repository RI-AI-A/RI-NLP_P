"""Feedback Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class FeedbackCreate(BaseModel):
    """Schema for creating feedback"""
    query_id: UUID = Field(..., description="ID of the query being rated")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional comment")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query_id": "123e4567-e89b-12d3-a456-426614174000",
                    "rating": 5,
                    "comment": "Very helpful response"
                }
            ]
        }
    }


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: UUID
    query_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }
