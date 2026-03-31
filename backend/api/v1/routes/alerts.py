"""
Price alert CRUD endpoints.

POST   /api/v1/alerts          — create alert rule
GET    /api/v1/alerts          — list user's alerts
DELETE /api/v1/alerts/{id}     — delete alert rule
PATCH  /api/v1/alerts/{id}     — toggle active / update thresholds
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.orm_models import AlertRule, SavedSearch
from dependencies import get_db, get_current_user
from models import (
    AlertRuleCreate,
    AlertRuleResponse,
    DataResponse,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=DataResponse[AlertRuleResponse], status_code=201)
async def create_alert(
    payload: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # Verify the saved search belongs to this user
    saved_search = await db.get(SavedSearch, payload.saved_search_id)
    if saved_search is None or saved_search.user_id != user_id:
        raise HTTPException(status_code=404, detail="Saved search not found")

    if payload.trigger_type == "target_price" and payload.target_price_gbp is None:
        raise HTTPException(status_code=422, detail="target_price_gbp required for target_price trigger")
    if payload.trigger_type == "percentage_drop" and payload.percentage_drop is None:
        raise HTTPException(status_code=422, detail="percentage_drop required for percentage_drop trigger")

    rule = AlertRule(
        user_id=user_id,
        saved_search_id=payload.saved_search_id,
        trigger_type=payload.trigger_type,
        target_price_gbp=payload.target_price_gbp,
        percentage_drop=payload.percentage_drop,
        is_active=True,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    logger.info("alert.created user=%s rule=%d", user_id, rule.id)
    return DataResponse(data=AlertRuleResponse.model_validate(rule))


@router.get("", response_model=DataResponse[PaginatedResponse[AlertRuleResponse]])
async def list_alerts(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    offset = (page - 1) * page_size
    result = await db.execute(
        select(AlertRule)
        .where(AlertRule.user_id == user_id)
        .order_by(AlertRule.created_at.desc())
        .offset(offset)
        .limit(page_size + 1)
    )
    rows = result.scalars().all()
    has_more = len(rows) > page_size
    items = [AlertRuleResponse.model_validate(r) for r in rows[:page_size]]
    return DataResponse(data=PaginatedResponse(
        items=items, total=len(items), page=page, page_size=page_size, has_more=has_more
    ))


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    rule = await db.get(AlertRule, alert_id)
    if rule is None or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.execute(delete(AlertRule).where(AlertRule.id == alert_id))
    await db.commit()


@router.patch("/{alert_id}", response_model=DataResponse[AlertRuleResponse])
async def update_alert(
    alert_id: int,
    is_active: bool | None = None,
    target_price_gbp: int | None = None,
    percentage_drop: float | None = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    rule = await db.get(AlertRule, alert_id)
    if rule is None or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail="Alert not found")
    if is_active is not None:
        rule.is_active = is_active
    if target_price_gbp is not None:
        rule.target_price_gbp = target_price_gbp
    if percentage_drop is not None:
        rule.percentage_drop = percentage_drop
    await db.commit()
    await db.refresh(rule)
    return DataResponse(data=AlertRuleResponse.model_validate(rule))
