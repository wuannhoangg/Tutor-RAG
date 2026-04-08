import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. Import settings và Base model của TutorRAG
from app.core.config import get_settings
from app.db.base import Base
import app.db.models  # Đảm bảo các models đã được load vào Base.metadata

config = context.config

# Setup logging từ file alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Gán target_metadata để Alembic so sánh DB và Code
target_metadata = Base.metadata

# Lấy cấu hình database URL từ settings của hệ thống
settings = get_settings()

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section, {})
    # 3. Ghi đè sqlalchemy.url bằng DATABASE_URL từ file .env
    configuration["sqlalchemy.url"] = settings.DATABASE_URL

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()