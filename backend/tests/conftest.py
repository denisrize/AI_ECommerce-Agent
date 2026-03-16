"""
Pytest configuration and shared fixtures.

Key concept: DEPENDENCY OVERRIDE
---------------------------------
In production, your routes get database sessions via Depends(get_db).
In tests, we OVERRIDE that dependency to inject our own session.
This means:
  - Tests use the same database (so seeded data is available)
  - Each test gets its own session
  - We can rollback after each test to avoid side effects

Why not use a separate test database?
  For this project, sharing the dev database is simpler. The tests
  are read-heavy (GET requests against seeded data). The few write
  tests (POST) will rollback. In a larger project, you'd use a
  dedicated test DB or SQLite in-memory.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.models.database import Base
from app.models.connection import get_db
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """
    Create a single event loop for the entire test session.
    
    Why? Async tests need an event loop. By default, pytest-asyncio
    creates one per test, but database connections opened in one
    loop can't be used in another. Sharing one loop avoids that.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for each test.
    
    scope="function" means: fresh session per test. This ensures
    tests don't leak state to each other.
    """
    engine = create_async_engine(settings.database_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        yield session
        # After the test, rollback any changes it made
        await session.rollback()

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP test client.
    
    This client talks directly to your FastAPI app IN-PROCESS —
    no actual HTTP server is started. It's fast and reliable.
    
    The dependency_overrides trick: we replace the real get_db
    with one that returns our test session. This is FastAPI's
    built-in way to inject test dependencies.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as ac:
        yield ac

    # Clean up: remove the override so it doesn't affect other tests
    app.dependency_overrides.clear()
