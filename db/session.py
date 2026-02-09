"""Database session management"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Async database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://nlp_user:nlp_password@localhost:5432/nlp_db"
)

# Sync database URL (for Alembic migrations)
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://nlp_user:nlp_password@localhost:5432/nlp_db"
)

# Async engine
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Sync engine (for migrations)
sync_engine = create_engine(
    DATABASE_URL_SYNC,
    echo=False,
    pool_pre_ping=True
)

# Sync session factory
SessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
