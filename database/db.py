"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from config.config import settings
from database.models import Base

logger = logging.getLogger(__name__)


# Convert postgres:// to postgresql+asyncpg:// for async support
def get_async_database_url(url: str) -> str:
    """Convert PostgreSQL URL to async format"""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Create async engine
DATABASE_URL = get_async_database_url(settings.database_url)
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.log_level == "DEBUG",
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """
    Initialize database (create tables if they don't exist)
    Note: In production, use Alembic migrations instead
    """
    async with engine.begin() as conn:
        # For development: create all tables
        # await conn.run_sync(Base.metadata.create_all)

        # For production: use Alembic migrations
        logger.info("Database initialized. Use Alembic for migrations in production.")


async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session

    Usage:
        async with get_db() as db:
            # Use db session
            result = await db.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Get a new database session (for use with FastAPI dependency injection)"""
    async with AsyncSessionLocal() as session:
        yield session


# Export
__all__ = ["engine", "AsyncSessionLocal", "get_db", "init_db", "close_db", "get_db_session"]
