"""Database connection and session management."""

from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Create async engine with optimized pool settings for concurrent requests
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Disable SQLAlchemy query logging
    pool_pre_ping=True,
    pool_size=20,          # Increased from 5 for better concurrency
    max_overflow=30,       # Increased from 10 to handle burst traffic
    pool_timeout=30,       # Timeout waiting for connection from pool
    pool_recycle=1800,     # Recycle connections every 30 minutes
)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


async def init_db() -> None:
    """Initialize database connection."""
    # Test connection
    async with engine.begin() as conn:
        # Just test connectivity - schema is created via SQL file
        await conn.execute(text("SELECT 1"))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
