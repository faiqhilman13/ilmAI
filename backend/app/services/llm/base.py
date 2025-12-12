"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User message/question
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM.

        Args:
            system_prompt: System instructions for the model
            user_prompt: User message/question
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

    def count_tokens(self, text: str) -> int:
        """Count tokens in text. Default implementation uses character-based estimate.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Default rough estimate: ~4 chars per token
        return len(text) // 4
