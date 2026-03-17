from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import products, users, orders, chat


# ── Trailing Slash Middleware ─────────────────────────────────
# Problem: /api/v1/users and /api/v1/users/ are treated as
# different URLs by default. FastAPI's built-in handling uses
# a 307 redirect to send one to the other, but that causes
# two issues:
#
# 1. POST/PUT redirects: Some HTTP clients drop the request
#    body on redirect, causing silent failures.
# 2. Extra round trip: The client makes two requests instead
#    of one, adding latency.
#
# Solution: Strip trailing slashes BEFORE the request reaches
# the router. Both URLs hit the same handler directly, no
# redirect needed. We keep the root path "/" untouched so
# the health/root endpoints still work.

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Strip trailing slash (but not from root "/")
        if request.url.path != "/" and request.url.path.endswith("/"):
            request.scope["path"] = request.url.path.rstrip("/")
        return await call_next(request)


app = FastAPI(
    title="E-commerce Agent API",
    description="AI-powered e-commerce operations assistant",
    version="0.1.0",
    redirect_slashes=False,  # Disable default 307 redirects
)

# ── CORS Middleware ────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) controls which websites
# can call your API. Without this, a React frontend at
# localhost:5173 would be BLOCKED from calling your API at
# localhost:8000 — the browser enforces this for security.
#
# In development, we allow localhost origins. In production,
# you'd restrict this to your actual domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrailingSlashMiddleware)

# ── Routes ────────────────────────────────────────────────────
# Each router handles a group of related endpoints.
# The prefix="/api/v1" means all routes start with /api/v1/...
# Versioning (v1) lets you make breaking API changes later by
# adding /api/v2/ without breaking existing clients.
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "E-commerce Agent API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}