# SignalFlow

A production-style real-time event analytics platform. Activity events are ingested through a REST API, aggregated asynchronously, cached in Redis, and pushed live to a dashboard over WebSockets.

Built as a full-stack portfolio project to demonstrate distributed backend thinking, async processing, and real-time UI patterns.

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
  ├── HTTP GET  /metrics/summary     ──► Redis cache (10s TTL)
  │                                         │ miss → PostgreSQL aggregates
  ├── HTTP GET  /metrics/timeseries  ──► PostgreSQL date_trunc query
  │
  ├── HTTP POST /events              ──► PostgreSQL insert
  │                                         │
  │                                   background worker
  │                                         │
  │                                   invalidate Redis cache
  │                                         │
  └── WebSocket /ws/metrics  ◄────── broadcast updated metrics
                                      to all connected clients
```

### Event ingestion pipeline

1. Client sends `POST /events` with `event_type`, `session_id`, and optional metadata
2. Pydantic validates the payload; FastAPI returns `201` with the persisted event
3. An `asyncio` background task fires immediately after — no added latency to the response
4. The task invalidates the Redis summary cache, recomputes aggregates from Postgres, and broadcasts the fresh summary to all connected WebSocket clients
5. The Next.js dashboard receives the push and updates KPI cards and charts without polling

---

## Project Structure

```
signalflow/
├── backend/
│   ├── api/              # Route handlers — health, events, metrics
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request / response shapes
│   ├── services/
│   │   ├── cache.py      # Redis async client
│   │   ├── event_service.py
│   │   ├── metrics_service.py
│   │   └── worker.py     # Background post-ingest task
│   ├── websocket/        # ConnectionManager + WS route
│   ├── db.py             # Async engine, session factory, table init
│   ├── main.py           # App entry point + lifespan hook
│   ├── seed.py           # Demo event generator
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js App Router
│   ├── components/       # StatCard, EventTypeChart, TimeseriesChart, EventSimulator
│   ├── lib/
│   │   ├── api.ts        # Typed fetch client
│   │   ├── useWebSocket.ts  # Auto-reconnecting WS hook
│   │   └── utils.ts
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Running Locally

### Option A — Docker (recommended, one command)

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

---

### Option B — Native (frontend + backend separately)

**Prerequisites:** Python 3.12+, Node 18+, a running Postgres instance, a running Redis instance.

**Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env          # set DATABASE_URL and REDIS_URL to localhost
uvicorn main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
# create frontend/.env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
#   NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/metrics
npm run dev
```

**Seed demo data**
```bash
cd backend
source .venv/bin/activate
python seed.py --count 40
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/events` | Ingest an activity event |
| `GET` | `/metrics/summary` | Aggregated KPIs — Redis-cached, 10 s TTL |
| `GET` | `/metrics/timeseries` | Time-bucketed counts (`?interval=minute\|hour\|day`) |
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

### Quick curl test

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "signup", "session_id": "s1", "user_id": "u1"}'
```

---

## Key Engineering Patterns

- **Async FastAPI** with SQLAlchemy 2.x and `asyncpg` — no blocking DB calls on the request thread
- **Redis read-through cache** — summary metrics are served from Redis and recomputed only on write, keeping read latency low under high ingest volume
- **Fire-and-forget background tasks** — `asyncio.create_task()` decouples post-ingest work from HTTP response time
- **WebSocket fan-out** — `ConnectionManager` holds all active sockets and broadcasts JSON to every connected client on each ingest
- **Pydantic v2 validation** — all inputs validated at the boundary; invalid payloads are rejected with structured 422 errors
- **Containerised multi-service stack** — Postgres, Redis, API, and UI all defined in a single `docker-compose.yml`
