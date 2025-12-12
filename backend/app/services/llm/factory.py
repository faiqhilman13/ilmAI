"""LLM client factory for provider switching."""

from functools import lru_cache

from app.config import get_settings, Settings
from app.services.llm.base import BaseLLMClient
from app.services.llm.openai_client import OpenAIClient
from app.services.llm.anthropic_client import AnthropicClient


def create_llm_client(settings: Settings) -> BaseLLMClient:
    """Create LLM client based on settings.

    Args:
        settings: Application settings

    Returns:
        Configured LLM client

    Raises:
        ValueError: If provider is unknown
    """
    if settings.llm_provider == "openai":
        return OpenAIClient(
            api_key=settings.openai_api_key,
            org_id=settings.openai_org_id,
            project_id=settings.openai_project_id,
            chat_model=settings.openai_chat_model,
            embedding_model=settings.openai_embedding_model,
        )
    elif settings.llm_provider == "anthropic":
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            openai_api_key=settings.openai_api_key,  # For embeddings
            openai_org_id=settings.openai_org_id,
            openai_project_id=settings.openai_project_id,
            embedding_model=settings.openai_embedding_model,
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")


@lru_cache(maxsize=1)
def get_llm_client() -> BaseLLMClient:
    """Get cached LLM client instance.

    Returns:
        Configured LLM client singleton
    """
    settings = get_settings()
    return create_llm_client(settings)


def get_embedding_client() -> BaseLLMClient:
    """Get client for embeddings (always uses the same client for consistency).

    Returns:
        LLM client for embedding generation
    """
    return get_llm_client()
