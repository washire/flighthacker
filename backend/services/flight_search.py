"""
Flight search service — wraps the `fli` library (pip install flights).

fli reverse-engineers Google Flights' Protobuf/Base64 URL encoding.
No API key, completely free.

Usage:
    client = FlightSearchClient(redis, currency_converter)
    results = await client.search(origin="LHR", destination="NRT", date=date(2025,8,1))
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from datetime import date, datetime, timezone
from functools import partial
from typing import Any

# Limit concurrent Google Flights requests to avoid rate-limiting.
# Google blocks bursts of 10+ simultaneous requests from one IP.
# 3 concurrent = safe, quick enough for Phase 1.
_FLI_SEMAPHORE = asyncio.Semaphore(3)

from services.currency import CurrencyConverter
from config import get_settings

logger = logging.getLogger(__name__)


def _make_cache_key(origin: str, destination: str, travel_date: date, cabin: str) -> str:
    raw = f"{origin}:{destination}:{travel_date.isoformat()}:{cabin}"
    return "flight:" + hashlib.sha256(raw.encode()).hexdigest()[:16]


class RawFlightResult:
    """Normalised single flight result from fli."""
    __slots__ = (
        "origin", "destination", "departure_at", "arrival_at",
        "airline_code", "airline_name", "flight_number",
        "duration_minutes", "stops", "price_usd", "price_gbp_pence",
        "cabin", "deep_link",
    )

    def __init__(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class FlightSearchClient:
    def __init__(self, redis, currency: CurrencyConverter) -> None:
        self._redis = redis
        self._currency = currency
        self._settings = get_settings()

    async def search(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        cabin: str = "economy",
        passengers: int = 1,
        return_date: date | None = None,
    ) -> list[RawFlightResult]:
        """
        Search flights using fli. Returns up to MAX_SEARCH_RESULTS results,
        sorted by total price ascending.

        Results are cached in Redis for CACHE_TTL_FLIGHT_SEARCH seconds (6 hrs).
        """
        cache_key = _make_cache_key(origin, destination, travel_date, cabin)
        cached = await self._redis.get(cache_key)
        if cached:
            raw_list = json.loads(cached)
            return [RawFlightResult(**r) for r in raw_list]

        results = await self._fetch_live(
            origin, destination, travel_date, cabin, passengers, return_date
        )

        # RawFlightResult uses __slots__ so we serialise via slot names directly
        cacheable = [
            {s: getattr(r, s) for s in RawFlightResult.__slots__}
            for r in results
        ]
        # Convert datetime to ISO strings for JSON
        for item in cacheable:
            for k in ("departure_at", "arrival_at"):
                if isinstance(item[k], datetime):
                    item[k] = item[k].isoformat()

        await self._redis.setex(
            cache_key,
            self._settings.CACHE_TTL_FLIGHT_SEARCH,
            json.dumps(cacheable),
        )
        return results

    async def _fetch_live(
        self,
        origin: str,
        destination: str,
        travel_date: date,
        cabin: str,
        passengers: int,
        return_date: date | None,
    ) -> list[RawFlightResult]:
        """
        Call fli in a thread (it's sync) and parse results.
        fli returns Flight objects with .price, .legs, .duration etc.
        """
        loop = asyncio.get_running_loop()
        try:
            async with _FLI_SEMAPHORE:
                raw = await loop.run_in_executor(
                    None,
                    partial(
                        _fli_search_sync,
                        origin, destination, travel_date,
                        cabin, passengers, return_date,
                    ),
                )
        except Exception as exc:
            logger.error(
                "flight_search.fli_error origin=%s dest=%s date=%s err=%s",
                origin, destination, travel_date, exc,
            )
            return []

        results: list[RawFlightResult] = []
        for flight in raw[: self._settings.MAX_SEARCH_RESULTS * 3]:
            try:
                price_gbp = await self._currency.usd_to_gbp_pence(float(flight.price))
                leg = flight.legs[0] if flight.legs else None
                results.append(RawFlightResult(
                    origin=origin,
                    destination=destination,
                    # fli FlightLeg uses departure_datetime / arrival_datetime
                    departure_at=_parse_dt(leg.departure_datetime if leg else None),
                    arrival_at=_parse_dt(leg.arrival_datetime if leg else None),
                    airline_code=_airline_code(flight),
                    airline_name=_airline_name(flight),
                    flight_number=_flight_number(leg),
                    # fli FlightResult.duration is total trip duration in minutes
                    duration_minutes=int(getattr(flight, "duration", 0) or 0),
                    stops=int(getattr(flight, "stops", 0) or 0),
                    price_usd=float(flight.price),
                    price_gbp_pence=price_gbp,
                    cabin=cabin,
                    deep_link=getattr(flight, "url", None),
                ))
            except Exception as exc:
                logger.debug("flight_search.parse_skip err=%s", exc)
                continue

        results.sort(key=lambda r: r.price_gbp_pence)
        return results[: self._settings.MAX_SEARCH_RESULTS]


# ---------------------------------------------------------------------------
# Sync helper — runs in executor
# ---------------------------------------------------------------------------


def _fli_search_sync(
    origin: str,
    destination: str,
    travel_date: date,
    cabin: str,
    passengers: int,
    return_date: date | None,
) -> list:
    """
    Wrapper around fli's sync API (pip install flights installs as fli module).

    fli uses Airport and SeatType enums — airport codes must be valid IATA codes
    present in the fli Airport enum. Unknown codes raise ValueError.
    """
    from fli.search import SearchFlights, SearchFlightsFilters  # type: ignore
    from fli.models import Airport, SeatType, PassengerInfo  # type: ignore

    _CABIN_MAP = {
        "economy": SeatType.ECONOMY,
        "premium_economy": SeatType.PREMIUM_ECONOMY,
        "business": SeatType.BUSINESS,
        "first": SeatType.FIRST,
    }
    seat_type = _CABIN_MAP.get(cabin, SeatType.ECONOMY)

    try:
        dep_airport = Airport[origin.upper()]
        arr_airport = Airport[destination.upper()]
    except KeyError as exc:
        raise ValueError(f"Airport code not in fli enum: {exc}") from exc

    filters = SearchFlightsFilters(
        departure_airport=dep_airport,
        arrival_airport=arr_airport,
        departure_date=travel_date.strftime("%Y-%m-%d"),
        passenger_info=PassengerInfo(adults=passengers),
        seat_type=seat_type,
    )
    searcher = SearchFlights()
    results = searcher.search(filters)
    return results or []


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _airline_code(flight: Any) -> str:
    # fli: leg.airline is an Airline enum; .name is the IATA code e.g. "BA"
    try:
        return flight.legs[0].airline.name or "??"
    except Exception:
        return "??"


def _airline_name(flight: Any) -> str:
    # fli: leg.airline.value is the full name e.g. "British Airways"
    try:
        return flight.legs[0].airline.value or "Unknown Airline"
    except Exception:
        return "Unknown Airline"


def _flight_number(leg: Any) -> str:
    try:
        return f"{leg.airline.name}{leg.flight_number}"
    except Exception:
        return "??0"
