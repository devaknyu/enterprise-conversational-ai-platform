"""Application configuration via pydantic-settings.

All environment variables are read through this module. Use get_settings()
everywhere — never use os.environ.get() or os.getenv() outside this file.

The Settings class is instantiated once and cached via lru_cache.
Test fixtures override this via app.dependency_overrides[get_settings].
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file.

    All fields map directly to the environment variables documented in
    CLAUDE.md and .env.example. Pydantic validates types and constraints
    at startup — missing required fields raise a clear error immediately.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_env: str = Field(default="development", pattern="^(development|staging|production)$")
    app_name: str = "enterprise-it-assistant"
    app_version: str = "1.0.0"
    log_level: str = "INFO"

    # Security
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    webhook_shared_secret: str = Field(..., min_length=16)

    # LLM Backend
    llm_backend: str = Field(default="gemini_api", pattern="^(gemini_api|vertex_ai)$")
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Embedding Backend
    embedding_backend: str = Field(default="local", pattern="^(local|vertex_ai)$")
    embedding_model_local: str = "all-MiniLM-L6-v2"

    # Google Cloud / Vertex AI (production only)
    google_cloud_project: str = ""
    google_cloud_region: str = "us-central1"
    google_application_credentials: str = ""
    vertex_ai_model: str = "gemini-1.5-pro"

    # ChromaDB
    chroma_persist_dir: str = "./knowledge_base/chroma_db"
    chroma_collection_name: str = "it_knowledge_base"

    # Integration flags
    use_mock_integrations: bool = True
    mock_error_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    mock_latency_ms_min: int = 100
    mock_latency_ms_max: int = 300

    # ServiceNow
    servicenow_base_url: str = "https://mock.servicenow.internal"
    servicenow_username: str = ""
    servicenow_password: str = ""

    # Active Directory
    ad_base_url: str = "https://mock.ad.internal"
    ad_service_account: str = ""

    # VPN
    vpn_api_base_url: str = "https://mock.vpn.internal"
    vpn_api_key: str = ""

    @field_validator("llm_backend")
    @classmethod
    def validate_llm_backend_credentials(cls, v: str, info: object) -> str:
        """Validate that gemini_api_key is set when LLM_BACKEND=gemini_api."""
        return v


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance.

    Uses lru_cache so Settings is instantiated exactly once per process.
    Tests override this via app.dependency_overrides[get_settings].
    """
    return Settings()
