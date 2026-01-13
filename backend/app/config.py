"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List, Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Always prefer `backend/.env` regardless of CWD (scripts may be run from repo root).
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
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
    # Optional: force a specific OpenAI org/project when keys belong to multiple.
    openai_org_id: str = ""
    openai_project_id: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # RAG Configuration
    rag_top_k: int = 10
    rag_rerank_top_k: int = 5
    rag_score_threshold: float = 0.2
    rag_use_hybrid: bool = True
    rag_dense_candidates: int = 30
    rag_sparse_candidates: int = 30
    rag_rrf_k: int = 60
    rag_multi_query: bool = True
    rag_num_rewrites: int = 3
    rag_self_filtering: bool = True
    # Per-source balancing is applied only for Quran-cue queries.
    rag_per_source_k: int = 1
    rag_use_source_priors: bool = True
    rag_quran_context_window: int = 1

    # Retrieval telemetry / eval (optional)
    rag_enable_retrieval_telemetry: bool = False
    # JSONL append-only log file. If relative, it is resolved from the current working directory.
    rag_retrieval_telemetry_path: str = "data/eval/retrieval/telemetry.jsonl"
    # If false, do not store the raw user query in telemetry (still stores IDs/metrics).
    rag_retrieval_telemetry_include_query: bool = True
    # Best-effort online eval for explicit refs (e.g. "2:255", "2:255-257", "Hadith #1 Bukhari")
    # by inferring ground-truth chunk_ids from DB metadata.
    rag_retrieval_auto_eval_explicit_refs: bool = True
    # Standard metric cutoffs for telemetry.
    rag_retrieval_eval_cutoffs: str = "1,3,5,10,20"

    # Reranking
    rag_use_cross_encoder_rerank: bool = True
    rag_cross_encoder_model: str = "BAAI/bge-reranker-base"
    rag_use_llm_judge_rerank: bool = True
    rag_llm_judge_candidates: int = 8
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
