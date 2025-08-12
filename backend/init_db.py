import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings
from app.models import Service, ServiceCheck, ServiceLog, Alert
from app.core.database import Base

async def init_db():
    """Initialize database tables"""
    
    # Create async engine
    engine = create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        echo=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database tables created successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())