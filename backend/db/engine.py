"""
SQLAlchemy async engine.

Priority:
  1. DATABASE_URL env var (PostgreSQL)
  2. SQLite fallback for local dev without Docker
"""

import logging
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

_DATABASE_URL = os.getenv("DATABASE_URL", "")

# Convert sync postgres:// → async postgresql+asyncpg://
if _DATABASE_URL.startswith("postgresql://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _DATABASE_URL.startswith("postgres://"):
    _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

# Fallback: SQLite for local dev
if not _DATABASE_URL:
    _DATA_DIR = os.getenv("DATA_DIR", "../dados")
    _DATABASE_URL = f"sqlite+aiosqlite:///{_DATA_DIR}/oraculo.db"
    logger.warning(
        "DATABASE_URL not set — using SQLite fallback at %s. "
        "Set DATABASE_URL=postgresql://... for production.",
        _DATABASE_URL,
    )

engine = create_async_engine(
    _DATABASE_URL,
    echo=os.getenv("DB_ECHO", "false").lower() == "true",
    # NullPool avoids issues with async SQLite + multiple workers
    poolclass=NullPool if "sqlite" in _DATABASE_URL else None,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields an AsyncSession per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
