"""
Pytest fixtures shared across the test suite.

Uses an in-memory SQLite database so tests run without a live Postgres
instance, and a fake Redis client so no Redis server is needed either.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock

# ── In-memory SQLite engine ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create tables using the real metadata
    from db import Base
    import models.event  # noqa: F401 — registers Event with Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    Returns an AsyncClient wired to the FastAPI app with:
    - DB overridden to the in-memory SQLite session
    - Redis patched to a no-op in-memory mock
    """
    # Patch Redis before importing the app so cache calls are no-ops
    import services.cache as cache_module
    fake_redis = AsyncMock()
    fake_redis.get = AsyncMock(return_value=None)   # always cache miss
    fake_redis.setex = AsyncMock(return_value=True)
    fake_redis.delete = AsyncMock(return_value=1)
    cache_module._redis_client = fake_redis

    from main import app
    from db import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    cache_module._redis_client = None
