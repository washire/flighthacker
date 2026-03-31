"""
Search route — the main entry point for flight hacking queries.

POST /api/v1/search          — kick off a search, returns Phase 1 results fast
GET  /api/v1/search/{id}     — poll for Phase 2 deep results
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db, get_redis, get_current_user, get_app_settings
from models import SearchRequest, SearchResponse, SearchPhase, DataResponse
from services.hack_engine import HackEngine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=DataResponse[SearchResponse])
async def create_search(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    user_id: str = Depends(get_current_user),
    settings=Depends(get_app_settings),
):
    """
    Kick off a flight hack search.

    Returns Phase 1 results (direct + top 5 hubs) within ~3-5 seconds.
    A background task continues Phase 2 (all 20 methods, all hubs).
    Poll GET /search/{search_id} for the full results.
    """
    search_id = str(uuid.uuid4())
    engine = HackEngine(db=db, redis=redis, settings=settings)

    # Phase 1 — fast, synchronous
    phase1_results = await engine.run_phase_1(request)

    # Phase 2 — deep, runs in background
    background_tasks.add_task(engine.run_phase_2, search_id, request)

    direct_price = None
    if phase1_results:
        cash_only = [r for r in phase1_results if not r.is_award]
        if cash_only:
            direct_price = min(r.cost.total_gbp for r in cash_only)

    response = SearchResponse(
        search_id=search_id,
        request=request,
        results=phase1_results,
        phase=SearchPhase.PHASE_1,
        total_results=len(phase1_results),
        cheapest_gbp=min((r.cost.total_gbp for r in phase1_results), default=None),
        generated_at=datetime.now(timezone.utc),
        cached=False,
        direct_price_gbp=direct_price,
    )

    logger.info(
        "search.phase1 id=%s origin=%s dest=%s results=%d",
        search_id, request.origin, request.destination, len(phase1_results),
    )

    return DataResponse(data=response)


@router.get("/{search_id}", response_model=DataResponse[SearchResponse])
async def get_search_results(
    search_id: str,
    redis=Depends(get_redis),
    user_id: str = Depends(get_current_user),
):
    """
    Poll for Phase 2 deep results.

    Returns cached Phase 2 results if ready, otherwise Phase 1 results
    with phase=phase_1 so the client knows to keep polling.
    """
    cached = await redis.get(f"search:phase2:{search_id}")
    if cached is None:
        cached = await redis.get(f"search:phase1:{search_id}")
        if cached is None:
            raise HTTPException(status_code=404, detail="Search not found")

    response = SearchResponse.model_validate_json(cached)
    return DataResponse(data=response)
