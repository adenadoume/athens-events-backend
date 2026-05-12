import os
import json
import uuid
import anthropic
from models.event import Event

_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

PARSE_PROMPT = """You are an event data extractor. Extract ALL events from the provided page content.
Return a JSON array of event objects. Each object must have these fields:

- title: string (event name)
- date: string (ISO 8601 format, e.g. "2026-05-16T22:00:00". If only date known, use "2026-05-16T00:00:00")
- venue: string (venue/club name)
- location: string (Athens neighbourhood: Gazi, Psirri, Kolonaki, Exarchia, Piraeus, or "Athens" if unknown)
- category: string — one of: "concert", "dj", "party", "electronic"
- description: string (2-3 sentence summary of the event)
- image_url: string (full URL to event image, or "" if not found)
- ticket_url: string (direct booking link, or the source URL if not found)
- ticket_source: string — one of: "viva", "ticketswap", "ticketmaster", "ra", "door", "other"
- price: string or null (e.g. "€15", "Free", or null if unknown)
- artists: array of strings (performing artists/DJs, empty array if none)

RULES:
- Only include events in Athens, Greece
- Only include future events (after May 2026)
- If multiple events are on the page, extract ALL of them
- Return ONLY the JSON array, no explanation, no markdown fences
- If no events found, return []

Page source URL: {url}
Page content:
{content}"""


def _parse_content_sync(url: str, content: str) -> list[dict]:
    try:
        message = _client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": PARSE_PROMPT.format(url=url, content=content[:12000]),
            }]
        )
        raw = message.content[0].text.strip()
        # Strip markdown fences if model added them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        print(f"Parser error for {url}: {e}")
        return []


def parse_events_from_scraped(scraped_pages: list[dict], tavily_results: list[dict]) -> list[Event]:
    """
    Parse events from:
    1. Firecrawl-scraped markdown pages (rich content)
    2. Tavily search snippets (fallback for non-scraped pages)
    Returns deduplicated list of Event objects.
    """
    all_raw: list[dict] = []

    # Parse firecrawl pages
    for page in scraped_pages:
        raw_events = _parse_content_sync(page["url"], page["markdown"])
        all_raw.extend(raw_events)

    # Parse Tavily snippets for URLs not already scraped
    scraped_urls = {p["url"] for p in scraped_pages}
    tavily_unseen = [r for r in tavily_results if r.get("url") and r["url"] not in scraped_urls]

    if tavily_unseen:
        # Combine all snippets into one batch for efficiency
        combined = "\n\n---\n\n".join(
            f"Source: {r['url']}\nTitle: {r['title']}\n{r['content']}"
            for r in tavily_unseen[:10]
        )
        raw_events = _parse_content_sync("combined-search-results", combined)
        all_raw.extend(raw_events)

    # Deduplicate by title+date
    seen: set[str] = set()
    events: list[Event] = []
    for raw in all_raw:
        key = f"{raw.get('title', '').lower().strip()}|{raw.get('date', '')[:10]}"
        if key in seen or not raw.get("title"):
            continue
        seen.add(key)
        try:
            events.append(Event(
                id=str(uuid.uuid4())[:8],
                title=raw.get("title", ""),
                date=raw.get("date", ""),
                venue=raw.get("venue", "Unknown Venue"),
                location=raw.get("location", "Athens"),
                category=raw.get("category", "concert"),
                description=raw.get("description", ""),
                image_url=raw.get("image_url", ""),
                ticket_url=raw.get("ticket_url", ""),
                ticket_source=raw.get("ticket_source", "other"),
                price=raw.get("price"),
                artists=raw.get("artists", []),
            ))
        except Exception as e:
            print(f"Event model error: {e} — raw: {raw}")
            continue

    # Sort by date ascending
    events.sort(key=lambda e: e.date)
    return events
