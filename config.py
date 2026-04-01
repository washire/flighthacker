"""
config.py
---------
Central configuration for the FlightHacker backend.

Why this exists:
    All environment variables, secrets, and feature flags live in one place.
    Nothing is hardcoded anywhere else in the codebase — everything reads
    from this module. This means changing behaviour (e.g. enabling a feature,
    pointing at a different database) never requires touching business logic.

What it connects to:
    - Every other module imports Settings or get_settings() from here.
    - Values are read from environment variables at startup, with sensible
      defaults for local development.
    - In production (Railway), set these as environment variables in the
      Railway dashboard. Never commit a .env file with real secrets.

Feature flags:
    Each major feature has an on/off toggle. If a downstream dependency
    breaks (e.g. an award scraper stops working), flip its flag to False
    and redeploy — no code changes needed, the feature degrades gracefully.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All application configuration in one typed, validated class.

    Pydantic-settings reads each field from the matching environment variable
    (case-insensitive). Missing required fields raise a clear error at startup
    rather than failing silently later.

    For local development, create a file called `.env` in the `backend/`
    directory. It is git-ignored and never committed.

    Example .env:
        DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/flighthacker
        REDIS_URL=redis://localhost:6379/0
        DEV_AUTH_BYPASS=true
    """

    model_config = SettingsConfigDict(
        # Load from .env file if present. Safe to omit in production.
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra fields in .env so adding comments doesn't break things.
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Core infrastructure
    # -------------------------------------------------------------------------

    # PostgreSQL connection string. asyncpg driver required for async SQLAlchemy.
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/flighthacker"

    # Redis connection. Used for caching and Celery task queue.
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application environment. Controls logging verbosity and error detail.
    # Values: "development" | "staging" | "production"
    ENVIRONMENT: str = "development"

    # Secret key for signing internal tokens. Change this in production.
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY: str = "change-me-in-production-generate-with-secrets-module"

    # -------------------------------------------------------------------------
    # External service URLs (no auth required)
    # -------------------------------------------------------------------------

    # frankfurter.app: free ECB exchange rates, no API key, no signup.
    # Used to convert all USD prices from fli into GBP for display.
    FRANKFURTER_URL: str = "https://api.frankfurter.app"

    # ntfy.sh: free push notification service. One HTTP POST = push notification.
    # We use the public server for development. Self-host for production privacy.
    NTFY_BASE_URL: str = "https://ntfy.sh"

    # -------------------------------------------------------------------------
    # Cache TTLs (seconds)
    # -------------------------------------------------------------------------

    # How long to cache an exact route+date search result.
    # 6 hours: prices don't move that fast, and this prevents hammering Google.
    CACHE_TTL_FLIGHT_SEARCH: int = 21_600  # 6 hours

    # Currency rates change slowly. Cache for 1 hour.
    CACHE_TTL_CURRENCY: int = 3_600  # 1 hour

    # Ground transport costs (airport to city) almost never change.
    # Cache aggressively.
    CACHE_TTL_GROUND_TRANSPORT: int = 2_592_000  # 30 days

    # Hub productivity scores are updated as new data comes in.
    CACHE_TTL_HUB_SCORES: int = 604_800  # 7 days

    # -------------------------------------------------------------------------
    # Search configuration
    # -------------------------------------------------------------------------

    # Maximum number of results returned per search.
    # Ranked by true all-in cost, top N shown.
    MAX_SEARCH_RESULTS: int = 20

    # Radius in km around origin/destination to find secondary airports.
    SECONDARY_AIRPORT_RADIUS_KM: int = 150

    # Number of top-scoring hubs to query in Phase 1 (fast, immediate results).
    # These fire in the first 3-5 seconds. More = slower Phase 1.
    PHASE_1_HUB_COUNT: int = 5

    # Minimum layover time (minutes) to flag as "city exploration opportunity".
    LAYOVER_EXPLORE_THRESHOLD_MINS: int = 360  # 6 hours

    # Minimum layover time (minutes) for "proper stopover" messaging.
    LAYOVER_STOPOVER_THRESHOLD_MINS: int = 720  # 12 hours

    # -------------------------------------------------------------------------
    # Feature flags
    # -------------------------------------------------------------------------
    # Each major feature can be toggled without code changes.
    # Set to False in .env or Railway env vars to disable a feature.

    # Award flight search (ba_rewards + flightplan scrapers).
    # Disable if award scrapers are temporarily broken.
    FEATURE_AWARDS_ENABLED: bool = True

    # Oneworld portal arbitrage (points cost + fuel surcharge comparison).
    # Requires award_charts and surcharges static data to be populated.
    FEATURE_AVIOS_PORTAL_ARBITRAGE: bool = True

    # Error fare monitoring (Secret Flying RSS + price anomaly detection).
    FEATURE_ERROR_FARES_ENABLED: bool = True

    # Stopover programme suggestions (Turkish, Qatar, Icelandair etc.)
    # Requires stopovers static data to be populated.
    FEATURE_STOPOVER_PROGRAMS: bool = True

    # UK Air Passenger Duty calculation.
    # Requires apd static data to be populated.
    FEATURE_APD_CALCULATION: bool = True

    # Ground transport cost inclusion in true all-in cost.
    # Requires ground_transport static data to be populated.
    FEATURE_GROUND_TRANSPORT: bool = True

    # Avios earning suggestions on ancillary spend (hotels, car hire etc.)
    # Requires avios_partners static data to be populated.
    FEATURE_AVIOS_EARNING: bool = True

    # Crazy Mode (Shenanigans Mode): removes all comfort constraints,
    # enables multi-modal routing, pure lowest-cost optimisation.
    FEATURE_CRAZY_MODE: bool = True

    # Long layover city exploration suggestions.
    FEATURE_LAYOVER_EXPLORE: bool = True

    # -------------------------------------------------------------------------
    # Development / testing
    # -------------------------------------------------------------------------

    # DEV_AUTH_BYPASS: when True, all API endpoints are accessible without
    # authentication. Every request is treated as a known test user.
    #
    # CRITICAL: This MUST be False in production. It is True by default only
    # to allow development without setting up Clerk auth.
    # Set DEV_AUTH_BYPASS=false in Railway environment variables.
    DEV_AUTH_BYPASS: bool = True

    # ID used for the fake user when DEV_AUTH_BYPASS is True.
    # All test searches and alerts are attributed to this user.
    DEV_USER_ID: str = "dev-user-001"


@lru_cache
def get_settings() -> Settings:
    """
    Returns the singleton Settings instance.

    Why lru_cache: Settings reads from env vars and .env on every instantiation.
    Caching ensures we only do that once at startup, not on every request.

    Usage throughout the app:
        from config import get_settings
        settings = get_settings()
        print(settings.DATABASE_URL)
    """
    return Settings()
