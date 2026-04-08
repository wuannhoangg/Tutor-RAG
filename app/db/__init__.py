"""
Database package exports.
"""

from .base import Base, engine, async_session_factory, get_async_session, create_all_tables
from . import models

BaseModel = Base


async def init_db_tables() -> None:
    """Initialize database tables for local/dev usage."""
    await create_all_tables()


__all__ = [
    "Base",
    "BaseModel",
    "engine",
    "async_session_factory",
    "get_async_session",
    "create_all_tables",
    "init_db_tables",
    "models",
]