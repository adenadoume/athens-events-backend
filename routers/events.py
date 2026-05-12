from fastapi import APIRouter, Query
from models.event import EventResponse
from services.events_service import get_events

router = APIRouter()

VALID_CATEGORIES = {"all", "concert", "dj", "party", "electronic"}
VALID_DATE_RANGES = {"today", "this_weekend", "this_week", "this_month"}


@router.get("/events", response_model=EventResponse)
async def list_events(
    category: str = Query(default="all", description="Filter by category"),
    date_range: str = Query(default="this_week", description="Filter by date range"),
):
    if category not in VALID_CATEGORIES:
        category = "all"
    if date_range not in VALID_DATE_RANGES:
        date_range = "this_week"

    return await get_events(category=category, date_range=date_range)
