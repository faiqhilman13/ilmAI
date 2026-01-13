"""Redis-based embedding cache to reduce API calls."""

import hashlib
import json
import logging
from typing import List, Optional

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Cache TTL in seconds (24 hours)
EMBEDDING_CACHE_TTL = 86400

# Cache key prefix
CACHE_PREFIX = "emb:v1:"


def _compute_cache_key(text: str, model: str = "default") -> str:
    """Compute a cache key for the given text and model."""
    # Use MD5 hash for shorter keys (collision is acceptable for cache)
    text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
    return f"{CACHE_PREFIX}{model}:{text_hash}"


async def get_cached_embedding(text: str, model: str = "default") -> Optional[List[float]]:
    """
    Get a cached embedding from Redis.

    Args:
        text: The text that was embedded
        model: The embedding model identifier

    Returns:
        The cached embedding list, or None if not found
    """
    try:
        redis = await get_redis()
        if redis is None:
            return None

        cache_key = _compute_cache_key(text, model)
        cached = await redis.get(cache_key)

        if cached:
            logger.debug(f"Embedding cache hit for key {cache_key[:32]}...")
            return json.loads(cached)

        return None

    except Exception as e:
        logger.warning(f"Embedding cache get failed: {e}")
        return None


async def set_cached_embedding(
    text: str,
    embedding: List[float],
    model: str = "default",
    ttl: int = EMBEDDING_CACHE_TTL,
) -> bool:
    """
    Cache an embedding in Redis.

    Args:
        text: The text that was embedded
        embedding: The embedding vector
        model: The embedding model identifier
        ttl: Time-to-live in seconds

    Returns:
        True if cached successfully, False otherwise
    """
    try:
        redis = await get_redis()
        if redis is None:
            return False

        cache_key = _compute_cache_key(text, model)
        # Serialize embedding to JSON (compact format)
        embedding_json = json.dumps(embedding, separators=(",", ":"))

        await redis.setex(cache_key, ttl, embedding_json)
        logger.debug(f"Embedding cached for key {cache_key[:32]}...")
        return True

    except Exception as e:
        logger.warning(f"Embedding cache set failed: {e}")
        return False


async def get_or_compute_embedding(
    text: str,
    compute_fn,
    model: str = "default",
) -> List[float]:
    """
    Get embedding from cache or compute and cache it.

    Args:
        text: The text to embed
        compute_fn: Async function to compute embedding if not cached
        model: The embedding model identifier

    Returns:
        The embedding vector
    """
    # Try cache first
    cached = await get_cached_embedding(text, model)
    if cached is not None:
        return cached

    # Compute embedding
    embedding = await compute_fn(text)

    # Cache for future use (fire and forget)
    await set_cached_embedding(text, embedding, model)

    return embedding


async def get_embedding_cache_stats() -> dict:
    """Get cache statistics (approximate)."""
    try:
        redis = await get_redis()
        if redis is None:
            return {"status": "unavailable"}

        # Count keys with our prefix
        cursor = 0
        count = 0
        pattern = f"{CACHE_PREFIX}*"

        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            count += len(keys)
            if cursor == 0:
                break

        return {
            "status": "available",
            "cached_embeddings": count,
            "ttl_seconds": EMBEDDING_CACHE_TTL,
        }

    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}
