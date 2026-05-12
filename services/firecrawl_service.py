import os
from firecrawl import FirecrawlApp
import asyncio
from concurrent.futures import ThreadPoolExecutor

_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
_executor = ThreadPoolExecutor(max_workers=5)

# Sites worth deep-scraping vs just using Tavily snippets
DEEP_SCRAPE_DOMAINS = [
    "viva.gr",
    "residentadvisor.net",
    "ticketswap.com",
    "ticketmaster.gr",
    "more.com.gr",
]


def _should_deep_scrape(url: str) -> bool:
    return any(domain in url for domain in DEEP_SCRAPE_DOMAINS)


def _scrape_url_sync(url: str) -> dict | None:
    try:
        result = _app.scrape_url(
            url=url,
            formats=["markdown"],
            actions=[{"type": "wait", "milliseconds": 2000}],
        )
        return {
            "url": url,
            "markdown": result.get("markdown", ""),
            "metadata": result.get("metadata", {}),
        }
    except Exception as e:
        print(f"Firecrawl error for {url}: {e}")
        return None


async def scrape_event_pages(urls: list[str]) -> list[dict]:
    """
    Scrape each URL with Firecrawl. Only deep-scrape priority domains;
    skip others (Tavily content snippet is sufficient for generic pages).
    Returns list of {url, markdown, metadata}.
    """
    priority = [u for u in urls if _should_deep_scrape(u)]
    # Cap at 10 pages to stay within free-tier credits
    to_scrape = priority[:10]

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_executor, _scrape_url_sync, url)
        for url in to_scrape
    ]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r and r.get("markdown")]
