"""
main.py
-------
FlightHacker backend entry point.

Why this exists:
    Creates and configures the FastAPI application instance. This is the file
    that uvicorn runs. It wires together middleware, routers, startup/shutdown
    events, and the health check endpoint.

    Kept deliberately thin — no business logic lives here. This file only
    assembles components defined elsewhere.

What it connects to:
    - config.py: reads settings for CORS origins and environment
    - api/middleware.py: registers auth and logging middleware
    - api/v1/router.py: mounts all v1 API routes under /api/v1
    - db/session.py: initialises database connection pool on startup

How to run locally:
    uv run uvicorn main:app --reload --port 8000

How to run in production (Railway):
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import AuthMiddleware
from api.v1.router import v1_router
from config import get_settings
from db.session import close_db, init_db

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
# Configure before anything else so startup events are logged correctly.
# In production, Railway captures stdout so this goes to Railway's log viewer.

logging.basicConfig(
    level=logging.DEBUG if get_settings().ENVIRONMENT == "development" else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

settings = get_settings()

app = FastAPI(
    title="FlightHacker API",
    description=(
        "Finds the cheapest way between any two points using 20 hacking methods "
        "including hub arbitrage, open jaw, Avios portal arbitrage, positioning "
        "flights, and Crazy Mode."
    ),
    version="0.1.0",
    # Disable docs in production — no need to expose API structure publicly.
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
# Allows the React Native mobile app (running on a device/emulator) to call
# the API. In development we allow all origins. In production, restrict to
# the Railway domain and any custom domain once configured.

ALLOWED_ORIGINS = (
    ["*"]
    if settings.ENVIRONMENT == "development"
    else [
        "https://flighthacker.app",
        "https://api.flighthacker.app",
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------
# Handles authentication on every request. In development (DEV_AUTH_BYPASS=True)
# this injects a fake user so no auth setup is needed. In production it will
# verify Clerk JWTs. See api/middleware.py for full details.

app.add_middleware(AuthMiddleware)

# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------
# All v1 routes are mounted under /api/v1. Versioning means we can add /api/v2
# later without breaking existing mobile app clients.

app.include_router(v1_router)

# ---------------------------------------------------------------------------
# Startup and shutdown events
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """
    Runs once when the server starts.

    Initialises the database connection pool and loads static data CSVs
    into memory so the first request doesn't bear the loading cost.
    """
    logger.info("FlightHacker backend starting up (environment: %s)", settings.ENVIRONMENT)

    if settings.DEV_AUTH_BYPASS:
        logger.warning(
            "DEV_AUTH_BYPASS is enabled — all endpoints accessible without auth. "
            "This MUST be disabled in production."
        )

    await init_db()
    logger.info("Database connection pool initialised")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """
    Runs once when the server shuts down.

    Closes the database connection pool cleanly so no connections are leaked.
    Railway sends SIGTERM before stopping a deployment — this ensures
    in-flight requests complete and connections close gracefully.
    """
    logger.info("FlightHacker backend shutting down")
    await close_db()


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """
    Simple liveness probe.

    Why this exists: Railway (and any load balancer) pings this endpoint to
    verify the app is running. Returns 200 OK with basic status info.
    Does not check database or Redis — those are checked by a separate
    readiness endpoint added in a future iteration.
    """
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0",
        "dev_auth_bypass": settings.DEV_AUTH_BYPASS,
    }
