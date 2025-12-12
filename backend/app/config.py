"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "IlmuAI"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ilmuai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration
    llm_provider: Literal["openai", "anthropic"] = "openai"

    # OpenAI
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # RAG Configuration
    rag_top_k: int = 10
    rag_rerank_top_k: int = 5
    rag_score_threshold: float = 0.3
    chunk_size: int = 500
    chunk_overlap: int = 100

    # Safety
    enable_safety_filter: bool = True

    # JWT Auth
    jwt_secret: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
