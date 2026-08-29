import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[3]  # adzmate/
API_ROOT = Path(__file__).resolve().parents[1]

# Ensure GEMINI_API_KEY / OPENAI_API_KEY from apps/api/.env are visible to os.getenv
load_dotenv(API_ROOT / ".env", override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AdzMate API"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    database_url: str = f"sqlite+aiosqlite:///{API_ROOT / 'adzmate.db'}"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    redis_url: str | None = Field(default=None, validation_alias="REDIS_URL")
    storage_backend: str = Field(default="local", validation_alias="STORAGE_BACKEND")
    token_encryption_key: str | None = Field(default=None, validation_alias="TOKEN_ENCRYPTION_KEY")
    allow_demo_user: bool = Field(default=False, validation_alias="ADZMATE_ALLOW_DEMO")
    # Cloudflare R2 (S3-compatible)
    r2_account_id: str | None = Field(default=None, validation_alias="R2_ACCOUNT_ID")
    r2_access_key_id: str | None = Field(default=None, validation_alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str | None = Field(default=None, validation_alias="R2_SECRET_ACCESS_KEY")
    r2_bucket: str | None = Field(default=None, validation_alias="R2_BUCKET")
    r2_public_url: str | None = Field(default=None, validation_alias="R2_PUBLIC_URL")
    r2_endpoint: str | None = Field(default=None, validation_alias="R2_ENDPOINT")
    # Prefer apps/api/fixtures (Docker / Root Directory = apps/api); fall back to repo-root fixtures
    fixtures_dir: Path = API_ROOT / "fixtures"
    uploads_dir: Path = API_ROOT / "uploads"
    generated_dir: Path = API_ROOT / "generated"
    previews_dir: Path = API_ROOT / "previews"
    public_base_url: str = "http://localhost:8000"
    sentiment_threshold: float = 0.55
    roas_floor: float = 1.5
    creative_ready_threshold: float = 0.7
    force_fail_agent: str | None = None
    use_fixture_metrics: bool = Field(default=True, validation_alias="ADZMATE_USE_FIXTURE_METRICS")

    # Supabase Auth
    auth_enabled: bool = True
    supabase_url: str | None = None
    supabase_jwt_secret: str | None = None
    demo_workspace_id: str = "00000000-0000-4000-8000-000000000001"

    # AI agents
    use_llm: bool = False
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    use_distilbert: bool = False
    gemini_api_key: str | None = Field(default=None, validation_alias="GEMINI_API_KEY")
    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    # Free AI image generation
    use_ai_images: bool = True
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")
    hf_image_model: str = "black-forest-labs/FLUX.1-schnell"
    use_rembg: bool = False
    max_upload_mb: int = 8

    # Meta / Facebook Marketing API OAuth
    meta_app_id: str | None = Field(default=None, validation_alias="META_APP_ID")
    meta_app_secret: str | None = Field(default=None, validation_alias="META_APP_SECRET")
    meta_oauth_redirect_uri: str | None = Field(
        default=None, validation_alias="META_OAUTH_REDIRECT_URI"
    )
    web_app_url: str = Field(default="http://localhost:3000", validation_alias="WEB_APP_URL")

    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod")

    def is_development(self) -> bool:
        return self.environment.lower() in ("development", "dev", "local")

    def r2_configured(self) -> bool:
        return bool(self.r2_bucket and self.r2_access_key_id and self.r2_secret_access_key)

    def effective_storage_backend(self) -> str:
        if self.storage_backend == "r2" and self.r2_configured():
            return "r2"
        return "local"


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def is_localhost_url(url: str) -> bool:
    lower = url.lower()
    return "localhost" in lower or "127.0.0.1" in lower


def resolve_meta_oauth_redirect_uri() -> str:
    explicit = settings.meta_oauth_redirect_uri
    if explicit:
        return explicit.rstrip("/")
    return f"{settings.public_base_url.rstrip('/')}/api/meta/oauth/callback"


def normalize_database_url(url: str) -> str:
    """Convert Supabase/Heroku postgres URLs to SQLAlchemy asyncpg form."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def uses_pgbouncer(url: str) -> bool:
    """Supabase pooler (PgBouncer) breaks asyncpg prepared statements."""
    lower = url.lower()
    if ":6543" in lower or ".pooler.supabase.com" in lower:
        return True
    return os.getenv("DATABASE_USE_PGBOUNCER", "").lower() in {"1", "true", "yes"}


def _append_query_param(url: str, key: str, value: str) -> str:
    sep = "&" if "?" in url else "?"
    if f"{key}=" in url:
        return url
    return f"{url}{sep}{key}={value}"


def prepare_database_url(url: str) -> str:
    """Normalize postgres URLs and disable prepared statements for PgBouncer poolers."""
    normalized = normalize_database_url(url)
    if "+asyncpg" in normalized and uses_pgbouncer(normalized):
        normalized = _append_query_param(normalized, "prepared_statement_cache_size", "0")
    return normalized


def asyncpg_connect_args(url: str | None = None) -> dict:
    """Disable asyncpg statement cache when connecting through PgBouncer."""
    target = url or settings.database_url
    if "+asyncpg" not in target or not uses_pgbouncer(target):
        return {}
    return {
        "statement_cache_size": 0,
        # PgBouncer transaction mode reuses backend connections; unique names avoid collisions.
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    }


settings = Settings()
settings.database_url = prepare_database_url(settings.database_url)
settings.meta_app_id = _strip_or_none(settings.meta_app_id)
settings.meta_app_secret = _strip_or_none(settings.meta_app_secret)
settings.meta_oauth_redirect_uri = _strip_or_none(settings.meta_oauth_redirect_uri)
settings.public_base_url = settings.public_base_url.strip()
settings.web_app_url = settings.web_app_url.strip()
if settings.is_development() and os.getenv("ADZMATE_ALLOW_DEMO", "").lower() in {"1", "true", "yes"}:
    settings.allow_demo_user = True
elif settings.is_development() and not settings.supabase_url and not settings.supabase_jwt_secret:
    # Local hackathon demo when Supabase is not configured
    settings.allow_demo_user = True
if os.getenv("FIXTURES_DIR"):
    settings.fixtures_dir = Path(os.getenv("FIXTURES_DIR", ""))
elif not settings.fixtures_dir.is_dir() and (ROOT / "fixtures").is_dir():
    settings.fixtures_dir = ROOT / "fixtures"
if os.getenv("FORCE_FAIL_AGENT"):
    settings.force_fail_agent = os.getenv("FORCE_FAIL_AGENT")

# Resolve provider keys (Gemini preferred)
_gemini_key = settings.gemini_api_key or settings.google_api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
_openai_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")

if _gemini_key and not settings.llm_api_key:
    settings.llm_api_key = _gemini_key
    settings.llm_provider = "gemini"
    if settings.llm_base_url.rstrip("/") == "https://api.openai.com/v1" or not os.getenv("LLM_BASE_URL"):
        settings.llm_base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
    if settings.llm_model in {"gpt-4o-mini", ""} or (
        not os.getenv("LLM_MODEL") and settings.llm_model == "gpt-4o-mini"
    ):
        # Keep explicit LLM_MODEL from .env if pydantic already loaded it
        if settings.llm_model == "gpt-4o-mini":
            settings.llm_model = os.getenv("LLM_MODEL") or "gemini-2.0-flash"
elif _openai_key and not settings.llm_api_key:
    settings.llm_api_key = _openai_key
    settings.llm_provider = "openai"

_use_llm_env = os.getenv("ADZMATE_USE_LLM", "").lower()
if _use_llm_env in {"1", "true", "yes"} or settings.use_llm:
    settings.use_llm = True
if os.getenv("ADZMATE_USE_DISTILBERT", "").lower() in {"1", "true", "yes"}:
    settings.use_distilbert = True
if os.getenv("ADZMATE_USE_AI_IMAGES", "").lower() in {"0", "false", "no"}:
    settings.use_ai_images = False
if os.getenv("ADZMATE_USE_REMBG", "").lower() in {"1", "true", "yes"}:
    settings.use_rembg = True

_use_fixture_env = os.getenv("ADZMATE_USE_FIXTURE_METRICS", "").lower()
if _use_fixture_env in {"0", "false", "no"}:
    settings.use_fixture_metrics = False
elif settings.is_production() and _use_fixture_env not in {"1", "true", "yes"}:
    settings.use_fixture_metrics = False

# Auto-enable LLM when a key is present unless explicitly disabled
if settings.llm_api_key and _use_llm_env not in {"0", "false", "no"}:
    settings.use_llm = True

if "generativelanguage.googleapis.com" in settings.llm_base_url:
    settings.llm_provider = "gemini"

settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.generated_dir.mkdir(parents=True, exist_ok=True)
settings.previews_dir.mkdir(parents=True, exist_ok=True)
