from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Async engine for FastAPI
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async with async_session_factory() as session:
        yield session


def _to_sync_database_url(url: str) -> str:
    """
    Convert common async SQLAlchemy URLs to sync equivalents for optional sync usage.
    """
    replacements = {
        "sqlite+aiosqlite://": "sqlite://",
        "postgresql+asyncpg://": "postgresql+psycopg://",
        "mysql+aiomysql://": "mysql+pymysql://",
    }

    for async_prefix, sync_prefix in replacements.items():
        if url.startswith(async_prefix):
            return url.replace(async_prefix, sync_prefix, 1)

    return url


def get_sync_session() -> Generator[Session, None, None]:
    """
    Optional sync session generator for scripts or legacy code.
    Avoids building a sync engine eagerly at import time.
    """
    sync_engine = create_engine(
        _to_sync_database_url(settings.DATABASE_URL),
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=sync_engine,
        autoflush=False,
        autocommit=False,
    )

    with SessionLocal() as session:
        yield session


async def create_all_tables() -> None:
    """
    Create all tables registered on Base metadata.
    Intended for local/dev only.
    """
    import app.db.models  # Ensure models are imported before create_all

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)