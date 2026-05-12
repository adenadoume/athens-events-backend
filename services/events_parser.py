import os
import json
import uuid
from openai import OpenAI
from models.event import Event

_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

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
- ticket_source: string — one of: "viva", "ticketswap", "ticketmaster", "ra", "clubber", "door", "other"
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
        response = _client.chat.completions.create(
            model="deepseek-chat",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": PARSE_PROMPT.format(url=url, content=content[:12000]),
            }],
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except Exception as e:
        print(f"Parser error for {url}: {e}")
        return []


def parse_events_from_scraped(scraped_pages: list[dict], tavily_results: list[dict]) -> list[Event]:
    all_raw: list[dict] = []

    for page in scraped_pages:
        raw_events = _parse_content_sync(page["url"], page["markdown"])
        all_raw.extend(raw_events)

    scraped_urls = {p["url"] for p in scraped_pages}
    tavily_unseen = [r for r in tavily_results if r.get("url") and r["url"] not in scraped_urls]

    if tavily_unseen:
        combined = "\n\n---\n\n".join(
            f"Source: {r['url']}\nTitle: {r['title']}\n{r['content']}"
            for r in tavily_unseen[:10]
        )
        raw_events = _parse_content_sync("combined-search-results", combined)
        all_raw.extend(raw_events)

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
            print(f"Event model error: {e}")
            continue

    events.sort(key=lambda e: e.date)
    return events
