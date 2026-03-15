# SignalFlow

Real-Time Event Analytics Platform — a production-style full-stack project built with FastAPI, Next.js, PostgreSQL, Redis, and WebSockets.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 15 · TypeScript · Recharts |
| Backend API | FastAPI · Python 3.12 |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 |
| Real-time | WebSockets (native FastAPI) |
| Infra | Docker · docker-compose |

---

## Project Structure

```
signalflow/
├── backend/
│   ├── api/            # Route handlers (health, events, metrics)
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic, cache, background worker
│   ├── websocket/      # WS connection manager and routes
│   ├── db.py           # Async SQLAlchemy engine + session
│   ├── main.py         # FastAPI app entry point
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/            # Next.js App Router pages
│   ├── components/     # Reusable UI components
│   ├── lib/            # API client, WebSocket hook, utilities
│   ├── next.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
cd signalflow

# 2. Create your env file
cp .env.example .env

# 3. Build and start all services
docker compose up --build

# 4. Open the dashboard
open http://localhost:3000

# 5. Explore the API docs
open http://localhost:8000/docs
```

---

## Local Development (without Docker)

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure env vars
cp ../.env.example .env
# Edit DATABASE_URL and REDIS_URL to point to localhost

# Start the API server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure env vars
cp ../.env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/metrics

# Start the dev server
npm run dev
```

---

## API Reference

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/events` | Ingest an activity event |
| GET | `/metrics/summary` | Aggregated KPI summary (Redis-cached) |
| GET | `/metrics/timeseries` | Time-bucketed event counts for charts |
| WS | `/ws/metrics` | Live metric push stream |

---

## Event Schema

```json
{
  "event_type": "page_view",
  "session_id": "abc123",
  "user_id": "user-42",
  "metadata": { "path": "/pricing" }
}
```

Supported `event_type` values: `page_view`, `click`, `signup`, `purchase`, `session_start`

---

## Simulating Events

Use the **Event Simulator** panel on the dashboard to fire single events or a burst of 10 random events directly from the UI.

Or send events via curl:

```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "signup", "session_id": "s1", "user_id": "u1"}'
```

---

## Build Phases

- [x] Phase 1 — Project structure and starter files
- [ ] Phase 2 — Backend MVP (DB, Redis, worker, full routes)
- [ ] Phase 3 — Frontend dashboard (charts, KPI cards, live updates)
- [ ] Phase 4 — Docker wiring and end-to-end test
- [ ] Phase 5 — Polish and README finalization
