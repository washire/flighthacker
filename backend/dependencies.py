"""
dependencies.py
---------------
FastAPI dependency injection functions.
"""

import logging
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, get_settings
import db.session as _db_session  # import module, not value — so we see init_db() updates

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NullRedis — no-op fallback when Redis is unavailable
# ---------------------------------------------------------------------------

class _NullRedis:
    """Drop-in Redis replacement that silently discards all operations."""
    async def get(self, key): return None
    async def set(self, key, value, *a, **kw): pass
    async def setex(self, key, ttl, value): pass
    async def delete(self, *keys): pass
    async def ping(self): return True
    async def aclose(self): pass


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession | None, None]:
    """
    Yields a SQLAlchemy async database session, or None if DB is unreachable.
    Routes must handle None gracefully (search works without DB persistence).
    """
    session_factory = _db_session.AsyncSessionLocal
    if session_factory is None:
        logger.warning("db.not_initialised — yielding None")
        yield None
        return

    try:
        async with session_factory() as session:
            try:
                yield session
                try:
                    await session.commit()
                except Exception as exc:
                    logger.warning("db.commit_failed err=%s", exc)
                    try:
                        await session.rollback()
                    except Exception:
                        pass
            except Exception:
                try:
                    await session.rollback()
                except Exception:
                    pass
                raise
            finally:
                try:
                    await session.close()
                except Exception:
                    pass
    except Exception as exc:
        logger.warning("db.session_failed err=%s — yielding None", exc)
        yield None


# ---------------------------------------------------------------------------
# Redis connection
# ---------------------------------------------------------------------------

async def get_redis(
    settings: Settings = Depends(get_settings),
):
    """
    Yields an async Redis connection, or a NullRedis if Redis is unavailable.
    All cache reads/writes degrade gracefully — the app still works, just slower.
    """
    client = None
    use_null = False
    try:
        client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=2,
        )
        await client.ping()
    except Exception as exc:
        logger.warning("Redis unavailable (%s) — running without cache", exc)
        use_null = True
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                pass
        client = None

    if use_null:
        yield _NullRedis()
    else:
        try:
            yield client
        finally:
            if client is not None:
                try:
                    await client.aclose()
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

async def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    """
    Returns the authenticated user's ID for the current request.
    In dev (DEV_AUTH_BYPASS=True), returns a fixed dev user ID.
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
    return get_settings()
