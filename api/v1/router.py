"""
v1 API router — mounts all route modules under /api/v1.
"""
from fastapi import APIRouter

from api.v1.routes import search, alerts, users

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(search.router, prefix="/search", tags=["search"])
v1_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
v1_router.include_router(users.router, prefix="/users", tags=["users"])
