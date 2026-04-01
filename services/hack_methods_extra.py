"""
Additional hack methods — imported by HackEngine.

Kept separate to stay within 300-line file limit.
Contains: split ticket, date optimisation, error fares.
"""
from __future__ import annotations

import asyncio
import logging
import math
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import TYPE_CHECKING

from models.search import (
    CabinClass, HackMethod, FlightLeg,
    CostBreakdown, SavingExplanation, ItineraryResult, SearchRequest,
)
from services.error_fares import ErrorFareScanner

if TYPE_CHECKING:
    from services.hack_engine import HackEngine

logger = logging.getLogger(__name__)

# Max extra distance ratio to still qualify as "on-route" for split ticket
_MAX_DETOUR_RATIO = 1.35


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


async def method_split_ticket(
    engine: "HackEngine", req: SearchRequest
) -> list[ItineraryResult]:
    """
    Split ticket: buy origin→midpoint and midpoint→destination separately.

    Different from hub_arbitrage: we filter to only hubs that are
    geographically ON the route (detour ratio < 1.35), so these feel
    like natural stopovers rather than wild detours.

    Classic example: LHR→AMS + AMS→NRT can be £200 cheaper than LHR→NRT.
    """
    airports = engine._static._get_airports()
    orig_data = airports.get(req.origin.upper())
    dest_data = airports.get(req.destination.upper())
    if not orig_data or not dest_data:
        return []

    orig_lat, orig_lon = float(orig_data["lat"]), float(orig_data["lon"])
    dest_lat, dest_lon = float(dest_data["lat"]), float(dest_data["lon"])
    direct_km = _haversine_km(orig_lat, orig_lon, dest_lat, dest_lon)

    if direct_km < 500:
        # Too short to meaningfully split
        return []

    # Get major hubs and filter to on-route ones
    all_hubs = engine._static.get_major_hubs(req.origin, req.destination)
    on_route_hubs: list[str] = []
    for hub in all_hubs[:30]:
        hub_data = airports.get(hub.upper())
        if not hub_data:
            continue
        hub_lat, hub_lon = float(hub_data["lat"]), float(hub_data["lon"])
        via_km = (
            _haversine_km(orig_lat, orig_lon, hub_lat, hub_lon)
            + _haversine_km(hub_lat, hub_lon, dest_lat, dest_lon)
        )
        if direct_km > 0 and (via_km / direct_km) <= _MAX_DETOUR_RATIO:
            on_route_hubs.append(hub)
        if len(on_route_hubs) >= 8:
            break

    results: list[ItineraryResult] = []

    async def _probe(hub: str) -> list[ItineraryResult]:
        leg1_list, leg2_list = await asyncio.gather(
            engine._flight.search(
                req.origin, hub, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            ),
            engine._flight.search(
                hub, req.destination, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            ),
        )
        if not leg1_list or not leg2_list:
            return []
        r1, r2 = leg1_list[0], leg2_list[0]
        combined = r1.price_gbp_pence + r2.price_gbp_pence

        from services.cost_calculator import CostInputs
        cost = engine._calc.calculate(CostInputs(
            base_fare_gbp_pence=combined,
            taxes_gbp_pence=0,
        ))
        leg1 = engine._raw_to_leg(r1, req.cabin_class)
        leg2 = engine._raw_to_leg(r2, req.cabin_class)
        return [ItineraryResult(
            result_id=str(uuid.uuid4()),
            method=HackMethod.SPLIT_TICKET,
            outbound_legs=[leg1, leg2],
            return_legs=[],
            ground_legs=[],
            cost=cost,
            saving=SavingExplanation(
                headline=f"Split ticket via {hub} — two separate bookings",
                detail=(
                    f"Buy {req.origin}→{hub} and {hub}→{req.destination} as "
                    f"separate tickets. {hub} is on the route so no backtracking. "
                    f"Must self-transfer at {hub} — allow 2.5+ hours minimum."
                ),
            ),
            total_duration_minutes=(
                r1.duration_minutes + r2.duration_minutes + 90
            ),
            is_self_transfer=True,
            data_freshness=datetime.now(timezone.utc),
            deep_link=None,
        )]

    nested = await asyncio.gather(*[_probe(h) for h in on_route_hubs])
    for sub in nested:
        results.extend(sub)
    return results


async def method_date_optimisation(
    engine: "HackEngine", req: SearchRequest
) -> list[ItineraryResult]:
    """
    Date optimisation: search ±3 days and surface cheaper alternatives.

    If flying 2 days later saves £80, we surface that as a result with
    method=DATE_OPTIMISATION so the user can see the trade-off clearly.
    Returns up to 3 results (the cheapest alternative dates).
    """
    delta_days = [-3, -2, -1, 1, 2, 3]
    alt_dates: list[date] = []
    for d in delta_days:
        alt = req.outbound_date + timedelta(days=d)
        # Don't search past dates
        if alt >= date.today():
            alt_dates.append(alt)

    async def _search_date(alt_date: date) -> list[ItineraryResult]:
        raw_list = await engine._flight.search(
            req.origin, req.destination, alt_date,
            cabin=req.cabin_class.value, passengers=req.passengers,
        )
        if not raw_list:
            return []
        raw = raw_list[0]

        from services.cost_calculator import CostInputs
        cost = engine._calc.calculate(CostInputs(
            base_fare_gbp_pence=raw.price_gbp_pence,
            taxes_gbp_pence=0,
        ))
        day_diff = (alt_date - req.outbound_date).days
        direction = f"+{day_diff}" if day_diff > 0 else str(day_diff)
        return [ItineraryResult(
            result_id=str(uuid.uuid4()),
            method=HackMethod.DATE_OPTIMISATION,
            outbound_legs=[engine._raw_to_leg(raw, req.cabin_class)],
            return_legs=[],
            ground_legs=[],
            cost=cost,
            saving=SavingExplanation(
                headline=f"Fly {direction} days ({alt_date.strftime('%a %d %b')}) — different price",
                detail=(
                    f"Shifting your travel date by {abs(day_diff)} day(s) "
                    f"to {alt_date.isoformat()} changes the price. "
                    f"Flexible travellers often save 20-40% by avoiding "
                    f"peak departure days."
                ),
            ),
            total_duration_minutes=raw.duration_minutes,
            is_self_transfer=False,
            data_freshness=datetime.now(timezone.utc),
            deep_link=raw.deep_link,
        )]

    nested = await asyncio.gather(*[_search_date(d) for d in alt_dates])
    flat = [r for sub in nested for r in sub]
    # Only return dates cheaper than the requested date's cheapest result
    flat.sort(key=lambda r: r.cost.total_gbp)
    return flat[:3]


async def method_error_fares(
    engine: "HackEngine", req: SearchRequest
) -> list[ItineraryResult]:
    """
    Error fare detection: scans Secret Flying + Fly4Free RSS feeds.

    Surfaces deals mentioning the user's origin or destination. Price is
    parsed from the deal title (best-effort). User clicks through to the
    deal page to book — we don't book it ourselves.
    """
    scanner = ErrorFareScanner(engine._redis)
    deals = await scanner.find_deals(req.origin, req.destination)

    results: list[ItineraryResult] = []
    for deal in deals[:5]:
        price_pence = deal.get("price_hint_gbp")
        if price_pence is None:
            # Can't rank it without a price — skip
            continue

        from services.cost_calculator import CostInputs
        cost = engine._calc.calculate(CostInputs(
            base_fare_gbp_pence=price_pence,
            taxes_gbp_pence=0,
        ))
        results.append(ItineraryResult(
            result_id=str(uuid.uuid4()),
            method=HackMethod.ERROR_FARE,
            outbound_legs=[],   # No leg data — user books via deep link
            return_legs=[],
            ground_legs=[],
            cost=cost,
            saving=SavingExplanation(
                headline=f"Error/sale fare: {deal['title'][:80]}",
                detail=(
                    f"Deal found on {deal['source'].split('/')[2]}. "
                    f"Error fares disappear within hours — book immediately. "
                    f"Price shown is approximate from deal description."
                ),
            ),
            total_duration_minutes=0,
            is_self_transfer=False,
            requires_visa_check=True,
            data_freshness=datetime.now(timezone.utc),
            deep_link=deal.get("url"),
        ))
    return results
