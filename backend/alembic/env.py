"""
Alembic environment configuration.

This file is the bridge between Alembic and your application.
It tells Alembic:
  1. WHERE to connect (database URL from our .env)
  2. WHAT to track (our SQLAlchemy Base.metadata)

When you run `alembic revision --autogenerate`, Alembic:
  1. Connects to the database
  2. Reads the current table structure
  3. Compares it to your Python models (via target_metadata)
  4. Generates a migration script for the differences
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Import our app's models and config ────────────────────────
# We need sys.path manipulation because Alembic runs from the
# backend/ directory but our modules are in backend/app/.
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.models.database import Base  # This import loads ALL models

# ── Alembic Config ────────────────────────────────────────────
config = context.config

# Override the database URL with our app's setting
# (so we don't have to maintain it in two places)
config.set_main_option("sqlalchemy.url", settings.sync_database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# THIS is what makes --autogenerate work. Alembic compares the
# database against this metadata to detect changes.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This generates SQL without actually connecting to the database.
    Useful for generating migration scripts that a DBA will review
    and apply manually in production.
    """
    url = config.get_main_option("sqlalchemy.url")
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
    """
    Run migrations with an async engine.
    
    Even though our app uses async, Alembic itself is sync.
    This wrapper creates an async engine, runs the sync migration
    logic inside it, then cleans up.
    """
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connected to the database)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
