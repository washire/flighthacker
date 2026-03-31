"""
Currency conversion service using frankfurter.app (ECB rates, free, no key).

Usage:
    converter = CurrencyConverter(redis)
    gbp_pence = await converter.usd_to_gbp_pence(49.99)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

_REDIS_KEY = "currency:usd_gbp_rate"


class CurrencyConverter:
    def __init__(self, redis) -> None:
        self._redis = redis
        self._settings = get_settings()

    async def usd_to_gbp_pence(self, usd_amount: float) -> int:
        """Convert USD amount to GBP pence. Returns int to avoid float drift."""
        rate = await self._get_rate()
        gbp = usd_amount * rate
        return round(gbp * 100)  # pence

    async def gbp_pence_to_usd(self, pence: int) -> float:
        rate = await self._get_rate()
        gbp = pence / 100
        return round(gbp / rate, 2)

    async def _get_rate(self) -> float:
        """Return USD→GBP rate, cached in Redis for 1 hour."""
        cached = await self._redis.get(_REDIS_KEY)
        if cached:
            return float(cached)

        rate = await self._fetch_rate()
        ttl = self._settings.CACHE_TTL_CURRENCY
        await self._redis.setex(_REDIS_KEY, ttl, str(rate))
        return rate

    async def _fetch_rate(self) -> float:
        url = f"{self._settings.FRANKFURTER_URL}/latest?from=USD&to=GBP"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                rate = data["rates"]["GBP"]
                logger.info("currency.fetched rate=%.6f at=%s", rate, datetime.now(timezone.utc))
                return float(rate)
        except Exception as exc:
            logger.error("currency.fetch_failed error=%s — using fallback 0.79", exc)
            return 0.79  # ECB approximate fallback
