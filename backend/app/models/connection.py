from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# ── Engine ────────────────────────────────────────────────────
# The engine manages a POOL of database connections.
# 
# Why a pool? Opening a new DB connection is expensive (~50-100ms).
# The pool keeps connections open and reuses them. When your route
# needs a connection, it grabs one from the pool instantly instead
# of waiting to establish a new one.
#
# pool_pre_ping=True: Before handing out a connection, the pool
# sends a quick "are you alive?" ping. This prevents crashes from
# stale connections (e.g., if PostgreSQL restarted).
#
# echo=settings.debug: When debug=True, SQLAlchemy prints every
# SQL query it runs. Extremely useful for learning and debugging,
# but turn it off in production (noisy + slight performance cost).

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

# ── Session Factory ───────────────────────────────────────────
# This doesn't create a session — it creates a FACTORY that knows
# how to create sessions. 
#
# expire_on_commit=False: Normally, after you commit data, 
# SQLAlchemy "expires" all objects (forgets their values), forcing
# a re-query next time you access them. With async code, that 
# re-query would fail because the session might already be closed.
# Setting this to False keeps the data in memory after commit.

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI Dependency ────────────────────────────────────────
# This is an "async generator" — it yields a session, then cleans
# up after the route finishes. FastAPI's Depends() system calls
# this automatically for any route that asks for a db session.
#
# The pattern is: open session → yield to route → close session
# Even if the route crashes, the finally block ensures cleanup.

async def get_db():
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
