"""NLP Response Schemas"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List


class NLPResponse(BaseModel):
    """Response schema for NLP query processing"""
    intent: str = Field(..., description="Predicted intent")
    slots: Dict[str, Any] = Field(default_factory=dict, description="Extracted slots")
    routed_endpoint: str = Field(..., description="API endpoint to route to")
    response_text: str = Field(..., description="Generated response text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    sources: List[str] = Field(default_factory=list, description="Information sources used")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "intent": "kpi_query",
                    "slots": {
                        "branch_id": "A",
                        "time_range": "yesterday",
                        "kpi_type": "traffic"
                    },
                    "routed_endpoint": "/kpis/branch/A?date=yesterday&kpi_type=traffic",
                    "response_text": "Branch A had 23% higher traffic than its weekly baseline yesterday.",
                    "confidence": 0.91,
                    "sources": ["kpi_docs", "branch_kpi_timeseries"]
                }
            ]
        }
    }


class NLPErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    detail: str = Field(default="", description="Detailed error information")
