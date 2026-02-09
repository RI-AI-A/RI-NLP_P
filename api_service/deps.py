"""FastAPI Dependencies"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db
from api_service.services.orchestration_service import get_orchestration_service
from api_service.services.retrieval_service import get_retrieval_service


async def get_database() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency"""
    async for session in get_db():
        yield session


def get_orchestration() -> get_orchestration_service:
    """Get orchestration service dependency"""
    return get_orchestration_service()


def get_retrieval() -> get_retrieval_service:
    """Get retrieval service dependency"""
    return get_retrieval_service()
