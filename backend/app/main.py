from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import products, users, orders

app = FastAPI(
    title="E-commerce Agent API",
    description="AI-powered e-commerce operations assistant",
    version="0.1.0",
    redirect_slashes=True,
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

# ── Routes ────────────────────────────────────────────────────
# Each router handles a group of related endpoints.
# The prefix="/api/v1" means all routes start with /api/v1/...
# Versioning (v1) lets you make breaking API changes later by
# adding /api/v2/ without breaking existing clients.
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "E-commerce Agent API is running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}