"""
dependencies.py
---------------
FastAPI dependency injection functions.

Why this exists:
    FastAPI's Depends() system lets route handlers declare what they need
    (a database session, the current user, a Redis connection) without
    knowing how to create those things. This file defines the "how to create"
    part in one place.

    Benefits:
    - Routes stay thin and testable (swap real DB for mock in tests)
    - Resources are properly opened and closed per-request
    - The current user is always available without repeated auth code

What it connects to:
    - config.py: reads settings
    - db/session.py: provides async database sessions
    - api/middleware.py: middleware sets request.state.user_id which
      get_current_user() reads here

Usage in route handlers:
    from dependencies import get_db, get_current_user

    @router.get("/search")
    async def search(
        db: AsyncSession = Depends(get_db),
        user_id: str = Depends(get_current_user),
    ):
        ...
"""

import logging
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, get_settings
from db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yields a SQLAlchemy async database session for a single request.

    Why a generator: ensures the session is always closed after the request
    completes, even if an exception is raised. SQLAlchemy sessions hold
    a database connection — leaking them exhausts the connection pool.

    Usage:
        db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            # Roll back any partial writes if the request handler raised.
            # This prevents corrupt partial data from being saved.
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Redis connection
# ---------------------------------------------------------------------------

class _NullRedis:
    """
    No-op Redis substitute used when Redis is unavailable.
    All cache reads return None (cache miss), all writes are silently dropped.
    The app works correctly — just without caching (slower, no polling).
    """
    async def get(self, key): return None
    async def set(self, key, value, *a, **kw): pass
    async def setex(self, key, ttl, value): pass
    async def delete(self, *keys): pass
    async def ping(self): return True
    async def aclose(self): pass


async def get_redis(
    settings: Settings = Depends(get_settings),
):
    """
    Yields an async Redis connection, or a no-op NullRedis if unavailable.
    The app degrades gracefully — searches still work, just without caching.
    """
    client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=2,
    )
    try:
        await client.ping()
        try:
            yield client
        finally:
            await client.aclose()
    except Exception:
        logger.warning("Redis unavailable — running without cache")
        await client.aclose()
        yield _NullRedis()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Returns the authenticated user's ID for the current request.

    How it works:
        AuthMiddleware (api/middleware.py) runs before every request and sets
        request.state.user_id. This dependency simply reads that value.

        In development (DEV_AUTH_BYPASS=True), middleware sets a fixed dev
        user ID so no auth setup is needed.

        In production, middleware verifies the Clerk JWT in the Authorization
        header and sets the real user ID.

    Returns:
        str: the user's ID (Clerk user ID in production, DEV_USER_ID in dev)

    Raises:
        HTTPException 401: if middleware did not set a user_id (unauthenticated)

    Usage:
        user_id: str = Depends(get_current_user)
    """
    user_id: str | None = getattr(request.state, "user_id", None)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


# ---------------------------------------------------------------------------
# Settings shortcut
# ---------------------------------------------------------------------------

def get_app_settings() -> Settings:
    """
    Thin wrapper so routes can declare settings as a dependency.

    Why: keeps route signatures consistent — everything comes via Depends()
    rather than mixing direct imports with dependency injection.

    Usage:
        settings: Settings = Depends(get_app_settings)
    """
    return get_settings()
