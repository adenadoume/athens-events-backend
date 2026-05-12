# Athens Events — CLAUDE.md
> This file is the **living roadmap** for the Athens Events app.
> Give it to AI (Cursor, Claude Code) at the start of every new session.
> Update it with every planning decision, implementation choice, and status change.

---

## Project Identity

| Field | Value |
|---|---|
| Project | Athens Events |
| Goal | Show concerts, DJ sets, parties and nightlife in Athens, Greece — with real-time data, photo cards, ticket links |
| Frontend | React + Vite + TypeScript — deploys to Vercel |
| Backend | FastAPI (Python) — runs on Oracle VM, port **8004** |
| Stack ref | `app_architecture.md` (full patterns, boilerplate, deployment) |
| Handoff doc | `handoff.md` (original product spec) |

---

## Repositories

```
git@github.com:adenadoume/athens-events-frontend.git   (React, Vercel)
git@github.com:adenadoume/athens-events-backend.git    (FastAPI, Oracle VM)
```

> Use SSH remotes (not HTTPS) — credentials configured via SSH key on this machine.

Local paths:
```
/Users/nucintosh/PYTHON/athens_events/frontend/
/Users/nucintosh/PYTHON/athens_events/backend/
```

---

## Architecture Decisions (Why We Did What We Did)

### Frontend
- **TypeScript** — consistent with all other apps in the stack (softone-live, pool-maintenance-app etc.)
- **No Ant Design** — this is a consumer-facing nightlife app, not an internal dashboard
- **No icons** — clean text-only UI, no lucide-react or any icon library
- **No React Router** — single-page, no routing needed in Phase 1
- **Tailwind CSS** — switched from custom CSS to Tailwind (consistent with containers-claude and other apps in stack). Dark nightlife theme via Tailwind utilities + custom colors in `tailwind.config.js` (violet-600 primary, cyan-500 secondary)
- **Mock data fallback** — 6 sample events shown when backend is unreachable, with amber banner warning. UI is always usable even before backend is deployed.

### Backend
- **FastAPI** — async, typed, auto-generates OpenAPI docs at `/docs`
- **Tavily → Firecrawl → Claude pipeline** — 3-stage: discover URLs → scrape pages → parse into structured JSON
- **In-memory cache (60 min TTL)** — avoids re-scraping on every browser refresh; no Redis needed for Phase 1
- **Only deep-scrape priority domains** — viva.gr, RA, ticketswap.com, ticketmaster.gr. Tavily snippets used for everything else to save Firecrawl credits
- **Claude `claude-sonnet-4-5`** for parsing — structured extraction from raw markdown

### Data Flow
```
1. GET /api/events?category=all&date_range=this_week
2. Tavily searches 4 queries → top 20 URLs
3. Firecrawl deep-scrapes priority domains (max 10 pages)
4. Claude API parses markdown → Event JSON array
5. Deduplicate by title+date
6. Sort by date ascending
7. Cache result 60 min
8. Return EventResponse to frontend
```

---

## File Structure (What Was Built)

### Backend
```
backend/
├── main.py                       ✅ FastAPI app, CORS, health endpoint
├── routers/
│   └── events.py                 ✅ GET /api/events endpoint
├── services/
│   ├── tavily_service.py         ✅ 4 search queries, deduped URLs
│   ├── firecrawl_service.py      ✅ Async scraping, priority domains only
│   ├── events_parser.py          ✅ Claude parsing, deduplication logic
│   └── events_service.py         ✅ Orchestrator + in-memory cache
├── models/
│   └── event.py                  ✅ Event + EventResponse Pydantic models
├── requirements.txt              ✅ fastapi, uvicorn, tavily, firecrawl, anthropic
└── .env.example                  ✅
```

### Frontend
```
frontend/
├── src/
│   ├── components/
│   │   ├── EventCard.tsx         ✅ Photo + badge + meta + CTA button (no icons)
│   │   ├── EventGrid.tsx         ✅ Grid layout, empty state
│   │   ├── FilterBar.tsx         ✅ Category + date range pills, refresh button
│   │   └── LoadingSkeleton.tsx   ✅ 8-card shimmer skeleton
│   ├── pages/
│   │   └── Home.tsx              ✅ Main page, mock data banner
│   ├── hooks/
│   │   └── useEvents.ts          ✅ Data fetching, falls back to mock data on error
│   ├── utils/
│   │   ├── api.ts                ✅ fetchEvents, checkHealth
│   │   ├── format.ts             ✅ formatDate, formatTime, categoryLabel, placeholderImage
│   │   └── mockData.ts           ✅ 6 sample events (Unsplash images) for offline preview
│   ├── types/
│   │   └── event.ts              ✅ Event, EventResponse, Filters types
│   ├── App.tsx                   ✅
│   ├── main.tsx                  ✅
│   ├── vite-env.d.ts             ✅ import.meta.env TypeScript support
│   └── index.css                 ✅ Tailwind base + shimmer animation + scrollbar
├── index.html                    ✅ Inter font, meta tags
├── tailwind.config.js            ✅ Custom colors: bg, accent-purple/cyan/pink/green
├── postcss.config.js             ✅ Tailwind + autoprefixer
├── vite.config.ts                ✅ /api proxy for local dev
├── vercel.json                   ✅ SPA rewrite
└── package.json                  ✅ React 18, Vite 5, Tailwind 3, TypeScript (no icons)
```

---

## Environment Variables

### Backend `.env` (Oracle VM, never commit)
```
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

### Frontend `.env` (local dev, gitignored)
```
VITE_API_URL=http://localhost:8000/api
```

### Vercel Dashboard Environment Variables
```
VITE_API_URL=https://your-oracle-vm-domain.com/athens-events/api
```

---

## Oracle VM Access

| Item | Value |
|---|---|
| IP | `141.147.44.143` |
| User | `ubuntu` |
| SSH key | `~/.ssh/id_ed25519_ioagop` |
| SSH alias | `oracle-softone` (in `~/.ssh/config`) |
| App path on VM | `/home/ubuntu/athens-events-backend/` |

```bash
# SSH in
ssh oracle-softone

# Or direct
ssh -i ~/.ssh/id_ed25519_ioagop ubuntu@141.147.44.143
```

---

## Deployment Steps

### Backend (Oracle VM — first time)
```bash
ssh oracle-softone

cd /home/ubuntu
git clone git@github.com:adenadoume/athens-events-backend.git
cd athens-events-backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # fill in: TAVILY_API_KEY, FIRECRAWL_API_KEY, ANTHROPIC_API_KEY, CORS_ORIGINS

pm2 start "venv/bin/uvicorn main:app --host 0.0.0.0 --port 8004" --name athens-events
pm2 save && pm2 startup   # run the generated sudo command once

# Test
curl http://localhost:8004/health
```

### Backend — Update after code change
```bash
ssh oracle-softone
cd /home/ubuntu/athens-events-backend
git pull
source venv/bin/activate
pip install -r requirements.txt   # only if requirements.txt changed
pm2 restart athens-events
pm2 logs athens-events --lines 30
```

### Backend — Quick one-liner from Mac (single file change)
```bash
scp -i ~/.ssh/id_ed25519_ioagop ./services/events_service.py \
  ubuntu@141.147.44.143:/home/ubuntu/athens-events-backend/services/events_service.py \
  && ssh oracle-softone "pm2 restart athens-events"
```

### Nginx config (add to existing server block on VM)
```nginx
location /athens-events/api/ {
    proxy_pass http://localhost:8004/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

```bash
sudo nginx -t && sudo systemctl reload nginx
```

### Frontend (Vercel)
```bash
# Push to GitHub → Vercel auto-deploys from main branch
git add -A && git commit -m "message" && git push

# Set environment variable in Vercel dashboard:
# VITE_API_URL = http://141.147.44.143/athens-events/api
# (update to HTTPS domain once SSL is configured)
```

---

## Roadmap

### Phase 1 — MVP ✅ Built
- [x] Backend: FastAPI skeleton with `/api/events`
- [x] Backend: Tavily search service
- [x] Backend: Firecrawl scraper service
- [x] Backend: Claude API parser
- [x] Backend: In-memory cache (60 min TTL)
- [x] Frontend: React + Vite + TypeScript scaffold
- [x] Frontend: EventCard (photo, badge, meta, CTA — no icons)
- [x] Frontend: EventGrid with loading skeleton
- [x] Frontend: FilterBar (category + date range pills + refresh)
- [x] Frontend: Dark nightlife theme — **Tailwind CSS** (violet/cyan accents)
- [x] Frontend: Mock data fallback (6 sample events, amber preview banner)
- [x] Frontend: Fixed `vite-env.d.ts` TypeScript build error
- [x] Docs: `app_architecture.md` rewritten with actual patterns + Supabase guidance
- [x] Docs: `CLAUDE.md` (this file) as living roadmap
- [x] Repos: pushed to GitHub via SSH (`adenadoume/athens-events-*`)

### Phase 2 — Deploy & Validate
- [ ] Deploy backend to Oracle VM (port 8004)
- [ ] Configure Nginx reverse proxy on Oracle VM
- [ ] Set `VITE_API_URL=http://141.147.44.143/athens-events/api` in Vercel dashboard
- [ ] Test end-to-end with real API keys (Tavily + Firecrawl + Anthropic)
- [ ] Add Vercel domain to `CORS_ORIGINS` in backend `.env`

### Phase 3 — Polish & Data Quality
- [ ] Test each data source (Viva.gr, RA, TicketSwap)
- [ ] Tune Tavily queries for better relevance
- [ ] Handle missing images (verify placeholders)
- [ ] Add event detail modal (click card → full info)
- [ ] Add map view (Google Maps embed per event)

### Phase 4 — Advanced (optional)
- [ ] Redis cache (replace in-memory, survives restarts)
- [ ] Cron job: refresh events every 4 hours automatically
- [ ] Playwright MCP: scrape Facebook Events, login-gated sites
- [ ] Search bar: filter events by keyword
- [ ] Push notifications for new events matching saved preferences

---

## API Keys Needed

| Service | Where to Get | Notes |
|---|---|---|
| Tavily | https://app.tavily.com | Free tier: 1000 searches/month |
| Firecrawl | https://firecrawl.dev | Free tier: 500 pages/month |
| Anthropic | https://console.anthropic.com | Pay-per-use, claude-sonnet-4-5 |

---

## Notes & Decisions Log

**May 2026 — Initial Build**
- Decided: TypeScript frontend (consistent with all other personal apps)
- Decided: No Ant Design (wrong fit for consumer nightlife app)
- Decided: No icons anywhere — clean text-only UI
- Decided: **Tailwind CSS** (switched from custom CSS — consistent with containers-claude and full stack)
- Decided: No React Router in Phase 1 (single page, no need)
- Decided: In-memory cache, not Redis (simpler, sufficient for Phase 1)
- Decided: No Supabase (app only fetches + displays external data, no persistence needed)
- Decided: Mock data fallback so UI is always usable before backend is deployed
- Decided: Cap Firecrawl at 10 pages/request (free tier budget)
- Decided: Combine Tavily snippets into one Claude call (efficiency)
- Decided: Port 8004 on Oracle VM (follows existing port allocation)
- Decided: SSH remotes for GitHub (`git@github.com:adenadoume/`) — HTTPS auth fails on this Mac
- Architecture documented in `app_architecture.md` for reuse in future apps

---

## How to Use This File

When starting a new session with AI on this project:

1. Give the AI this file (`CLAUDE.md`) first
2. Give `app_architecture.md` for full stack patterns/boilerplate
3. State what you want to work on (e.g. "continue Phase 2 deployment")
4. AI will have full context: what's built, what's pending, why decisions were made

When something new is decided or built, update the relevant sections here.
