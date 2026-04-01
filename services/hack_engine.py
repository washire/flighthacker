"""
HackEngine — the central search orchestrator.

Phase 1 (fast, ~3-5 s):
  - Direct cheapest (method 1)
  - Secondary airports near origin/destination (methods 2, 3)
  - Hub arbitrage via top-5 scored hubs (method 4)
  - Open jaw basic (method 5)

Phase 2 (deep, ~15-30 s, runs in background):
  - All Phase 1 methods + extended hub list
  - Fare zone open jaw
  - Mixed cabin
  - Positioning flight
  - Oneworld portal arbitrage (if feature flag on)
  - Avios reward (if feature flag on + user has balance)
  - APD avoidance
  - Stopover programs (if feature flag on)
  - Layover explore (if feature flag on)
  - Crazy mode (if requested)
  - Error fares scan (if feature flag on)

Each method produces zero or more ItineraryResult objects.
Results are ranked by total_gbp, deduplicated by flight fingerprint,
and the cheapest-per-method set is returned.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from models.search import (
    CabinClass, HackMethod, FlightLeg, GroundLeg,
    CostBreakdown, SavingExplanation, ItineraryResult,
    SearchRequest, SearchPhase, SearchResponse,
)
from repositories.static_data import StaticDataRepository
from services.flight_search import FlightSearchClient, RawFlightResult
from services.hub_scorer import HubScorer
from services.cost_calculator import CostCalculator, CostInputs
from services.currency import CurrencyConverter
from services.hack_methods_extra import (
    method_split_ticket,
    method_date_optimisation,
    method_error_fares,
)

logger = logging.getLogger(__name__)

# Airports within this radius count as "nearby" for secondary airport method
_SECONDARY_RADIUS_KM = 150


class HackEngine:
    def __init__(
        self,
        db: AsyncSession,
        redis: Any,
        settings: Settings,
    ) -> None:
        self._db = db
        self._redis = redis
        self._settings = settings
        currency = CurrencyConverter(redis)
        self._flight = FlightSearchClient(redis, currency)
        static_repo = StaticDataRepository()
        self._scorer = HubScorer(redis, static_repo)
        self._calc = CostCalculator(static_repo)
        self._static = static_repo

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_phase_1(self, req: SearchRequest) -> list[ItineraryResult]:
        """Run fast methods. Returns results sorted cheapest first."""
        tasks = [
            self._method_direct(req),
            self._method_secondary_airports(req),
            self._method_hub_arbitrage(req, phase=1),
            self._method_open_jaw(req),
            method_split_ticket(self, req),
            method_date_optimisation(self, req),
        ]
        results = await self._gather(tasks)
        direct_price = self._cheapest_cash(results)
        self._annotate_savings(results, direct_price)

        # Cache Phase 1 results for polling
        response = SearchResponse(
            search_id="pending",
            request=req,
            results=results,
            phase=SearchPhase.PHASE_1,
            total_results=len(results),
            cheapest_gbp=min((r.cost.total_gbp for r in results), default=None),
            generated_at=datetime.now(timezone.utc),
            cached=False,
            direct_price_gbp=direct_price,
        )
        await self._redis.setex(
            f"search:phase1:pending",
            self._settings.CACHE_TTL_FLIGHT_SEARCH,
            response.model_dump_json(),
        )
        return results

    async def run_phase_2(self, search_id: str, req: SearchRequest) -> None:
        """
        Deep search. Runs in background after Phase 1.
        Writes final results to Redis key search:phase2:{search_id}.
        """
        tasks = [
            self._method_direct(req),
            self._method_secondary_airports(req),
            self._method_hub_arbitrage(req, phase=2),
            self._method_open_jaw(req),
            self._method_fare_zone_open_jaw(req),
            self._method_mixed_cabin(req),
            self._method_positioning(req),
            self._method_apd_avoidance(req),
        ]

        if self._settings.FEATURE_AVIOS_PORTAL_ARBITRAGE:
            tasks.append(self._method_oneworld_portal(req))
        if self._settings.FEATURE_AWARDS_ENABLED and req.avios_balance:
            tasks.append(self._method_avios_reward(req))
        if self._settings.FEATURE_STOPOVER_PROGRAMS:
            tasks.append(self._method_stopover(req))
        if self._settings.FEATURE_LAYOVER_EXPLORE:
            tasks.append(self._method_layover_explore(req))
        if req.crazy_mode and self._settings.FEATURE_CRAZY_MODE:
            tasks.append(self._method_crazy_mode(req))

        # Always run these three in Phase 2
        tasks.append(method_split_ticket(self, req))
        tasks.append(method_date_optimisation(self, req))
        if self._settings.FEATURE_ERROR_FARES_ENABLED:
            tasks.append(method_error_fares(self, req))

        results = await self._gather(tasks)
        direct_price = self._cheapest_cash(results)
        self._annotate_savings(results, direct_price)

        # Update hub scorer with winners
        if results:
            cheapest = results[0]
            for leg in cheapest.outbound_legs:
                if leg.stops > 0:
                    # middle airport is the hub
                    pass  # hub scoring done per-method

        response = SearchResponse(
            search_id=search_id,
            request=req,
            results=results,
            phase=SearchPhase.COMPLETE,
            total_results=len(results),
            cheapest_gbp=min((r.cost.total_gbp for r in results), default=None),
            generated_at=datetime.now(timezone.utc),
            cached=False,
            direct_price_gbp=direct_price,
        )
        await self._redis.setex(
            f"search:phase2:{search_id}",
            self._settings.CACHE_TTL_FLIGHT_SEARCH,
            response.model_dump_json(),
        )
        logger.info("phase2.complete search_id=%s results=%d", search_id, len(results))

    # ------------------------------------------------------------------
    # Individual hack methods
    # ------------------------------------------------------------------

    async def _method_direct(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 1: Plain direct/cheapest cash flight."""
        raw_list = await self._flight.search(
            req.origin, req.destination, req.outbound_date,
            cabin=req.cabin_class.value, passengers=req.passengers,
        )
        results = []
        for raw in raw_list[:3]:
            leg = self._raw_to_leg(raw, req.cabin_class)
            cost = self._calc.calculate(CostInputs(
                base_fare_gbp_pence=raw.price_gbp_pence,
                taxes_gbp_pence=0,
                carrier_surcharge_pence=0,
            ))
            results.append(self._make_result(
                method=HackMethod.DIRECT_CHEAPEST,
                outbound=[leg],
                cost=cost,
                duration=raw.duration_minutes,
                data_freshness=datetime.now(timezone.utc),
                deep_link=raw.deep_link,
                headline=f"Direct cheapest — {req.origin}→{req.destination}",
                detail="Cheapest direct or one-stop cash fare on this route.",
            ))
        return results

    async def _method_secondary_airports(self, req: SearchRequest) -> list[ItineraryResult]:
        """Methods 2 & 3: Try nearby airports within 150 km."""
        results = []
        nearby_origins = self._static.get_nearby_airports(req.origin, _SECONDARY_RADIUS_KM)
        nearby_dests = self._static.get_nearby_airports(req.destination, _SECONDARY_RADIUS_KM)

        # Search from alt origin to main destination
        for alt_origin in nearby_origins[:3]:
            raw_list = await self._flight.search(
                alt_origin, req.destination, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            for raw in raw_list[:1]:
                ground_pence = self._calc.ground_transport_cost(alt_origin)
                leg = self._raw_to_leg(raw, req.cabin_class)
                cost = self._calc.calculate(CostInputs(
                    base_fare_gbp_pence=raw.price_gbp_pence,
                    taxes_gbp_pence=0,
                    ground_transport_pence=ground_pence,
                ))
                ground_leg = self._make_ground_leg(req.origin, alt_origin, ground_pence)
                results.append(self._make_result(
                    method=HackMethod.NEARBY_ORIGIN,
                    outbound=[leg],
                    ground_legs=[ground_leg] if ground_leg else [],
                    cost=cost,
                    duration=raw.duration_minutes,
                    data_freshness=datetime.now(timezone.utc),
                    deep_link=raw.deep_link,
                    headline=f"Fly from {alt_origin} instead of {req.origin}",
                    detail=(
                        f"{alt_origin} is a secondary airport near {req.origin}. "
                        f"Ground transfer included in total cost."
                    ),
                ))

        # Search from main origin to alt destination
        for alt_dest in nearby_dests[:3]:
            raw_list = await self._flight.search(
                req.origin, alt_dest, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            for raw in raw_list[:1]:
                ground_pence = self._calc.ground_transport_cost(alt_dest)
                leg = self._raw_to_leg(raw, req.cabin_class)
                cost = self._calc.calculate(CostInputs(
                    base_fare_gbp_pence=raw.price_gbp_pence,
                    taxes_gbp_pence=0,
                    ground_transport_pence=ground_pence,
                ))
                ground_leg = self._make_ground_leg(alt_dest, req.destination, ground_pence)
                results.append(self._make_result(
                    method=HackMethod.NEARBY_DESTINATION,
                    outbound=[leg],
                    ground_legs=[ground_leg] if ground_leg else [],
                    cost=cost,
                    duration=raw.duration_minutes,
                    data_freshness=datetime.now(timezone.utc),
                    deep_link=raw.deep_link,
                    headline=f"Land at {alt_dest} instead of {req.destination}",
                    detail=(
                        f"{alt_dest} is a secondary airport near {req.destination}. "
                        f"Ground transfer included in total cost."
                    ),
                ))
        return results

    async def _method_hub_arbitrage(
        self, req: SearchRequest, phase: int = 1
    ) -> list[ItineraryResult]:
        """Method 4: Two separate tickets via a hub (often far cheaper than direct)."""
        limit = self._settings.PHASE_1_HUB_COUNT if phase == 1 else 20
        hubs = await self._scorer.get_ranked_hubs(req.origin, req.destination, limit=limit)
        results = []

        async def _probe_hub(hub: str) -> list[ItineraryResult]:
            leg1_list, leg2_list = await asyncio.gather(
                self._flight.search(req.origin, hub, req.outbound_date,
                    cabin=req.cabin_class.value, passengers=req.passengers),
                self._flight.search(hub, req.destination, req.outbound_date,
                    cabin=req.cabin_class.value, passengers=req.passengers),
            )
            if not leg1_list or not leg2_list:
                return []
            raw1, raw2 = leg1_list[0], leg2_list[0]
            combined_pence = raw1.price_gbp_pence + raw2.price_gbp_pence
            leg1 = self._raw_to_leg(raw1, req.cabin_class)
            leg2 = self._raw_to_leg(raw2, req.cabin_class)
            cost = self._calc.calculate(CostInputs(
                base_fare_gbp_pence=combined_pence,
                taxes_gbp_pence=0,
                carrier_surcharge_pence=0,
            ))
            return [self._make_result(
                method=HackMethod.HUB_ARBITRAGE,
                outbound=[leg1, leg2],
                cost=cost,
                duration=raw1.duration_minutes + raw2.duration_minutes + 90,
                data_freshness=datetime.now(timezone.utc),
                is_self_transfer=True,
                headline=f"Two tickets via {hub} hub",
                detail=(
                    f"Book {req.origin}→{hub} and {hub}→{req.destination} separately. "
                    f"You must self-transfer at {hub} — allow 3+ hours."
                ),
            )]

        hub_results = await asyncio.gather(*[_probe_hub(h) for h in hubs])
        for hr in hub_results:
            results.extend(hr)
        return results

    async def _method_open_jaw(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 5: Fly into a different destination city, return from another."""
        if req.return_date is None:
            return []
        alt_dests = self._static.get_nearby_airports(req.destination, _SECONDARY_RADIUS_KM)
        results = []
        for alt in alt_dests[:2]:
            raw_out = await self._flight.search(
                req.origin, req.destination, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            raw_ret = await self._flight.search(
                alt, req.origin, req.return_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            if not raw_out or not raw_ret:
                continue
            ro, rr = raw_out[0], raw_ret[0]
            cost = self._calc.calculate(CostInputs(
                base_fare_gbp_pence=ro.price_gbp_pence + rr.price_gbp_pence,
                taxes_gbp_pence=0,
            ))
            results.append(self._make_result(
                method=HackMethod.OPEN_JAW,
                outbound=[self._raw_to_leg(ro, req.cabin_class)],
                return_legs=[self._raw_to_leg(rr, req.cabin_class)],
                cost=cost,
                duration=ro.duration_minutes + rr.duration_minutes,
                data_freshness=datetime.now(timezone.utc),
                headline=f"Open jaw: fly in {req.destination}, fly home from {alt}",
                detail=(
                    f"Arrive at {req.destination}, return from {alt}. "
                    f"Ground transport between the two airports not included."
                ),
            ))
        return results

    async def _method_fare_zone_open_jaw(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 6: Airports in same BA fare zone treated as interchangeable."""
        same_zone = self._static.get_same_fare_zone_airports(req.destination)
        results = []
        for zone_airport in same_zone[:3]:
            raw_list = await self._flight.search(
                req.origin, zone_airport, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            for raw in raw_list[:1]:
                cost = self._calc.calculate(CostInputs(
                    base_fare_gbp_pence=raw.price_gbp_pence,
                    taxes_gbp_pence=0,
                ))
                results.append(self._make_result(
                    method=HackMethod.FARE_ZONE_OPEN_JAW,
                    outbound=[self._raw_to_leg(raw, req.cabin_class)],
                    cost=cost,
                    duration=raw.duration_minutes,
                    data_freshness=datetime.now(timezone.utc),
                    headline=f"Same fare zone: use {zone_airport} instead of {req.destination}",
                    detail=(
                        f"{zone_airport} is in the same BA fare pricing zone as {req.destination}. "
                        f"Can be cheaper due to lower demand on this specific route."
                    ),
                ))
        return results

    async def _method_mixed_cabin(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 7: Economy on long haul, business positioning."""
        if req.cabin_class == CabinClass.ECONOMY:
            return []
        raw_eco = await self._flight.search(
            req.origin, req.destination, req.outbound_date,
            cabin="economy", passengers=req.passengers,
        )
        raw_biz = await self._flight.search(
            req.origin, req.destination, req.outbound_date,
            cabin=req.cabin_class.value, passengers=req.passengers,
        )
        if not raw_eco or not raw_biz:
            return []
        eco_price = raw_eco[0].price_gbp_pence
        biz_price = raw_biz[0].price_gbp_pence
        if eco_price >= biz_price:
            return []
        cost = self._calc.calculate(CostInputs(
            base_fare_gbp_pence=eco_price, taxes_gbp_pence=0
        ))
        return [self._make_result(
            method=HackMethod.MIXED_CABIN,
            outbound=[self._raw_to_leg(raw_eco[0], CabinClass.ECONOMY)],
            cost=cost,
            duration=raw_eco[0].duration_minutes,
            data_freshness=datetime.now(timezone.utc),
            headline="Mixed cabin: economy saves vs requested cabin",
            detail=(
                f"Economy on this route is significantly cheaper than "
                f"{req.cabin_class.value}. Consider downgrading."
            ),
        )]

    async def _method_positioning(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 8: Fly to a hub first as a separate cheap ticket."""
        hubs = self._static.get_major_departure_hubs(req.origin)
        results = []
        for hub in hubs[:3]:
            pos_list = await self._flight.search(
                req.origin, hub, req.outbound_date,
                cabin="economy", passengers=req.passengers,
            )
            main_list = await self._flight.search(
                hub, req.destination, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            if not pos_list or not main_list:
                continue
            pos, main = pos_list[0], main_list[0]
            combined = pos.price_gbp_pence + main.price_gbp_pence
            cost = self._calc.calculate(CostInputs(
                base_fare_gbp_pence=main.price_gbp_pence,
                taxes_gbp_pence=0,
                positioning_flight_pence=pos.price_gbp_pence,
            ))
            results.append(self._make_result(
                method=HackMethod.POSITIONING_FLIGHT,
                outbound=[
                    self._raw_to_leg(pos, CabinClass.ECONOMY),
                    self._raw_to_leg(main, req.cabin_class),
                ],
                cost=cost,
                duration=pos.duration_minutes + main.duration_minutes + 120,
                data_freshness=datetime.now(timezone.utc),
                is_self_transfer=True,
                headline=f"Position to {hub}, then fly to {req.destination}",
                detail=(
                    f"Cheap positioning flight {req.origin}→{hub} (economy), "
                    f"then {hub}→{req.destination} in {req.cabin_class.value}. "
                    f"Two separate bookings — allow 3+ hours at {hub}."
                ),
            ))
        return results

    async def _method_apd_avoidance(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 9: Route via non-UK departure to avoid UK Air Passenger Duty."""
        if not self._static.is_uk_airport(req.origin):
            return []
        connectors = self._static.get_apd_avoidance_hubs(req.origin)
        results = []
        for hub in connectors[:2]:
            train_pence = self._calc.ground_transport_cost(hub)
            main_list = await self._flight.search(
                hub, req.destination, req.outbound_date,
                cabin=req.cabin_class.value, passengers=req.passengers,
            )
            if not main_list:
                continue
            raw = main_list[0]
            cost = self._calc.calculate(CostInputs(
                base_fare_gbp_pence=raw.price_gbp_pence,
                taxes_gbp_pence=0,
                ground_transport_pence=train_pence,
            ))
            results.append(self._make_result(
                method=HackMethod.APD_AVOIDANCE,
                outbound=[self._raw_to_leg(raw, req.cabin_class)],
                cost=cost,
                duration=raw.duration_minutes,
                data_freshness=datetime.now(timezone.utc),
                headline=f"Avoid APD: depart from {hub} instead of UK",
                detail=(
                    f"UK APD can add £88-£176 per person. Taking Eurostar/train to "
                    f"{hub} and departing from there avoids this tax entirely."
                ),
            ))
        return results

    async def _method_oneworld_portal(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 10: Oneworld Explorer portal — fixed price by zone count."""
        # TODO: integrate flightplan / award chart lookup
        return []

    async def _method_avios_reward(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 11: BA Avios reward flight via ba_rewards scraper."""
        # TODO: integrate ba_rewards library
        return []

    async def _method_stopover(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 12: Free stopover programs (SIA, Ethiopian, etc.)."""
        # TODO: integrate stopover program data
        return []

    async def _method_layover_explore(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 13: Long layover as a free city visit."""
        # TODO: surface long-layover itineraries
        return []

    async def _method_crazy_mode(self, req: SearchRequest) -> list[ItineraryResult]:
        """Method 20: Pure lowest cost — any combination, any modality."""
        # Probe every hub and every secondary airport, take absolute cheapest
        all_results = await asyncio.gather(
            self._method_hub_arbitrage(req, phase=2),
            self._method_secondary_airports(req),
            self._method_positioning(req),
        )
        flat = [r for sublist in all_results for r in sublist]
        if not flat:
            return []
        flat.sort(key=lambda r: r.cost.total_gbp)
        # Mark top 3 as crazy mode
        for r in flat[:3]:
            r.method = HackMethod.CRAZY_MODE
        return flat[:3]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _gather(self, coros) -> list[ItineraryResult]:
        """Run all method coroutines concurrently, flatten, deduplicate, sort."""
        results_nested = await asyncio.gather(*coros, return_exceptions=True)
        flat: list[ItineraryResult] = []
        for item in results_nested:
            if isinstance(item, Exception):
                logger.error("hack_engine.method_error err=%s", item)
                continue
            flat.extend(item)

        # Deduplicate by (method, cheapest_leg fingerprint, total_gbp)
        seen: set[str] = set()
        unique: list[ItineraryResult] = []
        for r in flat:
            key = f"{r.method}:{r.cost.total_gbp}:{len(r.outbound_legs)}"
            if key not in seen:
                seen.add(key)
                unique.append(r)

        unique.sort(key=lambda r: r.cost.total_gbp)
        return unique

    def _cheapest_cash(self, results: list[ItineraryResult]) -> int | None:
        cash = [r for r in results if not r.is_award]
        if not cash:
            return None
        return min(r.cost.total_gbp for r in cash)

    def _annotate_savings(
        self, results: list[ItineraryResult], direct_price: int | None
    ) -> None:
        for r in results:
            if direct_price and not r.is_award:
                saving = direct_price - r.cost.total_gbp
                r.saving.vs_direct_saving_gbp = saving if saving > 0 else 0

    def _raw_to_leg(self, raw: RawFlightResult, cabin: CabinClass) -> FlightLeg:
        return FlightLeg(
            origin=raw.origin,
            destination=raw.destination,
            departure_at=raw.departure_at,
            arrival_at=raw.arrival_at,
            airline_code=raw.airline_code,
            airline_name=raw.airline_name,
            flight_number=raw.flight_number,
            cabin_class=cabin,
            duration_minutes=raw.duration_minutes,
            stops=raw.stops,
        )

    def _make_ground_leg(
        self, from_label: str, to_label: str, cost_pence: int
    ) -> GroundLeg | None:
        if cost_pence <= 0:
            return None
        return GroundLeg(
            origin_label=from_label,
            destination_label=to_label,
            transport_type="train",
            duration_minutes=60,
            cost_gbp=cost_pence,
        )

    def _make_result(
        self,
        method: HackMethod,
        outbound: list[FlightLeg],
        cost: CostBreakdown,
        duration: int,
        data_freshness: datetime,
        headline: str,
        detail: str,
        return_legs: list[FlightLeg] | None = None,
        ground_legs: list[GroundLeg] | None = None,
        is_self_transfer: bool = False,
        is_award: bool = False,
        award_program: str | None = None,
        deep_link: str | None = None,
    ) -> ItineraryResult:
        return ItineraryResult(
            result_id=str(uuid.uuid4()),
            method=method,
            outbound_legs=outbound,
            return_legs=return_legs or [],
            ground_legs=ground_legs or [],
            cost=cost,
            saving=SavingExplanation(headline=headline, detail=detail),
            total_duration_minutes=duration,
            is_self_transfer=is_self_transfer,
            data_freshness=data_freshness,
            deep_link=deep_link,
            is_award=is_award,
            award_program=award_program,
        )
