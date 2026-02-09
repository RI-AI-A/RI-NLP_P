"""Retrieval Service Wrapper"""
from typing import List, Tuple
from nlp_service.retrieval import get_retrieval_system, Document
import structlog

logger = structlog.get_logger()


class RetrievalService:
    """Service wrapper for retrieval operations"""
    
    def __init__(self):
        self.retrieval_system = None
    
    async def initialize(self):
        """Initialize retrieval system"""
        if self.retrieval_system is None:
            self.retrieval_system = await get_retrieval_system()
            logger.info("Retrieval service initialized")
    
    async def search(self, query: str, top_k: int = 5) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of (Document, score) tuples
        """
        if self.retrieval_system is None:
            await self.initialize()
        
        return await self.retrieval_system.search(query, top_k)


# Singleton instance
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """Get or create retrieval service singleton"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
