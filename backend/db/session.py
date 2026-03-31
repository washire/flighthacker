"""
db/session.py
-------------
Database engine and session factory for async PostgreSQL access.

Why this exists:
    Creates the async SQLAlchemy engine and session factory that the rest of
    the app uses for all database operations. Also handles creating tables on
    startup (development) and closing connections on shutdown.

What it connects to:
    - config.py: reads DATABASE_URL
    - db/base.py: Base.metadata used to create tables
    - dependencies.py: AsyncSessionLocal used in get_db()
    - main.py: init_db() and close_db() called on startup/shutdown

Notes on async:
    asyncpg is the async PostgreSQL driver. All DB operations must be awaited.
    Never use synchronous SQLAlchemy operations in this codebase — they block
    the event loop and defeat the parallelism the search engine depends on.
"""

import logging

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import get_settings
from db.base import Base

logger = logging.getLogger(__name__)

# Module-level engine instance. Initialised in init_db(), closed in close_db().
# Using a module-level variable (rather than recreating per request) means
# the connection pool is shared across all requests — this is correct behaviour.
_engine: AsyncEngine | None = None

# Session factory. Call AsyncSessionLocal() to get a session for a request.
# Configured in init_db(). Used by get_db() in dependencies.py.
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Initialises the database engine and session factory.

    Called once at application startup (main.py on_startup event).

    In development: also creates all tables that don't exist yet.
    In production: tables are managed by Alembic migrations — we do NOT
    call create_all() in production to avoid accidental schema changes.

    Why pool_size=10: handles up to 10 concurrent database operations.
    The search engine fires many parallel queries — the pool ensures they
    don't queue behind each other waiting for a connection.
    """
    global _engine, AsyncSessionLocal

    settings = get_settings()

    _engine = create_async_engine(
        settings.DATABASE_URL,
        # Log all SQL in development for debugging. Disabled in production
        # to avoid flooding logs with query noise.
        echo=(settings.ENVIRONMENT == "development"),
        # Connection pool settings.
        # pool_size: number of persistent connections to keep open.
        pool_size=10,
        # max_overflow: additional connections allowed beyond pool_size
        # during traffic spikes. These are closed when no longer needed.
        max_overflow=20,
        # pool_timeout: how long to wait for a connection before raising.
        pool_timeout=30,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        # expire_on_commit=False: prevents SQLAlchemy from expiring loaded
        # objects after a commit. Without this, accessing a field on a returned
        # model after the route handler commits would trigger another DB query.
        expire_on_commit=False,
    )

    # In development, create tables automatically so the dev doesn't need
    # to run migrations just to start the server.
    if settings.ENVIRONMENT == "development":
        # Import all models here to ensure their tables are registered with
        # Base.metadata before create_all() is called. If you add a new model,
        # add its import here.
        import db.orm_models  # noqa: F401 — imported for side effects

        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Development: database tables created/verified")


async def close_db() -> None:
    """
    Closes the database engine and all pooled connections.

    Called on application shutdown (main.py on_shutdown event).
    Ensures connections are returned cleanly — prevents 'connection already
    closed' errors and resource leaks on Railway during redeployments.
    """
    global _engine
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database engine disposed")
        _engine = None
