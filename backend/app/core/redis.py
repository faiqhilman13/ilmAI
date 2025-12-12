"""Redis connection management."""

from typing import Optional

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global _redis_client
    _redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    # Test connection
    await _redis_client.ping()


async def get_redis() -> redis.Redis:
    """Get Redis client instance."""
    if _redis_client is None:
        await init_redis()
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
