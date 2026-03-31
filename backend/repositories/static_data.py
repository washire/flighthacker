"""
Static data repository — reads from CSV seed files in data/.

All data is loaded once at startup and held in memory (data is small:
~150 airports, ~500 routes). No DB round-trips for lookups.

CSV files live in data/ relative to the project root.
"""
from __future__ import annotations

import csv
import logging
import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Resolve data/ directory relative to this file
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_csv(filename: str) -> list[dict[str, str]]:
    path = _DATA_DIR / filename
    if not path.exists():
        logger.warning("static_data.missing_file path=%s", path)
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


class StaticDataRepository:
    """
    In-memory store for all static lookup tables.
    Instantiate once per process — data loaded lazily on first access.
    """

    def __init__(self) -> None:
        self._airports: dict[str, dict] | None = None
        self._ground_transport: dict[str, int] | None = None
        self._surcharges: dict[str, int] | None = None
        self._fare_zones: dict[str, str] | None = None
        self._hubs: list[dict] | None = None
        self._uk_airports: set[str] | None = None
        self._apd_hubs: dict[str, list[str]] | None = None

    # ------------------------------------------------------------------
    # Airport lookups
    # ------------------------------------------------------------------

    def get_nearby_airports(self, iata: str, radius_km: float) -> list[str]:
        """Return IATA codes of airports within radius_km of iata."""
        airports = self._get_airports()
        anchor = airports.get(iata.upper())
        if anchor is None:
            return []
        result = []
        for code, data in airports.items():
            if code == iata.upper():
                continue
            dist = _haversine_km(
                float(anchor["lat"]), float(anchor["lon"]),
                float(data["lat"]), float(data["lon"]),
            )
            if dist <= radius_km:
                result.append((code, dist))
        result.sort(key=lambda x: x[1])
        return [c for c, _ in result]

    def get_major_hubs(self, origin: str, destination: str) -> list[str]:
        """
        Return globally ranked major hubs, excluding origin and destination.
        Used as cold-start hub list before scorer has data.
        """
        hubs = self._get_hubs()
        excluded = {origin.upper(), destination.upper()}
        return [h["iata"] for h in hubs if h["iata"] not in excluded]

    def get_major_departure_hubs(self, origin: str) -> list[str]:
        """Hubs reachable from origin that serve as positioning departure points."""
        airports = self._get_airports()
        anchor = airports.get(origin.upper())
        if anchor is None:
            return []
        # Return airports flagged as major hubs within 500 km
        return self.get_nearby_airports(origin, 500)[:5]

    def is_uk_airport(self, iata: str) -> bool:
        if self._uk_airports is None:
            airports = self._get_airports()
            self._uk_airports = {
                code for code, data in airports.items()
                if data.get("country_code", "").upper() == "GB"
            }
        return iata.upper() in self._uk_airports

    def get_apd_avoidance_hubs(self, uk_origin: str) -> list[str]:
        """
        Return nearby non-UK departure points reachable by train/bus
        (Eurostar to Paris CDG, Brussels, Amsterdam etc).
        """
        if self._apd_hubs is None:
            rows = _load_csv("apd_avoidance_hubs.csv")
            self._apd_hubs = {}
            for row in rows:
                uk = row["uk_airport"].upper()
                self._apd_hubs.setdefault(uk, []).append(row["alt_hub"].upper())
        return self._apd_hubs.get(uk_origin.upper(), [])

    # ------------------------------------------------------------------
    # Fare zones
    # ------------------------------------------------------------------

    def get_same_fare_zone_airports(self, destination: str) -> list[str]:
        """Return airports in the same BA pricing fare zone as destination."""
        zones = self._get_fare_zones()
        dest_zone = zones.get(destination.upper())
        if dest_zone is None:
            return []
        return [
            code for code, zone in zones.items()
            if zone == dest_zone and code != destination.upper()
        ]

    # ------------------------------------------------------------------
    # Cost lookups
    # ------------------------------------------------------------------

    def get_ground_transport_cost(self, airport_iata: str) -> int:
        """Return typical ground transport cost in GBP pence from CSV."""
        gt = self._get_ground_transport()
        return gt.get(airport_iata.upper(), 0)

    def get_surcharge_table(self) -> dict[str, int]:
        """Return surcharge lookup dict keyed by airline_code or airline_code:cabin."""
        return self._get_surcharges()

    # ------------------------------------------------------------------
    # Lazy loaders
    # ------------------------------------------------------------------

    def _get_airports(self) -> dict[str, dict]:
        if self._airports is None:
            rows = _load_csv("airports.csv")
            self._airports = {r["iata"].upper(): r for r in rows if r.get("iata")}
            logger.info("static_data.airports_loaded count=%d", len(self._airports))
        return self._airports

    def _get_hubs(self) -> list[dict]:
        if self._hubs is None:
            self._hubs = _load_csv("major_hubs.csv")
            logger.info("static_data.hubs_loaded count=%d", len(self._hubs))
        return self._hubs

    def _get_ground_transport(self) -> dict[str, int]:
        if self._ground_transport is None:
            rows = _load_csv("ground_transport.csv")
            self._ground_transport = {
                r["airport_iata"].upper(): int(r.get("cost_gbp_pence", 0))
                for r in rows
            }
        return self._ground_transport

    def _get_surcharges(self) -> dict[str, int]:
        if self._surcharges is None:
            rows = _load_csv("carrier_surcharges.csv")
            self._surcharges = {}
            for r in rows:
                key = r["airline_code"].upper()
                if r.get("cabin"):
                    key = f"{key}:{r['cabin']}"
                self._surcharges[key] = int(r.get("surcharge_gbp_pence", 0))
        return self._surcharges

    def _get_fare_zones(self) -> dict[str, str]:
        if self._fare_zones is None:
            rows = _load_csv("fare_zones.csv")
            self._fare_zones = {r["iata"].upper(): r["zone"] for r in rows}
        return self._fare_zones
