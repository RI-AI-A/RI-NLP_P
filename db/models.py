"""Database models"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class NLPQueryLog(Base):
    """Log of NLP queries"""
    __tablename__ = "nlp_queries_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_role = Column(String(50), nullable=False)  # manager, analyst, staff
    query_text = Column(Text, nullable=False)
    intent = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    routed_endpoint = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship to feedback
    feedback = relationship("NLPFeedback", back_populates="query", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<NLPQueryLog(id={self.id}, intent={self.intent}, confidence={self.confidence})>"


class NLPFeedback(Base):
    """User feedback on NLP responses"""
    __tablename__ = "nlp_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("nlp_queries_log.id"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to query
    query = relationship("NLPQueryLog", back_populates="feedback")
    
    def __repr__(self):
        return f"<NLPFeedback(id={self.id}, query_id={self.query_id}, rating={self.rating})>"
