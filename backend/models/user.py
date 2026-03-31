"""
Pydantic models for user profile, saved searches, and alert rules.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from .search import AlertTriggerType


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class UserBase(BaseModel):
    email: EmailStr
    avios_balance: int = Field(0, ge=0)
    pence_per_point: float = Field(1.0, gt=0)
    ntfy_topic: str | None = None


class UserCreate(UserBase):
    user_id: str  # Clerk user ID (or dev bypass ID)


class UserUpdate(BaseModel):
    avios_balance: int | None = Field(None, ge=0)
    pence_per_point: float | None = Field(None, gt=0)
    ntfy_topic: str | None = None


class UserResponse(UserBase):
    user_id: str
    subscription_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Saved Search
# ---------------------------------------------------------------------------


class SavedSearchCreate(BaseModel):
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    travel_date: datetime
    return_date: datetime | None = None


class SavedSearchResponse(SavedSearchCreate):
    id: int
    user_id: str
    last_price_gbp: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Alert Rule
# ---------------------------------------------------------------------------


class AlertRuleCreate(BaseModel):
    saved_search_id: int
    trigger_type: AlertTriggerType
    target_price_gbp: int | None = Field(None, ge=0)
    percentage_drop: float | None = Field(None, gt=0, le=100)


class AlertRuleResponse(AlertRuleCreate):
    id: int
    user_id: str
    is_active: bool
    last_notified_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
