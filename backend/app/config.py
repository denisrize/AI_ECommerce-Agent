from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Centralized application configuration.
    
    Values are loaded from environment variables or .env file.
    This is the SINGLE SOURCE OF TRUTH for all config — no hardcoded
    values anywhere else in the codebase.
    
    Why pydantic-settings?
    - Auto-validates types (catches bad config early)
    - Reads from .env files automatically
    - Gives clear error messages for missing required fields
    """

    # ── Database ──────────────────────────────────────────────
    # Two URLs because SQLAlchemy async and Alembic sync need different drivers
    # asyncpg = async driver (used by the running app)
    # plain postgresql = sync driver (used by Alembic migrations)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ecommerce"
    sync_database_url: str = "postgresql://postgres:postgres@localhost:5432/ecommerce"

    # ── LLM Configuration ─────────────────────────────────────
    # Starting with GPT-4o. Later we'll add model routing logic
    # that selects the best model per task (e.g., cheaper model for
    # simple FAQ, stronger model for multi-step reasoning).
    openai_api_key: str = ""
    default_model: str = "gpt-4o"

    # ── App ────────────────────────────────────────────────────
    app_name: str = "E-commerce Agent"
    debug: bool = True

    class Config:
        env_file = ".env"
        # This means DATABASE_URL env var maps to database_url field
        # (case-insensitive matching)


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    
    lru_cache ensures we only read .env once, not on every request.
    The tradeoff: if you change .env, you need to restart the app.
    That's fine — config changes should require a restart.
    """
    return Settings()


settings = get_settings()
