from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from typing import AsyncGenerator
import logging
from config.config import settings

logger = logging.getLogger(__name__)

# 1. Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# 2. Конвертация URL для asyncpg
def get_async_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

DATABASE_URL = get_async_database_url(settings.database_url)

# 3. Движок БД
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# 4. Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# 5. Инициализация (С ЯДЕРНЫМ СБРОСОМ)
async def init_db() -> None:
    """
    Инициализация базы данных.
    ВНИМАНИЕ: ВКЛЮЧЕН РЕЖИМ ПОЛНОГО СБРОСА (DROP_ALL)
    Это необходимо для исправления конфликта UUID/Integer.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))

            logger.info("⚡ Checking/Creating tables (Police Mode)...")
            await conn.run_sync(Base.metadata.create_all)

            logger.info("✅ Database schema created FRESH.")
    except Exception as e:
        logger.critical(f"❌ Database initialization failed: {e}")
        raise e

async def close_db() -> None:
    await engine.dispose()

# 6. Зависимость для сессий
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
