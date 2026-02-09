"""NLP Request Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Literal


class NLPRequest(BaseModel):
    """Request schema for NLP query processing"""
    query: str = Field(..., min_length=1, max_length=1000, description="User query text")
    conversation_id: UUID = Field(..., description="Unique conversation identifier")
    user_role: Literal["manager", "analyst", "staff"] = Field(..., description="User role")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "How busy was branch A yesterday?",
                    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                    "user_role": "manager"
                }
            ]
        }
    }
