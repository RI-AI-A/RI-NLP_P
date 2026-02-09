import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://retail_user:retail_pass@localhost:5432/retail_intel"

async def inspect():
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        # List tables
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = [row[0] for row in result.fetchall()]
        print("Tables:", tables)
        
        # Check alembic_version
        if 'alembic_version' in tables:
            result = await conn.execute(text("SELECT * FROM alembic_version"))
            print("alembic_version:", result.fetchall())
            
        # Check alembic_version_nlp
        if 'alembic_version_nlp' in tables:
            result = await conn.execute(text("SELECT * FROM alembic_version_nlp"))
            print("alembic_version_nlp:", result.fetchall())

if __name__ == "__main__":
    asyncio.run(inspect())
