"""
Authentication middleware.

In production: expects Bearer token in Authorization header.
In development (DEV_AUTH_BYPASS=True): injects a fake user_id so every
endpoint works without any auth setup.

Sets request.state.user_id — consumed by dependencies.get_current_user().
"""
from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from config import get_settings

logger = logging.getLogger(__name__)

# Paths that never require authentication
_PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()

        # Always allow public paths
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        # DEV bypass — inject fake user, skip all token validation
        if settings.DEV_AUTH_BYPASS:
            request.state.user_id = settings.DEV_USER_ID
            return await call_next(request)

        # Production: extract Bearer token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "Missing Bearer token"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        user_id = _verify_token(token)
        if user_id is None:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "Invalid or expired token"},
            )

        request.state.user_id = user_id
        return await call_next(request)


def _verify_token(token: str) -> str | None:
    """
    Verify a JWT/Clerk session token and return the user_id.
    Placeholder — swap in Clerk JWT verification when auth is wired up.
    Returns None if invalid.
    """
    # TODO: replace with Clerk JWKS verification
    # from clerk_backend_api import verify_token
    # payload = verify_token(token, jwks_url=settings.CLERK_JWKS_URL)
    # return payload.get("sub")
    logger.warning("Token verification not yet implemented — rejecting all tokens")
    return None
