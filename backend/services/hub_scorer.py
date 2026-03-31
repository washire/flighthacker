"""
Hub Productivity Scorer.

Dynamically scores airport hubs so the search engine knows WHICH hubs
to probe first for a given origin→destination pair.

Score = weighted average of:
  - Historical cheapness (how often this hub produced the cheapest result)
  - Route coverage (does this hub have a direct onward leg to destination?)
  - Alliance fit (Oneworld / Star Alliance / SkyTeam match for awards)

Scores are stored in Redis and decay over time so the engine adapts.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict

from config import get_settings
from repositories.static_data import StaticDataRepository

logger = logging.getLogger(__name__)

# Redis key pattern: hub_score:{origin}:{destination}
_KEY_PREFIX = "hub_score:"
_DEFAULT_TTL = 86400 * 7  # 7 days


@dataclass
class HubScore:
    hub: str           # IATA code e.g. "MAD"
    score: float       # 0.0 – 1.0 (higher = probe first)
    win_count: int = 0  # times this hub produced cheapest result
    probe_count: int = 0  # times this hub was probed at all
    has_direct_onward: bool = False
    alliance: str | None = None  # "oneworld" / "star" / "skyteam" / None


class HubScorer:
    def __init__(self, redis, static_repo: StaticDataRepository) -> None:
        self._redis = redis
        self._static = static_repo
        self._settings = get_settings()

    async def get_ranked_hubs(
        self,
        origin: str,
        destination: str,
        limit: int | None = None,
    ) -> list[str]:
        """
        Return hub IATA codes sorted by productivity score, best first.
        Falls back to static hub list if no Redis data yet.
        """
        limit = limit or self._settings.PHASE_1_HUB_COUNT
        scores = await self._load_scores(origin, destination)

        if not scores:
            # Cold start: use static hubs ordered by global traffic rank
            hubs = self._static.get_major_hubs(origin, destination)
            return hubs[:limit]

        ranked = sorted(scores, key=lambda s: s.score, reverse=True)
        return [s.hub for s in ranked][:limit]

    async def record_result(
        self,
        origin: str,
        destination: str,
        hub: str,
        was_cheapest: bool,
    ) -> None:
        """Update hub score after a search completes."""
        scores = await self._load_scores(origin, destination)
        score_map = {s.hub: s for s in scores}

        if hub not in score_map:
            score_map[hub] = HubScore(hub=hub, score=0.5)

        s = score_map[hub]
        s.probe_count += 1
        if was_cheapest:
            s.win_count += 1

        # Win rate with Laplace smoothing
        s.score = (s.win_count + 1) / (s.probe_count + 2)

        await self._save_scores(origin, destination, list(score_map.values()))

    async def _load_scores(self, origin: str, destination: str) -> list[HubScore]:
        key = f"{_KEY_PREFIX}{origin}:{destination}"
        raw = await self._redis.get(key)
        if raw is None:
            return []
        try:
            data = json.loads(raw)
            return [HubScore(**item) for item in data]
        except Exception as exc:
            logger.warning("hub_scorer.load_error key=%s err=%s", key, exc)
            return []

    async def _save_scores(
        self, origin: str, destination: str, scores: list[HubScore]
    ) -> None:
        key = f"{_KEY_PREFIX}{origin}:{destination}"
        await self._redis.setex(key, _DEFAULT_TTL, json.dumps([asdict(s) for s in scores]))
