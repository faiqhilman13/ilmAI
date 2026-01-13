"""Anthropic Claude LLM client implementation."""

import logging
from typing import AsyncGenerator, List

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.llm.base import BaseLLMClient
from app.core.exceptions import LLMError
from app.core.circuit_breaker import anthropic_circuit, openai_circuit

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client for chat, with OpenAI for embeddings."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        openai_api_key: str = "",
        openai_org_id: str = "",
        openai_project_id: str = "",
        embedding_model: str = "text-embedding-3-small",
    ):
        """Initialize Anthropic client.

        Args:
            api_key: Anthropic API key
            model: Claude model name
            openai_api_key: OpenAI API key for embeddings (Claude doesn't have embeddings)
            openai_org_id: Optional OpenAI organization id for embeddings
            openai_project_id: Optional OpenAI project id for embeddings
            embedding_model: OpenAI embedding model
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

        # Use OpenAI for embeddings since Anthropic doesn't have embedding API
        if openai_api_key:
            client_kwargs = {"api_key": openai_api_key}
            if openai_org_id:
                client_kwargs["organization"] = openai_org_id
            if openai_project_id:
                client_kwargs["project"] = openai_project_id
            self.openai_client = AsyncOpenAI(**client_kwargs)
        else:
            self.openai_client = None
        self.embedding_model = embedding_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response from Claude."""
        async def _do_generate() -> str:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=temperature,
            )
            return response.content[0].text

        try:
            return await anthropic_circuit.call(_do_generate)
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise LLMError(f"Anthropic API error: {str(e)}")

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from Claude."""
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=temperature,
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise LLMError(f"Anthropic API error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI (Anthropic doesn't have embeddings)."""
        if not self.openai_client:
            raise LLMError("OpenAI API key required for embeddings when using Anthropic")

        async def _do_embedding() -> List[float]:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding

        try:
            return await openai_circuit.call(_do_embedding)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise LLMError(f"Embedding error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI."""
        if not self.openai_client:
            raise LLMError("OpenAI API key required for embeddings when using Anthropic")

        async def _do_batch_embedding() -> List[List[float]]:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]

        try:
            return await openai_circuit.call(_do_batch_embedding)
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            raise LLMError(f"Embedding error: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Estimate token count for Claude (no official tokenizer)."""
        # Claude's tokenizer is not publicly available
        # Rough estimate: ~3.5 chars per token for English
        # Arabic text may be more tokens per character
        return len(text) // 3
