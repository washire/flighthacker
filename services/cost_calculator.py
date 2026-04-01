"""
True all-in cost calculator.

Takes raw flight prices and adds:
  - Baggage fees
  - Carrier surcharges (fuel surcharges on award tickets)
  - UK Air Passenger Duty (APD) where applicable
  - Ground transport costs (taxi/train to/from airport)
  - Positioning flight costs (if routing via a different departure airport)
  - Avios redemption value (pence-per-point calculation)

All monetary values are GBP pence (int).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from models.search import CostBreakdown, FlightLeg, GroundLeg
from repositories.static_data import StaticDataRepository

logger = logging.getLogger(__name__)

# UK APD bands (2024/25 rates, pence)
# Reduced rate = economy; standard rate = premium/business/first
_APD_BANDS: dict[str, dict[str, int]] = {
    "A": {"reduced": 1388, "standard": 2778},   # 0–2000 miles
    "B": {"reduced": 8800, "standard": 17600},  # 2001+ miles
}


@dataclass
class CostInputs:
    """All the raw numbers needed to compute true cost."""
    base_fare_gbp_pence: int
    taxes_gbp_pence: int
    carrier_surcharge_pence: int = 0
    checked_bag_pence: int = 0
    ground_transport_pence: int = 0
    positioning_flight_pence: int = 0
    # Avios
    avios_required: int | None = None
    cash_copay_pence: int | None = None
    pence_per_point: float | None = None


class CostCalculator:
    def __init__(self, static_repo: StaticDataRepository) -> None:
        self._static = static_repo

    def calculate(self, inputs: CostInputs) -> CostBreakdown:
        """Assemble CostBreakdown from raw inputs."""
        total = (
            inputs.base_fare_gbp_pence
            + inputs.taxes_gbp_pence
            + inputs.carrier_surcharge_pence
            + inputs.checked_bag_pence
            + inputs.ground_transport_pence
            + inputs.positioning_flight_pence
        )
        return CostBreakdown(
            base_fare_gbp=inputs.base_fare_gbp_pence,
            taxes_gbp=inputs.taxes_gbp_pence,
            carrier_surcharges_gbp=inputs.carrier_surcharge_pence,
            bags_gbp=inputs.checked_bag_pence,
            ground_transport_gbp=inputs.ground_transport_pence,
            positioning_flight_gbp=inputs.positioning_flight_pence,
            total_gbp=total,
            avios_required=inputs.avios_required,
            cash_copay_gbp=inputs.cash_copay_pence,
            pence_per_point=inputs.pence_per_point,
        )

    def get_apd(self, origin_iata: str, cabin: str, distance_miles: int) -> int:
        """
        Return UK APD in pence for a departure from a UK airport.
        Returns 0 if origin is not a UK airport.
        """
        if not self._static.is_uk_airport(origin_iata):
            return 0

        band = "A" if distance_miles <= 2000 else "B"
        rate_type = "reduced" if cabin == "economy" else "standard"
        apd = _APD_BANDS[band][rate_type]
        logger.debug("apd origin=%s band=%s rate=%s pence=%d", origin_iata, band, rate_type, apd)
        return apd

    def get_carrier_surcharge(self, airline_code: str, cabin: str, is_award: bool) -> int:
        """
        Return carrier surcharge in pence.
        Award tickets on BA/IB/AA carry heavy fuel surcharges (YQ).
        Cash tickets rarely have separable surcharges.
        """
        if not is_award:
            return 0
        surcharges = self._static.get_surcharge_table()
        key = f"{airline_code}:{cabin}"
        return surcharges.get(key, surcharges.get(airline_code, 0))

    def compute_ppp(self, avios: int, cash_copay_pence: int, cash_equivalent_pence: int) -> float:
        """
        Calculate pence-per-point for an Avios redemption.
        ppp = (cash_value - copay) / avios
        """
        if avios <= 0:
            return 0.0
        net_saving = cash_equivalent_pence - cash_copay_pence
        return round(net_saving / avios, 4)

    def ground_transport_cost(self, airport_iata: str) -> int:
        """Return typical ground transport cost in pence from static CSV."""
        return self._static.get_ground_transport_cost(airport_iata)
