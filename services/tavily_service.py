import os
from tavily import TavilyClient
from datetime import datetime

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

DATE_RANGE_QUERIES = {
    "today": "today",
    "this_weekend": "this weekend",
    "this_week": "this week",
    "this_month": "this month",
}

CATEGORY_QUERIES = {
    "all": "concerts live music DJ electronic parties nightlife",
    "concert": "live concerts music shows",
    "dj": "DJ set electronic music club",
    "party": "parties nightlife events",
    "electronic": "electronic music techno house events",
}


async def search_event_urls(category: str = "all", date_range: str = "this_week") -> list[dict]:
    """
    Use Tavily to discover event URLs from Athens event sources.
    Returns list of {url, title, content, score, image_url}.
    """
    date_str = DATE_RANGE_QUERIES.get(date_range, "this week")
    cat_str = CATEGORY_QUERIES.get(category, CATEGORY_QUERIES["all"])

    queries = [
        f"{cat_str} Athens Greece {date_str}",
        f"Athens events {date_str} site:viva.gr",
        f"Athens events {date_str} site:residentadvisor.net",
        f"Athens events {date_str} site:clubber.gr",
        f"Athens Greece nightlife {date_str} tickets",
    ]

    all_results: list[dict] = []
    seen_urls: set[str] = set()

    for query in queries:
        try:
            response = client.search(
                query=query,
                search_depth="advanced",
                max_results=8,
                include_images=True,
                include_answer=False,
            )
            for r in response.get("results", []):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append({
                        "url": r["url"],
                        "title": r.get("title", ""),
                        "content": r.get("content", ""),
                        "score": r.get("score", 0),
                    })
            # Collect images separately
            for img in response.get("images", []):
                all_results.append({"image_url": img, "url": "", "title": "", "content": "", "score": 0})
        except Exception as e:
            print(f"Tavily search error for query '{query}': {e}")
            continue

    # Sort by score, filter out image-only entries, return top 20
    url_results = [r for r in all_results if r.get("url")]
    url_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return url_results[:20]
