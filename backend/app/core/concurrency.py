"""Concurrency control utilities for managing resource usage."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Semaphore to limit concurrent RAG pipeline executions
# This prevents resource exhaustion under high load
_rag_semaphore: Optional[asyncio.Semaphore] = None

# Maximum concurrent RAG operations allowed
MAX_CONCURRENT_RAG_OPERATIONS = 20

# Timeout waiting for semaphore (seconds)
RAG_SEMAPHORE_TIMEOUT = 30.0


def _get_rag_semaphore() -> asyncio.Semaphore:
    """Get or create the RAG semaphore (lazy initialization for event loop safety)."""
    global _rag_semaphore
    if _rag_semaphore is None:
        _rag_semaphore = asyncio.Semaphore(MAX_CONCURRENT_RAG_OPERATIONS)
    return _rag_semaphore


@asynccontextmanager
async def rag_concurrency_limit():
    """
    Context manager to limit concurrent RAG pipeline executions.

    Usage:
        async with rag_concurrency_limit():
            result = await pipeline.answer(...)

    Raises:
        HTTPException: If timeout waiting for semaphore (server overloaded)
    """
    semaphore = _get_rag_semaphore()

    try:
        # Try to acquire semaphore with timeout
        acquired = await asyncio.wait_for(
            semaphore.acquire(),
            timeout=RAG_SEMAPHORE_TIMEOUT
        )
        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Server is currently overloaded. Please try again later.",
            )
    except asyncio.TimeoutError:
        logger.warning("RAG semaphore timeout - server overloaded")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is currently overloaded. Please try again later.",
        )

    try:
        yield
    finally:
        semaphore.release()


def get_rag_queue_status() -> dict:
    """Get current status of RAG concurrency queue."""
    semaphore = _get_rag_semaphore()
    available = semaphore._value if hasattr(semaphore, '_value') else 'unknown'
    return {
        "max_concurrent": MAX_CONCURRENT_RAG_OPERATIONS,
        "available_slots": available,
        "in_use": MAX_CONCURRENT_RAG_OPERATIONS - available if isinstance(available, int) else 'unknown',
    }
