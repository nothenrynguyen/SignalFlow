"""
seed.py — generates a burst of realistic demo events against the running API.
Run after `uvicorn main:app --reload` is up:

    python seed.py
    python seed.py --count 50 --url http://localhost:8000
"""
import asyncio
import random
import argparse
import uuid
from datetime import datetime, timezone, timedelta

import httpx

EVENT_TYPES = ["page_view", "click", "signup", "purchase", "session_start"]

SAMPLE_METADATA = {
    "page_view": [{"path": "/home"}, {"path": "/pricing"}, {"path": "/docs"}],
    "click":     [{"element": "cta-button"}, {"element": "nav-link"}, {"element": "signup-btn"}],
    "signup":    [{"plan": "free"}, {"plan": "pro"}],
    "purchase":  [{"amount": 29.99, "currency": "USD"}, {"amount": 99.0, "currency": "USD"}],
    "session_start": [{"referrer": "google"}, {"referrer": "direct"}, {"referrer": "twitter"}],
}


def random_event(session_id: str) -> dict:
    event_type = random.choice(EVENT_TYPES)
    return {
        "event_type": event_type,
        "session_id": session_id,
        "user_id": f"user-{random.randint(1, 30)}",
        "timestamp": (
            datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60 * 24))
        ).isoformat(),
        "metadata": random.choice(SAMPLE_METADATA[event_type]),
    }


async def seed(base_url: str, count: int) -> None:
    sessions = [str(uuid.uuid4())[:8] for _ in range(max(1, count // 5))]

    async with httpx.AsyncClient(base_url=base_url, timeout=10) as client:
        tasks = [
            client.post("/events", json=random_event(random.choice(sessions)))
            for _ in range(count)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 201)
    errors    = count - successes
    print(f"Seeded {successes}/{count} events  ({errors} errors)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed SignalFlow with demo events")
    parser.add_argument("--count", type=int, default=20, help="Number of events to send")
    parser.add_argument("--url",   type=str, default="http://localhost:8000")
    args = parser.parse_args()

    asyncio.run(seed(args.url, args.count))
