"""
Database connection and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from loguru import logger

from config.config import settings
from database.base import Base

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
    Initialize database.
    CRITICAL FIX: Creates tables if they don't exist.
    This solves the 'migration on empty DB' crash.
    """
    try:
        async with engine.begin() as conn:
            # 1. Enable UUID extension (often needed for Postgres)
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

            # 2. Create all tables defined in models.py
            # This is safe: SQLAlchemy checks existence before creating
            logger.info("⚡ Checking/Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database schema verified/created.")

    except Exception as e:
        logger.critical(f"❌ Database initialization failed: {e}")
        raise e

async def close_db() -> None:
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
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
