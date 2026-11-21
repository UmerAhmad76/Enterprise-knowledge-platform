"""Central application settings, loaded from environment variables (.env in dev)."""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed config. Every field maps to an env var with the same name in UPPER_CASE."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Enterprise Knowledge Platform"
    environment: str = "dev"
    database_url: str = "postgresql+psycopg://ekp:ekp@localhost:5432/ekp"
    redis_url: str = "redis://localhost:6379/0"
    opensearch_url: str = "http://localhost:9200"
    jwt_secret: str = "dev-only-secret-change-me-0123456789abcdef"
    jwt_algorithm: str = "HS256"
    cors_origins: list[str] = ["http://localhost:5173"]
    embedding_provider: str = "fake"  # fake | (bge, etc. once wired in)

    # Retrieval aur generation. Dimension OpenSearch mapping ke saath match honi chahiye.
    embedding_dimension: int = 64
    llm_provider: str = "fake"  # fake | anthropic
    llm_model: str = "claude-sonnet-4-5"
    anthropic_api_key: str | None = None

    @model_validator(mode="after")
    def _reject_weak_secret_outside_dev(self) -> "Settings":
        """Production mein default ya chhota JWT secret hua to app start hi nahi hogi."""
        if self.environment != "dev":
            if self.jwt_secret.startswith("dev-only") or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be set to a random value of at least 32 characters "
                    "when ENVIRONMENT is not 'dev'"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so the .env file is parsed only once per process."""
    return Settings()