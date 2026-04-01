"""
User profile endpoints.

GET   /api/v1/users/me         — get current user profile
PUT   /api/v1/users/me         — update avios balance, pence_per_point, ntfy_topic
POST  /api/v1/users/me/searches — save a search
GET   /api/v1/users/me/searches — list saved searches
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.orm_models import User, SavedSearch
from dependencies import get_db, get_current_user
from models import (
    UserResponse,
    UserUpdate,
    SavedSearchCreate,
    SavedSearchResponse,
    DataResponse,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/me", response_model=DataResponse[UserResponse])
async def get_me(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return DataResponse(data=UserResponse.model_validate(user))


@router.put("/me", response_model=DataResponse[UserResponse])
async def update_me(
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.avios_balance is not None:
        user.avios_balance = payload.avios_balance
    if payload.pence_per_point is not None:
        user.pence_per_point = payload.pence_per_point
    if payload.ntfy_topic is not None:
        user.ntfy_topic = payload.ntfy_topic
    await db.commit()
    await db.refresh(user)
    return DataResponse(data=UserResponse.model_validate(user))


@router.post("/me/searches", response_model=DataResponse[SavedSearchResponse], status_code=201)
async def save_search(
    payload: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    saved = SavedSearch(
        user_id=user_id,
        origin=payload.origin.upper(),
        destination=payload.destination.upper(),
        travel_date=payload.travel_date,
        return_date=payload.return_date,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    logger.info("saved_search.created user=%s id=%d", user_id, saved.id)
    return DataResponse(data=SavedSearchResponse.model_validate(saved))


@router.get("/me/searches", response_model=DataResponse[PaginatedResponse[SavedSearchResponse]])
async def list_saved_searches(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(SavedSearch)
        .where(SavedSearch.user_id == user_id)
        .order_by(SavedSearch.created_at.desc())
        .offset(offset)
        .limit(page_size + 1)
    )
    rows = result.scalars().all()
    has_more = len(rows) > page_size
    items = [SavedSearchResponse.model_validate(r) for r in rows[:page_size]]
    return DataResponse(data=PaginatedResponse(
        items=items, total=len(items), page=page, page_size=page_size, has_more=has_more
    ))
