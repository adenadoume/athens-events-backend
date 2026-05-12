# Athens Events App — AI Handoff Document

> Give this file to your AI assistant (Cursor, Copilot, Claude Code) as the starting context for building the app.

---

## 🎯 Project Goal

Build a full-stack web app that finds and displays **concerts, live music, DJ/electronic events, parties, and nightlife** happening in **Athens, Greece** — with photo cards, descriptions, dates, venues, and direct ticket booking links (including TicketSwap).

The app fetches real-time event data by combining **AI-powered web search** (Tavily), **deep web scraping** (Firecrawl), and optionally **full browser automation** (Playwright MCP) — all orchestrated by a FastAPI backend.

---

## 🏗️ Stack & Infrastructure

This app follows the same pattern as my existing projects:

| Layer | Technology |
|---|---|
| Frontend | React (Vite) |
| Backend | FastAPI (Python) |
| Hosting — Frontend | Vercel (auto-deploy from GitHub) |
| Hosting — Backend | Oracle VM (Ubuntu, existing server) |
| Reverse Proxy | Nginx on Oracle VM |
| Process Manager | PM2 or systemd on Oracle VM |
| Repo | GitHub |

> ⚠️ Backend runs on an **existing Oracle VM** — do not suggest Docker, Railway, Render, or other hosting. FastAPI goes on the Oracle VM as it does for my other apps.

---

## 🛠️ Web Intelligence Tools to Integrate

### 1. Tavily — AI Web Search
- **Role:** Fast search to discover event listings across the web
- **What it does:** Returns ranked URLs + summaries from event sites (Viva.gr, Resident Advisor, Ticketmaster GR, TicketSwap, Facebook Events, club websites)
- **MCP:** `tavily-mcp` — connect in Claude Code or Cursor
- **API docs:** https://docs.tavily.com
- **Setup:**
  ```bash
  pip install tavily-python
  ```
  ```python
  from tavily import TavilyClient
  client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
  results = client.search("concerts Athens this weekend", search_depth="advanced")
  ```

### 2. Firecrawl — Deep Page Scraping
- **Role:** Fully render and extract structured data from JS-heavy event pages (TicketSwap, RA, club sites)
- **What it does:** Turns any URL into clean markdown/JSON that Claude can parse; handles JavaScript rendering, anti-bot, and dynamic content
- **MCP:** `firecrawl-mcp` — connect in Claude Code or Cursor
- **API docs:** https://docs.firecrawl.dev
- **Setup:**
  ```bash
  pip install firecrawl-py
  ```
  ```python
  from firecrawl import FirecrawlApp
  app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
  result = app.scrape_url("https://www.ticketswap.com/...", formats=["markdown", "json"])
  ```
- **Free tier:** Available at https://firecrawl.dev (get API key first)

### 3. Playwright MCP — Full Browser Automation (Optional / Phase 2)
- **Role:** For sites that require login, dropdown interaction, or complex navigation (Facebook Events, some club booking portals)
- **What it does:** Gives AI full browser control — click, scroll, fill forms, extract dynamic content
- **Built by:** Microsoft (official MCP server)
- **MCP:** `@playwright/mcp` — install via npm
- **Setup:**
  ```bash
  npm install -g @playwright/mcp
  playwright install chromium
  ```
- **Use when:** Firecrawl can't reach content (login walls, interactive calendars, infinite scroll)
- **Phase 2** — build the app without it first, add when needed

---

## 📦 Backend Architecture (FastAPI on Oracle VM)

### Folder Structure
```
athens-events-backend/
├── main.py                  # FastAPI app entry point
├── routers/
│   └── events.py            # /api/events endpoint
├── services/
│   ├── tavily_service.py    # Search for event URLs
│   ├── firecrawl_service.py # Scrape full event pages
│   └── events_parser.py     # Claude API call to structure data
├── models/
│   └── event.py             # Pydantic Event model
├── .env                     # API keys (never commit)
├── requirements.txt
└── README.md
```

### Event Data Model
```python
class Event(BaseModel):
    id: str
    title: str
    date: str                  # ISO format
    venue: str
    location: str              # Athens neighbourhood if known
    category: str              # "concert" | "dj" | "party" | "electronic"
    description: str
    image_url: str             # Photo URL
    ticket_url: str            # Direct booking link
    ticket_source: str         # "viva" | "ticketswap" | "ticketmaster" | "door"
    price: str | None          # e.g. "€15" or "Free"
    artists: list[str]
```

### Main Endpoint
```
GET /api/events?category=all&date=this_week
```

### Data Flow
```
1. Tavily searches: "concerts parties DJ events Athens [this week]"
2. Returns top 15-20 URLs from Viva.gr, RA, TicketSwap, club sites
3. Firecrawl scrapes each URL → clean markdown
4. Claude API call structures the markdown into Event JSON
5. FastAPI returns array of Event objects
6. React frontend renders photo cards
```

### Key Sources to Target
- `viva.gr/tickets/music` — main Greek ticketing platform
- `residentadvisor.net/events/gr/athens` — electronic/DJ events
- `ticketswap.com` — secondary market + listings
- `ticketmaster.gr` — large concerts
- `more.com.gr` — Greek events
- Club-specific sites (Fuzz Live, Gagarin 205, Six D.O.G.S, Venue Athens, etc.)

---

## 🎨 Frontend Architecture (React + Vite on Vercel)

### Folder Structure
```
athens-events-frontend/
├── src/
│   ├── components/
│   │   ├── EventCard.jsx        # Photo card component
│   │   ├── EventGrid.jsx        # Masonry/grid layout
│   │   ├── FilterBar.jsx        # Category + date filters
│   │   ├── SearchBar.jsx
│   │   └── LoadingSkeleton.jsx
│   ├── pages/
│   │   └── Home.jsx
│   ├── hooks/
│   │   └── useEvents.js         # Data fetching hook
│   ├── utils/
│   │   └── api.js               # Backend API calls
│   └── App.jsx
├── .env                         # VITE_API_URL=https://your-oracle-vm-ip/api
├── vercel.json
└── package.json
```

### EventCard Design Requirements
Each card must show:
- **Hero photo** (full-width, 16:9 or 4:3 crop)
- **Category badge** (pill: "DJ Set", "Live", "Party", "Electronic")
- **Event title** (bold, large)
- **Date + time** with calendar icon
- **Venue name** with location pin icon
- **Artist names** (if applicable)
- **Price** (or "Free Entry")
- **"Get Tickets" button** → opens `ticket_url` in new tab
- **Source badge** (Viva / TicketSwap / RA / etc.)

Design direction: **dark theme, neon accents (purple/cyan), editorial magazine layout** — evokes nightlife energy. Cards should have subtle hover lift animation and glow effect.

### Filter Bar
- Category: All / Concerts / DJ & Electronic / Parties
- Date: Today / This Weekend / This Week / This Month
- Auto-refresh button

---

## 🔑 Environment Variables

### Backend `.env`
```
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

### Frontend `.env`
```
VITE_API_URL=https://your-oracle-vm-domain-or-ip/api
```

---

## 🚀 Deployment

### Backend (Oracle VM)
```bash
# On Oracle VM
git clone https://github.com/your-username/athens-events-backend
cd athens-events-backend
pip install -r requirements.txt
# Add .env with API keys
uvicorn main:app --host 0.0.0.0 --port 8000
# Or with PM2:
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name athens-events
```

Nginx config (same pattern as existing apps):
```nginx
location /api/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Frontend (Vercel)
```bash
# Vercel picks up from GitHub automatically
# Set VITE_API_URL in Vercel environment variables dashboard
```

---

## 📋 Build Order

1. **Backend first:**
   - Set up FastAPI skeleton with `/api/events` returning mock data
   - Add Tavily search service
   - Add Firecrawl scraper service
   - Add Claude API parser to structure scraped content into Event model
   - Test locally, deploy to Oracle VM

2. **Frontend second:**
   - Scaffold React + Vite
   - Build EventCard component with dark/neon design
   - Build EventGrid with filter bar
   - Connect to backend API
   - Deploy to Vercel via GitHub

3. **Phase 2 (optional):**
   - Add Playwright for login-gated sources (Facebook Events)
   - Add caching layer (Redis or simple file cache) to avoid re-scraping
   - Add a cron job to refresh events every few hours

---

## 📎 Also Generate

After implementing, please also create `app_architecture.md` (see separate instructions below) documenting every architectural decision made in this project so it can serve as a template for future apps.

---

## 🗂️ Related File

See `app_architecture.md` — generated after build — for reusable architecture patterns, decisions, and a template for future apps on this same stack.
