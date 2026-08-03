import os
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
    database_url: str = f"sqlite+aiosqlite:///{API_ROOT / 'adzmate.db'}"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
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


settings = Settings()
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

# Auto-enable LLM when a key is present unless explicitly disabled
if settings.llm_api_key and _use_llm_env not in {"0", "false", "no"}:
    settings.use_llm = True

if "generativelanguage.googleapis.com" in settings.llm_base_url:
    settings.llm_provider = "gemini"

settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.generated_dir.mkdir(parents=True, exist_ok=True)
settings.previews_dir.mkdir(parents=True, exist_ok=True)
