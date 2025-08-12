 from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from .config import settings

# Create sync engine for migrations
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG
)
AsyncSessionLocal = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()