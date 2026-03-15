# SignalFlow

**[https://signal-flow.vercel.app](https://signal-flow.vercel.app)**

A production-style real-time event analytics platform. Events are ingested through a REST API, aggregated with Redis caching, and pushed live to a dashboard over WebSockets.

Built as a full-stack portfolio project demonstrating async backend architecture, real-time UI patterns, and containerised deployment.

---

## Screenshots

### Dashboard
![SignalFlow Dashboard](assets/signalflow%20dashboard.png)

### Backend API Docs
![SignalFlow Backend](assets/signalflow%20backend.png)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 · TypeScript · Recharts |
| Backend | FastAPI · Python 3.12 · Uvicorn |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Real-time | WebSockets (native FastAPI) |
| Infra | Docker · docker-compose |

---

## Architecture

```
Browser
  │
  ├─ HTTP GET  /metrics/summary     ──► Redis cache (10 s TTL)
  │                                        │ miss → PostgreSQL aggregates
  ├─ HTTP GET  /metrics/timeseries  ──► PostgreSQL date_trunc query
  │
  ├─ HTTP POST /events              ──► PostgreSQL insert
  │                                        │
  │                                  background task (asyncio)
  │                                        ├─ invalidate Redis cache
  │                                        ├─ broadcast event_ingested → live feed
  │                                        └─ broadcast metrics_update → KPI cards
  │
  └─ WebSocket /ws/metrics  ◄──────────── fan-out to all connected clients
```

---

## How Event Ingestion Works

1. Client sends `POST /events` with `event_type`, `session_id`, and optional metadata.
2. Pydantic validates the payload; FastAPI writes the row to Postgres and returns `201` with the persisted event.
3. An `asyncio.create_task` fires immediately — the HTTP response is never blocked by this work.
4. The background task (a) invalides the Redis summary cache, (b) broadcasts `event_ingested` with the full event to all WebSocket clients (appears instantly in the live feed), and (c) recomputes the summary and broadcasts `metrics_update` (KPI cards update without polling).

## How Live Updates Work

- The Next.js dashboard opens a single WebSocket connection to `/ws/metrics` on mount.
- The hook (`useWebSocket.ts`) reconnects automatically after a 3 s delay if the connection drops.
- Two message types arrive:
  - `event_ingested` — prepended to the live event feed, capped at 20 entries.
  - `metrics_update` — triggers a re-fetch of summary and timeseries data scoped to the active time range.
- A **Pause / Resume** toggle in the header gates all incoming WebSocket messages without closing the socket. On resume, a fresh fetch catches up immediately.

---

## Project Structure

```
signalflow/
├── backend/
│   ├── api/                  # Route handlers — health, events, metrics
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request / response shapes
│   ├── services/
│   │   ├── cache.py          # Redis async client (singleton)
│   │   ├── event_service.py  # Persist events to Postgres
│   │   ├── metrics_service.py# Aggregate queries + Redis cache
│   │   └── worker.py         # Background post-ingest task
│   ├── websocket/            # ConnectionManager + WebSocket route
│   ├── tests/                # pytest suite (SQLite in-memory)
│   ├── db.py                 # Async engine, session factory, table init
│   ├── main.py               # FastAPI app entry point
│   ├── seed.py               # Demo event generator
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # StatCard, EventTypeChart, TimeseriesChart,
│   │                         # EventSimulator, RecentEventsFeed
│   ├── lib/
│   │   ├── api.ts            # Typed fetch client
│   │   ├── useWebSocket.ts   # Auto-reconnecting WebSocket hook
│   │   └── utils.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Local Setup

### Option A — Docker (all services, one command)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

To seed demo data while Docker is running:
```bash
cd backend
pip install httpx   # if not in your local env
python seed.py --count 40 --url http://localhost:8000
```

---

### Option B — Native (Postgres + Redis in Docker, services native)

**1. Start Postgres and Redis**
```bash
docker compose up -d postgres redis
```

**2. Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
# Edit .env: change postgres host to localhost, redis host to localhost
#   DATABASE_URL=postgresql+asyncpg://signalflow:signalflow@localhost:5432/signalflow
#   REDIS_URL=redis://localhost:6379
uvicorn main:app --reload --port 8000
```

**3. Frontend**
```bash
cd frontend
npm install
# Create frontend/.env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
#   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/metrics
npm run dev
```

**4. Seed demo data** (optional)
```bash
cd backend
source .venv/bin/activate
python seed.py --count 40
```

**5. Run tests**
```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/events` | Ingest an activity event |
| `GET` | `/metrics/summary` | KPI aggregates — Redis-cached, 10 s TTL. Accepts `?lookback_hours=N` |
| `GET` | `/metrics/timeseries` | Time-bucketed counts. Params: `interval` (minute\|hour\|day), `lookback_hours` |
| `WS` | `/ws/metrics` | Live push stream — server broadcasts on every ingest |

### Event payload

```json
{
  "event_type": "page_view",
  "session_id": "abc123",
  "user_id": "user-42",
  "metadata": { "path": "/pricing" }
}
```

Supported `event_type` values: `page_view` · `click` · `signup` · `purchase` · `session_start`

---

## Dashboard Features

- **KPI cards** — total events, unique sessions, unique users, top event type
- **Events by Type** — bar chart with per-type colour coding
- **Event Volume Over Time** — area chart with time-bucketed counts
- **Time range selector** — 15 m / 1 h / 24 h; controls both charts and KPI cards
- **Live event feed** — last 20 events with type pill, session ID, and relative timestamp; updates in real time
- **Pause / Resume** — freezes WebSocket updates without closing the socket; resume fetches fresh data immediately
- **Event Simulator** — fire individual events or a burst of 10 from the dashboard

---

## Deployment Notes

- For production, restrict `allow_origins` in `main.py` to your frontend domain.
- Set strong credentials in `.env`; never commit `.env` to version control.
- The backend `Dockerfile` runs without `--reload`; add a process manager (e.g. Gunicorn with Uvicorn workers) for multi-worker deployments.
- For Next.js, the frontend `Dockerfile` uses `output: 'standalone'` which produces a minimal self-contained build.
- Postgres data is persisted in a named Docker volume (`postgres_data`). Back it up before destroying the stack.
