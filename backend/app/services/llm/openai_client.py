"""OpenAI LLM client implementation."""

import logging
from typing import AsyncGenerator, List

import tiktoken
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.llm.base import BaseLLMClient
from app.core.exceptions import LLMError
from app.core.circuit_breaker import openai_circuit

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client for chat and embeddings."""

    def __init__(
        self,
        api_key: str,
        org_id: str = "",
        project_id: str = "",
        chat_model: str = "gpt-4o",
        embedding_model: str = "text-embedding-3-small",
    ):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            org_id: Optional OpenAI organization id
            project_id: Optional OpenAI project id
            chat_model: Model for chat completions
            embedding_model: Model for embeddings
        """
        client_kwargs = {"api_key": api_key}
        if org_id:
            client_kwargs["organization"] = org_id
        if project_id:
            client_kwargs["project"] = project_id
        self.client = AsyncOpenAI(**client_kwargs)
        self.chat_model = chat_model
        self.embedding_model = embedding_model

        # Initialize tokenizer
        try:
            self.tokenizer = tiktoken.encoding_for_model(chat_model)
        except KeyError:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response from OpenAI."""
        async def _do_generate() -> str:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""

        try:
            return await openai_circuit.call(_do_generate)
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise LLMError(f"OpenAI API error: {str(e)}")

    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from OpenAI."""
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            stream = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise LLMError(f"OpenAI API error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        async def _do_embedding() -> List[float]:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return response.data[0].embedding

        try:
            return await openai_circuit.call(_do_embedding)
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise LLMError(f"OpenAI embedding error: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        async def _do_batch_embedding() -> List[List[float]]:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
            return [item.embedding for item in response.data]

        try:
            return await openai_circuit.call(_do_batch_embedding)
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            raise LLMError(f"OpenAI embedding error: {str(e)}")

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.tokenizer.encode(text))
