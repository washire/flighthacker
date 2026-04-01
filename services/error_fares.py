"""
Error fare scanner — fetches Secret Flying & Fly4Free RSS feeds.

Parses deal titles for mentions of the user's origin/destination city or
country. Returns matching deals as lightweight results so the hack engine
can surface them alongside normal search results.

No API key required — both sites publish public RSS.
Cached aggressively (1 hour) so we don't hammer the feed on every search.
"""
from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

# Public RSS feeds for error/mistake fares
_FEEDS = [
    "https://secretflying.com/feed/",
    "https://www.fly4free.com/feed/",
]

# Airport → city/country aliases used to match deal titles
_AIRPORT_HINTS: dict[str, list[str]] = {
    "LHR": ["london", "heathrow", "uk", "united kingdom", "england"],
    "LGW": ["london", "gatwick", "uk", "united kingdom", "england"],
    "STN": ["london", "stansted", "uk", "united kingdom", "england"],
    "MAN": ["manchester", "uk", "united kingdom", "england"],
    "EDI": ["edinburgh", "scotland", "uk"],
    "CDG": ["paris", "france"],
    "ORY": ["paris", "france"],
    "AMS": ["amsterdam", "netherlands", "holland"],
    "FRA": ["frankfurt", "germany"],
    "MAD": ["madrid", "spain"],
    "BCN": ["barcelona", "spain"],
    "FCO": ["rome", "italy"],
    "MXP": ["milan", "italy"],
    "NRT": ["tokyo", "japan", "narita"],
    "HND": ["tokyo", "japan", "haneda"],
    "JFK": ["new york", "usa", "united states"],
    "LAX": ["los angeles", "usa", "united states"],
    "DXB": ["dubai", "uae"],
    "SIN": ["singapore"],
    "BKK": ["bangkok", "thailand"],
    "SYD": ["sydney", "australia"],
    "YYZ": ["toronto", "canada"],
    "GRU": ["sao paulo", "brazil"],
    "JNB": ["johannesburg", "south africa"],
}

_CACHE_TTL = 3600  # 1 hour


class ErrorFareScanner:
    def __init__(self, redis) -> None:
        self._redis = redis

    async def find_deals(
        self,
        origin: str,
        destination: str,
    ) -> list[dict]:
        """
        Returns a list of matching error fare dicts, each with:
          title, price_hint_gbp (best-effort parse, may be None),
          url, published_at, source
        """
        cache_key = f"errorfares:{origin}:{destination}"
        cached = await self._redis.get(cache_key)
        if cached:
            return json.loads(cached)

        all_items = await self._fetch_all_feeds()
        matches = _filter_relevant(all_items, origin, destination)

        await self._redis.setex(cache_key, _CACHE_TTL, json.dumps(matches))
        return matches

    async def _fetch_all_feeds(self) -> list[dict]:
        items: list[dict] = []
        async with httpx.AsyncClient(timeout=8.0) as client:
            for url in _FEEDS:
                try:
                    resp = await client.get(url, headers={"User-Agent": "FlightHacker/1.0"})
                    if resp.status_code == 200:
                        items.extend(_parse_rss(resp.text, source=url))
                except Exception as exc:
                    logger.warning("error_fares.feed_error url=%s err=%s", url, exc)
        return items


def _parse_rss(xml_text: str, source: str) -> list[dict]:
    items = []
    try:
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub_date = (item.findtext("pubDate") or "").strip()
            description = (item.findtext("description") or "").strip()
            price = _extract_price(title + " " + description)
            items.append({
                "title": title,
                "url": link,
                "published_at": pub_date,
                "source": source,
                "price_hint_gbp": price,
                "description": description[:300],
            })
    except ET.ParseError as exc:
        logger.debug("error_fares.parse_error err=%s", exc)
    return items


def _extract_price(text: str) -> int | None:
    """Best-effort: extract first £NNN from text. Returns pence or None."""
    m = re.search(r"£\s*(\d[\d,]*)", text)
    if m:
        try:
            return int(m.group(1).replace(",", "")) * 100
        except ValueError:
            pass
    return None


def _filter_relevant(
    items: list[dict],
    origin: str,
    destination: str,
) -> list[dict]:
    """Keep items that mention the origin OR destination in the title."""
    origin_hints = set(_AIRPORT_HINTS.get(origin.upper(), [origin.lower()]))
    dest_hints = set(_AIRPORT_HINTS.get(destination.upper(), [destination.lower()]))
    all_hints = origin_hints | dest_hints

    results = []
    for item in items:
        text = (item["title"] + " " + item.get("description", "")).lower()
        if any(hint in text for hint in all_hints):
            results.append(item)
    return results[:10]
