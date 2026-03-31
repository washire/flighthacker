"""
Shared response envelopes and error models.
"""
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class DataResponse(BaseModel, Generic[T]):
    """Standard success envelope: { data: <T> }"""
    data: T


class ErrorResponse(BaseModel):
    """Standard error envelope."""
    error: str
    detail: str | None = None
    code: str | None = None  # machine-readable error code


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_more: bool
