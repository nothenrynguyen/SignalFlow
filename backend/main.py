from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()  # loads backend/.env when running locally

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import events, metrics, health
from db import create_tables
from websocket.routes import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup (idempotent — uses CREATE IF NOT EXISTS)."""
    await create_tables()
    yield


app = FastAPI(
    title="SignalFlow API",
    description="Real-Time Event Analytics Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(ws_router, prefix="/ws", tags=["websocket"])
