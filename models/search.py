"""
Pydantic models for flight search requests and responses.
All prices are in GBP pence (int) to avoid floating-point drift.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CabinClass(str, Enum):
    ECONOMY = "economy"
    PREMIUM_ECONOMY = "premium_economy"
    BUSINESS = "business"
    FIRST = "first"


class HackMethod(str, Enum):
    """Every distinct hacking method the engine can produce."""
    DIRECT_CHEAPEST = "direct_cheapest"
    SECONDARY_AIRPORT = "secondary_airport"
    HUB_ARBITRAGE = "hub_arbitrage"
    OPEN_JAW = "open_jaw"
    FARE_ZONE_OPEN_JAW = "fare_zone_open_jaw"
    POSITIONING_FLIGHT = "positioning_flight"
    MIXED_CABIN = "mixed_cabin"
    ONEWORLD_PORTAL = "oneworld_portal"
    AVIOS_REWARD = "avios_reward"
    AVIOS_PART_PAY = "avios_part_pay"
    FUEL_SURCHARGE_ARBITRAGE = "fuel_surcharge_arbitrage"
    STOPOVER_PROGRAM = "stopover_program"
    ERROR_FARE = "error_fare"
    APD_AVOIDANCE = "apd_avoidance"
    NEARBY_ORIGIN = "nearby_origin"
    NEARBY_DESTINATION = "nearby_destination"
    SPLIT_TICKET = "split_ticket"
    POSITIONING_PLUS_MAIN = "positioning_plus_main"
    CRAZY_MODE = "crazy_mode"
    LAYOVER_EXPLORE = "layover_explore"
    DATE_OPTIMISATION = "date_optimisation"


class AlertTriggerType(str, Enum):
    TARGET_PRICE = "target_price"
    PERCENTAGE_DROP = "percentage_drop"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class FlightLeg(BaseModel):
    """A single flight segment within an itinerary."""
    origin: str = Field(..., min_length=3, max_length=3, description="IATA airport code")
    destination: str = Field(..., min_length=3, max_length=3)
    departure_at: datetime
    arrival_at: datetime
    airline_code: str = Field(..., min_length=2, max_length=3)
    airline_name: str
    flight_number: str
    cabin_class: CabinClass
    duration_minutes: int = Field(..., gt=0)
    stops: int = Field(0, ge=0)
    # Transfer info
    self_transfer: bool = False
    layover_minutes: int | None = None
    # Baggage
    carry_on_included: bool = True
    checked_bag_included: bool = False
    checked_bag_fee_gbp: int = 0  # pence
    # Points earning
    avios_earn: int | None = None

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def uppercase_iata(cls, v: str) -> str:
        return v.upper().strip()


class GroundLeg(BaseModel):
    """A ground transport segment (train, bus, taxi) within the itinerary."""
    origin_label: str  # e.g. "London Gatwick" or "Paris CDG"
    destination_label: str
    transport_type: Literal["train", "bus", "taxi", "metro", "walk"]
    duration_minutes: int = Field(..., gt=0)
    cost_gbp: int = 0  # pence; 0 = free/walking


class CostBreakdown(BaseModel):
    """Itemised true cost in GBP pence."""
    base_fare_gbp: int
    taxes_gbp: int
    carrier_surcharges_gbp: int = 0
    bags_gbp: int = 0
    ground_transport_gbp: int = 0
    positioning_flight_gbp: int = 0
    total_gbp: int

    # Points alternative
    avios_required: int | None = None
    cash_copay_gbp: int | None = None  # cash needed on top of Avios
    pence_per_point: float | None = None  # how good this redemption is

    def model_post_init(self, __context: object) -> None:
        # Sanity-check total matches sum of components
        computed = (
            self.base_fare_gbp
            + self.taxes_gbp
            + self.carrier_surcharges_gbp
            + self.bags_gbp
            + self.ground_transport_gbp
            + self.positioning_flight_gbp
        )
        if self.total_gbp != computed:
            self.total_gbp = computed


class SavingExplanation(BaseModel):
    """Human-readable explanation of why this result is cheap."""
    headline: str  # e.g. "Fly via Madrid hub — saves £142 vs direct"
    detail: str    # longer explanation shown on card expand
    vs_direct_saving_gbp: int | None = None  # pence saved vs naive direct


# ---------------------------------------------------------------------------
# Core result model
# ---------------------------------------------------------------------------


class ItineraryResult(BaseModel):
    """One complete travel itinerary produced by a hack method."""
    result_id: str  # UUID assigned by engine
    method: HackMethod
    outbound_legs: list[FlightLeg]
    return_legs: list[FlightLeg] = Field(default_factory=list)
    ground_legs: list[GroundLeg] = Field(default_factory=list)
    cost: CostBreakdown
    saving: SavingExplanation
    total_duration_minutes: int
    # Metadata
    is_self_transfer: bool = False
    requires_visa_check: bool = False
    data_freshness: datetime  # when prices were fetched
    deep_link: str | None = None  # booking URL if available
    # Awards
    is_award: bool = False
    award_program: str | None = None  # e.g. "British Airways Executive Club"


# ---------------------------------------------------------------------------
# Request / Response
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    # Primary airport codes (required; used as display label and fallback)
    origin: str = Field(..., min_length=3, max_length=3)
    destination: str = Field(..., min_length=3, max_length=3)
    outbound_date: date
    return_date: date | None = None
    passengers: int = Field(1, ge=1, le=9)
    cabin_class: CabinClass = CabinClass.ECONOMY

    # City-mode: if set, the engine searches ALL combinations of these airports.
    # e.g. origin_airports=["LHR","LGW","STN","LTN","LCY"]
    #       destination_airports=["NRT","HND"]
    # surfaces the cheapest pair across all 10 combos.
    origin_airports: list[str] | None = None
    destination_airports: list[str] | None = None

    # Display labels for city-mode (e.g. "London", "Tokyo")
    origin_city: str | None = None
    destination_city: str | None = None

    # Optional Avios context
    avios_balance: int | None = Field(None, ge=0)
    pence_per_point: float | None = Field(None, gt=0)
    # Feature overrides (None = use server feature flag)
    include_awards: bool | None = None
    crazy_mode: bool = False

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def uppercase_iata(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("origin_airports", "destination_airports", mode="before")
    @classmethod
    def uppercase_iata_list(cls, v):
        if v is None:
            return v
        return [x.upper().strip() for x in v]

    @field_validator("return_date", mode="after")
    @classmethod
    def return_after_outbound(cls, v: date | None, info) -> date | None:
        if v and info.data.get("outbound_date") and v < info.data["outbound_date"]:
            raise ValueError("return_date must be on or after outbound_date")
        return v

    @property
    def all_origins(self) -> list[str]:
        """All origin airports to search (city-mode or single)."""
        return self.origin_airports or [self.origin]

    @property
    def all_destinations(self) -> list[str]:
        """All destination airports to search (city-mode or single)."""
        return self.destination_airports or [self.destination]


class SearchPhase(str, Enum):
    PHASE_1 = "phase_1"   # fast results ~3-5 s
    PHASE_2 = "phase_2"   # deep results ~15-30 s
    COMPLETE = "complete"


class SearchResponse(BaseModel):
    search_id: str
    request: SearchRequest
    results: list[ItineraryResult]
    phase: SearchPhase
    total_results: int
    cheapest_gbp: int | None = None   # pence, for quick display
    generated_at: datetime
    cached: bool = False
    # Direct baseline for savings comparison
    direct_price_gbp: int | None = None
