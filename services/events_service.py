import asyncio
from datetime import datetime
from models.event import Event, EventResponse
from services.tavily_service import search_event_urls
from services.firecrawl_service import scrape_event_pages
from services.events_parser import parse_events_from_scraped

# Simple in-memory cache: {cache_key: (EventResponse, timestamp)}
_cache: dict[str, tuple[EventResponse, datetime]] = {}
CACHE_TTL_MINUTES = 60


def _cache_key(category: str, date_range: str) -> str:
    return f"{category}|{date_range}"


def _is_cache_valid(timestamp: datetime) -> bool:
    delta = (datetime.utcnow() - timestamp).total_seconds()
    return delta < CACHE_TTL_MINUTES * 60


async def get_events(category: str = "all", date_range: str = "this_week") -> EventResponse:
    key = _cache_key(category, date_range)

    if key in _cache:
        cached_response, cached_at = _cache[key]
        if _is_cache_valid(cached_at):
            return cached_response

    # 1. Tavily search
    tavily_results = await search_event_urls(category=category, date_range=date_range)

    # 2. Firecrawl deep scrape of priority domains
    urls = [r["url"] for r in tavily_results if r.get("url")]
    scraped_pages = await scrape_event_pages(urls)

    # 3. Parse everything into Event objects via Claude
    events = parse_events_from_scraped(scraped_pages, tavily_results)

    response = EventResponse(
        events=events,
        total=len(events),
        fetched_at=datetime.utcnow().isoformat(),
        source_count=len(scraped_pages),
    )

    _cache[key] = (response, datetime.utcnow())
    return response
