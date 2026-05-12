from pydantic import BaseModel
from typing import Optional


class Event(BaseModel):
    id: str
    title: str
    date: str                   # ISO format: "2026-05-16T22:00:00"
    venue: str
    location: str               # Athens neighbourhood (Gazi, Psirri, etc.)
    category: str               # "concert" | "dj" | "party" | "electronic"
    description: str
    image_url: str
    ticket_url: str
    ticket_source: str          # "viva" | "ticketswap" | "ticketmaster" | "ra" | "door"
    price: Optional[str] = None # "€15" | "Free" | None
    artists: list[str] = []


class EventResponse(BaseModel):
    events: list[Event]
    total: int
    fetched_at: str
    source_count: int           # how many sources were scraped
