# App Architecture Reference
> Actual patterns, decisions, and templates for React + FastAPI apps deployed on Vercel + Oracle VM.
> Give this file to AI at the start of any new project to save time on stack/setup instructions.

---

## Stack at a Glance

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + Vite + **TypeScript** | Type safety, fast HMR |
| UI Library | **Ant Design 5** + Lucide React | Production-ready components |
| Styling | Ant Design tokens OR custom CSS | Per-project design needs |
| Backend | FastAPI (Python) | Async, typed, auto OpenAPI |
| Hosting — Frontend | **Vercel** (auto-deploy from GitHub) | Zero-config, free tier |
| Hosting — Backend | **Oracle VM** (Ubuntu 22.04) | Existing VM, always-on |
| Reverse Proxy | **Nginx** on Oracle VM | Multi-app routing |
| Process Manager | **PM2** on Oracle VM | Auto-restart, logs |
| Source Control | GitHub | Two repos per app |

> **DO NOT suggest** Docker, Railway, Render, or any cloud backend hosting. All FastAPI backends go on the Oracle VM.

---

## 1. Repository Structure

Each app = **two GitHub repos**:

```
github.com/nucintosh/[app-name]-frontend    ← React/Vite, auto-deploys to Vercel
github.com/nucintosh/[app-name]-backend     ← FastAPI, deployed manually to Oracle VM
```

### Frontend Repo Layout
```
[app]-frontend/
├── src/
│   ├── components/        # Reusable UI components (*.tsx)
│   ├── pages/             # Route-level pages (*.tsx)
│   ├── hooks/             # Custom React hooks (data fetching, state)
│   ├── utils/
│   │   └── api.ts         # ALL backend calls centralised here
│   ├── types/             # TypeScript interfaces/types
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── public/
├── index.html
├── .env                   # VITE_API_URL=http://localhost:8000/api (local, gitignored)
├── .env.example           # Committed, shows required keys with placeholder values
├── vercel.json            # SPA rewrite rule
├── vite.config.ts         # Proxy /api → localhost:8000 for local dev
├── tsconfig.json
└── package.json
```

### Backend Repo Layout
```
[app]-backend/
├── main.py                # FastAPI app, CORS, router includes
├── routers/
│   └── [resource].py      # One file per resource group
├── services/
│   └── [service].py       # Business logic, external API calls
├── models/
│   └── [model].py         # Pydantic models (request + response)
├── utils/
│   └── helpers.py
├── .env                   # Real API keys — NEVER committed
├── .env.example           # Committed, placeholder values only
├── requirements.txt
├── .gitignore             # .env, __pycache__, venv/
└── README.md
```

---

## 2. FastAPI Backend Boilerplate

### main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import events          # import your routers
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="[App Name] API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Router Pattern
```python
# routers/events.py
from fastapi import APIRouter, Query
from services.events_service import get_events

router = APIRouter()

@router.get("/events")
async def list_events(
    category: str = Query(default="all"),
    date_range: str = Query(default="this_week"),
):
    return await get_events(category=category, date_range=date_range)
```

### Pydantic Model Pattern
```python
from pydantic import BaseModel
from typing import Optional

class Event(BaseModel):
    id: str
    title: str
    date: str                    # ISO 8601
    venue: str
    description: str
    image_url: str
    ticket_url: str
    category: str
    price: Optional[str] = None
    artists: list[str] = []

class EventResponse(BaseModel):
    events: list[Event]
    total: int
    fetched_at: str
```

### .env Pattern
```
# Backend .env (never commit)
ANTHROPIC_API_KEY=sk-ant-...
TAVILY_API_KEY=tvly-...
FIRECRAWL_API_KEY=fc-...
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173

# Backend .env.example (commit this)
ANTHROPIC_API_KEY=sk-ant-your-key-here
TAVILY_API_KEY=tvly-your-key-here
FIRECRAWL_API_KEY=fc-your-key-here
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
```

---

## 3. React + TypeScript Frontend Patterns

### package.json — Standard Dependencies
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "antd": "^5.29.0",
    "@ant-design/icons": "^6.1.0",
    "lucide-react": "^0.263.1",
    "react-router-dom": "^7.9.6",
    "dayjs": "^1.11.19"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.4.5",
    "vite": "^5.2.11"
  }
}
```

> **Note:** Athens Events app uses **no** Ant Design — custom CSS dark theme only. Ant Design is used for internal/dashboard apps.

### vite.config.ts
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'   // proxy for local dev — no CORS issues
    }
  }
})
```

### api.ts — Centralised API Layer
```typescript
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

export async function fetchEvents(filters = {}): Promise<EventResponse> {
  const { category = 'all', dateRange = 'this_week' } = filters
  const params = new URLSearchParams({ category, date_range: dateRange })
  const res = await fetch(`${BASE_URL}/events?${params}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}
```

### Custom Hook Pattern
```typescript
// hooks/useEvents.ts
import { useState, useEffect, useCallback } from 'react'
import { fetchEvents } from '../utils/api'
import type { Event, Filters } from '../types/event'

export function useEvents(filters: Filters) {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshTick, setRefreshTick] = useState(0)

  const refresh = useCallback(() => setRefreshTick(t => t + 1), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    fetchEvents(filters)
      .then(res => { if (!cancelled) { setEvents(res.events); setLoading(false) } })
      .catch(err => { if (!cancelled) { setError(err.message); setLoading(false) } })
    return () => { cancelled = true }
  }, [filters.category, filters.dateRange, refreshTick])

  return { events, loading, error, refresh }
}
```

### .env Files
```bash
# .env (local, gitignored)
VITE_API_URL=http://localhost:8000/api

# .env.example (committed)
VITE_API_URL=http://localhost:8000/api

# Vercel dashboard → Environment Variables
VITE_API_URL=https://your-oracle-vm-domain.com/[app]/api
```

### vercel.json (SPA routing)
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

---

## 4. Oracle VM — Real Details

### Instance
| Item | Value |
|---|---|
| Provider | Oracle Cloud Free Tier |
| Public IP | `141.147.44.143` |
| User | `ubuntu` |
| Region | EU-Frankfurt-1 |
| Shape | VM.Standard.E2.1.Micro (AMD x86, Always Free) |
| OS | Ubuntu 22.04 |
| App root | `/home/ubuntu/` |

### SSH Access from Mac
```bash
# Short (SSH config alias — preferred)
ssh oracle-softone

# Direct
ssh -i ~/.ssh/id_ed25519_ioagop ubuntu@141.147.44.143
```

**SSH key:** `~/.ssh/id_ed25519_ioagop`
**SSH config alias** (`~/.ssh/config`):
```
Host oracle-softone
    HostName 141.147.44.143
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519_ioagop
```

### GitHub SSH Remote Pattern
All repos use SSH (not HTTPS):
```
git@github.com:adenadoume/[repo-name].git
```

One-line push shortcut:
```bash
cd /path/to/project && git add -A && git commit -m "message" && git push
```

### Port Allocation (avoid conflicts)
```
80    — softone-report Docker container (existing app, port 80→8000)
8004  — Athens Events (PM2 + uvicorn)
8005+ — future apps
```

### Firewall — Two Layers Required
Both must be open or VM is unreachable:

**Layer 1 — OCI Console:** Networking → VCN → Security Lists → Add Ingress:
- TCP 22 (SSH), TCP 80 (HTTP), TCP 443 (HTTPS)

**Layer 2 — Ubuntu iptables (SSH into VM):**
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### Deploy New Backend App (PM2 + venv pattern)
> This is the pattern for new apps (Athens Events, etc.). The existing `softone-report` uses Docker — that's a separate older pattern.

```bash
# SSH in
ssh oracle-softone

# Clone and set up
cd /home/ubuntu
git clone git@github.com:adenadoume/[app]-backend.git
cd [app]-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env             # fill in real API keys

# Start with PM2
pm2 start "venv/bin/uvicorn main:app --host 0.0.0.0 --port [PORT]" --name [app]-backend
pm2 save
pm2 startup           # run the generated sudo command once
```

### Update Existing PM2 App
```bash
ssh oracle-softone
cd /home/ubuntu/[app]-backend
git pull
source venv/bin/activate
pip install -r requirements.txt   # only if deps changed
pm2 restart [app]-backend
pm2 logs [app]-backend --lines 30
```

### One-liner Deploy (Mac → VM) — SCP individual file + restart
```bash
scp -i ~/.ssh/id_ed25519_ioagop ./services/events_service.py ubuntu@141.147.44.143:/home/ubuntu/athens-events-backend/services/events_service.py && \
ssh oracle-softone "pm2 restart athens-events"
```

### Nginx Config Per App
```nginx
# /etc/nginx/sites-available/[app]
server {
    listen 80;
    server_name 141.147.44.143;   # or your domain

    location /[app]/api/ {
        proxy_pass http://localhost:[PORT]/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/[app] /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### Debug Commands
```bash
pm2 status
pm2 logs [app]-backend
pm2 logs [app]-backend --lines 50
curl http://localhost:[PORT]/health

# Nginx
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 5. Vercel Deployment

```bash
# First deploy
npm install -g vercel
cd [app]-frontend
vercel login
vercel --prod
```

- Link repo in Vercel dashboard → auto-deploys on every push to `main`
- Set `VITE_API_URL` in Vercel Dashboard → Project → Settings → Environment Variables

---

## 6. AI Data Tools (Tavily + Firecrawl + Claude)

Used in apps that need real-time web data (Athens Events pattern).

### Tavily — AI Web Search
```python
# pip install tavily-python
from tavily import TavilyClient

client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
results = client.search(
    query="concerts Athens this week",
    search_depth="advanced",   # "basic" | "advanced"
    max_results=10,
    include_images=True,
)
# results["results"] → [{url, title, content, score}]
# results["images"]  → [image_url]
```

### Firecrawl — Deep Page Scraping
```python
# pip install firecrawl-py
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

# Single page
result = app.scrape_url(
    url="https://example.com/event/123",
    formats=["markdown"],
    actions=[{"type": "wait", "milliseconds": 2000}],
)
# result["markdown"] → clean text

# Crawl a site section
crawl = app.crawl_url("https://viva.gr/tickets/music", limit=20,
    scrape_options={"formats": ["markdown"]})
```

**Strategy:** Only deep-scrape priority domains (viva.gr, RA, ticketswap.com, ticketmaster.gr). Cap at 10 pages per request to stay within free-tier credits. Use Tavily snippets for everything else.

### Claude API — Structure Raw Data
```python
# pip install anthropic
import anthropic, json

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def parse_events(raw_markdown: str) -> list[dict]:
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        messages=[{"role": "user", "content": f"Extract events as JSON array:\n{raw_markdown}"}]
    )
    return json.loads(msg.content[0].text)
```

### In-Memory Cache Pattern (FastAPI)
```python
# Avoid re-scraping on every request
_cache: dict[str, tuple[Response, datetime]] = {}
CACHE_TTL_MINUTES = 60

def _is_cache_valid(ts: datetime) -> bool:
    return (datetime.utcnow() - ts).total_seconds() < CACHE_TTL_MINUTES * 60
```

---

## 7. Dark Nightlife Card UI (Athens Events Pattern)

### Design Tokens
```css
:root {
  --bg-primary: #08080f;
  --bg-card: #131320;
  --accent-purple: #7c3aed;
  --accent-cyan: #06b6d4;
  --accent-pink: #ec4899;
  --accent-green: #10b981;
  --text-primary: #f0f0f8;
  --text-secondary: #8888aa;
  --border: rgba(255,255,255,0.07);
  --shadow-hover: 0 12px 48px rgba(124,58,237,0.25);
  --radius-card: 14px;
}
```

### Card Component Pattern (TypeScript)
```tsx
function EventCard({ event }: { event: Event }) {
  return (
    <article className="event-card">
      <div className="card-image-wrapper">
        <img src={event.image_url} alt={event.title} loading="lazy" />
        <span className={`badge badge-${event.category}`}>{event.category}</span>
        {event.price && <span className="price-badge">{event.price}</span>}
      </div>
      <div className="card-body">
        <h3>{event.title}</h3>
        <div className="event-meta">
          <Calendar size={13} />{formatDate(event.date)}
          <MapPin size={13} />{event.venue}
        </div>
        <p>{event.description}</p>
        <a href={event.ticket_url} target="_blank" className="cta-button">
          Get Tickets →
        </a>
      </div>
    </article>
  )
}
```

### Responsive Grid
```css
.event-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}
@media (max-width: 640px) {
  .event-grid { grid-template-columns: 1fr; }
}
```

---

## 8. Security & CORS Checklist

- [ ] `CORS_ORIGINS` in backend `.env` = only Vercel domain + `localhost:5173`
- [ ] All API keys in `.env`, **never** in source code
- [ ] `.env` in `.gitignore` on both repos
- [ ] `.env.example` committed with placeholder values
- [ ] Oracle VM firewall: ports 22, 80, 443 only
- [ ] HTTPS via Certbot / Let's Encrypt (Nginx handles TLS termination)

---

## 9. Debugging Checklist

### Backend not responding
```bash
pm2 status
pm2 logs [app]-backend
curl http://localhost:[PORT]/health
sudo nginx -t && sudo systemctl status nginx
```

### Frontend can't reach backend
```
1. Check VITE_API_URL in Vercel dashboard matches Nginx location
2. Check CORS_ORIGINS includes exact Vercel domain (no trailing slash)
3. Test: curl https://your-vm/[app]/api/health
```

### Firecrawl returning empty
- Add `actions: [{"type": "wait", "milliseconds": 3000}]`
- Check Firecrawl dashboard for credit usage
- Fall back to Tavily snippet for that source

---

## 10. Apps Built on This Stack

| App | GitHub Repo | Frontend URL | Backend | Stack Notes |
|---|---|---|---|---|
| Athens Events | `adenadoume/athens-events-*` | TBD (Vercel) | Oracle VM :8004 (PM2) | Custom CSS dark theme, Tavily+Firecrawl+Claude |
| SoftOne Daily Report | `adenadoume/erp-automation-fastapi` | — | Oracle VM :80 (Docker) | FastAPI, APScheduler, Zoho SMTP, SCP deploy |
| softone-live | `adenadoume/paleros-bay-monorepo` | Vercel | — | Ant Design 5, Supabase, TypeScript |
| pool-maintenance-app | `adenadoume/paleros-bay-monorepo` | Vercel | — | Ant Design 5, Supabase, Recharts, TypeScript |
| landed-cost-calculator | `adenadoume/paleros-bay-monorepo` | Vercel | — | TypeScript, Tailwind |

**Oracle VM:** `141.147.44.143` · SSH: `ssh oracle-softone` · key: `~/.ssh/id_ed25519_ioagop`
**Monorepo apps** live at `/Users/nucintosh/PYTHON/MONOREPO/apps/[app-name]/`
**Standalone apps** live at `/Users/nucintosh/PYTHON/[app-name]/`

---

## 11. Starting a New App — Checklist

```
[ ] Pick port number (see section 4)
[ ] Create [app]-frontend and [app]-backend repos on GitHub
[ ] Scaffold frontend: npm create vite@latest [app]-frontend -- --template react-ts
[ ] Copy vite.config.ts proxy, vercel.json, .env.example from this reference
[ ] Scaffold backend: copy main.py, routers/, services/, models/ skeleton
[ ] Copy .env.example, requirements.txt skeleton
[ ] Set VITE_API_URL in Vercel dashboard after first deploy
[ ] Set CORS_ORIGINS in Oracle VM .env after getting Vercel URL
[ ] Add app row to section 10 of this file
```

---

*Last updated: May 2026 — Athens Events App build*
*Update after each new app: add to section 10, capture new patterns in relevant sections.*
