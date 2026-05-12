# Athens Events — AI Handoff (Quick Start)
> Give this file + `CLAUDE.md` + `app_architecture.md` to AI when resuming work on this project.
> This file: product spec + data sources. `CLAUDE.md`: what's built, roadmap, decisions. `app_architecture.md`: full stack boilerplate.

---

## What This App Does

Finds and displays **concerts, live music, DJ/electronic events, parties, and nightlife** happening in **Athens, Greece** — with photo cards, descriptions, dates, venues, and direct ticket booking links.

Data pipeline: **Tavily (search URLs) → Firecrawl (scrape pages) → Claude API (structure data) → FastAPI (serve JSON) → React (render cards)**

---

## Stack (Short Version)

- Frontend: React + Vite + TypeScript → **Vercel** (auto-deploy from GitHub)
- Backend: FastAPI (Python) → **Oracle VM `141.147.44.143`, port 8004**, PM2 process manager
- GitHub repos: `git@github.com:adenadoume/athens-events-frontend.git` / `athens-events-backend.git`
- See `app_architecture.md` for full patterns

## Oracle VM Access

```bash
# SSH (alias defined in ~/.ssh/config)
ssh oracle-softone

# Direct
ssh -i ~/.ssh/id_ed25519_ioagop ubuntu@141.147.44.143

# Health check
curl http://141.147.44.143:8004/health
```

---

## Event Data Model

```python
class Event(BaseModel):
    id: str
    title: str
    date: str                   # ISO 8601: "2026-05-16T22:00:00"
    venue: str
    location: str               # Athens neighbourhood (Gazi, Psirri…)
    category: str               # "concert" | "dj" | "party" | "electronic"
    description: str            # 2-3 sentences
    image_url: str
    ticket_url: str             # Direct booking link
    ticket_source: str          # "viva" | "ticketswap" | "ticketmaster" | "ra" | "door"
    price: str | None           # "€15" | "Free" | None
    artists: list[str]          # ["DJ Name", "Artist Name"]
```

---

## API Endpoint

```
GET /api/events?category=all&date_range=this_week
```

Valid categories: `all`, `concert`, `dj`, `party`, `electronic`
Valid date ranges: `today`, `this_weekend`, `this_week`, `this_month`

---

## Key Data Sources

| Source | URL | Type |
|---|---|---|
| Viva.gr | viva.gr/tickets/music | Main Greek ticketing |
| Resident Advisor | residentadvisor.net/events/gr/athens | Electronic/DJ |
| TicketSwap | ticketswap.com | Secondary market |
| Ticketmaster GR | ticketmaster.gr | Large concerts |
| More.com.gr | more.com.gr | Greek events |
| Club sites | Fuzz Live, Gagarin 205, Six D.O.G.S, Venue Athens | Direct |

---

## UI Design Brief

- **Dark theme** — background `#08080f`, cards `#131320`
- **Tailwind CSS** — no custom CSS files, no icon libraries
- **No icons** — clean text-only UI throughout
- **Neon accents** — violet-600 (primary), cyan-500 (secondary)
- Category badges: violet=concert, cyan=DJ, pink=party, emerald=electronic
- Cards: hero photo (16:9 aspect), category badge, title, date+venue, artists, description (3-line clamp), "Get Tickets →" button
- Filter bar: pill buttons for category + date range, plain Refresh button
- Hover: card lifts `-translate-y-1` + purple glow `shadow-card-hover`
- Loading: shimmer skeleton cards (`bg-shimmer` Tailwind utility)
- **Mock data fallback**: 6 sample events shown when backend unreachable + amber warning banner

---

## Environment Variables Needed

### Backend `.env`
```
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

### Frontend `.env` (local)
```
VITE_API_URL=http://localhost:8000/api
```

---

## Current Status

See `CLAUDE.md` for full roadmap and what has been built vs. what is pending.

**Short version:** Phase 1 (full app code) is complete. Phase 2 (deploy to Oracle VM + Vercel) is next.
