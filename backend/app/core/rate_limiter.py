"""Redis-based rate limiting for API endpoints."""

import logging
import time
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Rate limit configurations
RATE_LIMITS = {
    "chat": {"requests": 30, "window_seconds": 60},      # 30 requests per minute
    "chat_burst": {"requests": 5, "window_seconds": 10}, # 5 requests per 10 seconds (burst protection)
    "auth": {"requests": 10, "window_seconds": 60},      # 10 auth attempts per minute
    "default": {"requests": 60, "window_seconds": 60},   # 60 requests per minute default
}


async def check_rate_limit(
    key: str,
    limit_type: str = "default",
) -> Tuple[bool, int, int]:
    """
    Check if a request should be rate limited.

    Args:
        key: Unique identifier (e.g., user_id, IP address)
        limit_type: Type of rate limit to apply

    Returns:
        Tuple of (is_allowed, remaining_requests, reset_time_seconds)
    """
    try:
        redis = await get_redis()
        if redis is None:
            # Redis not available, allow request
            logger.warning("Redis not available for rate limiting")
            return True, -1, 0

        config = RATE_LIMITS.get(limit_type, RATE_LIMITS["default"])
        max_requests = config["requests"]
        window_seconds = config["window_seconds"]

        redis_key = f"ratelimit:{limit_type}:{key}"
        current_time = int(time.time())
        window_start = current_time - window_seconds

        # Use Redis pipeline for atomic operations
        pipe = redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(redis_key, 0, window_start)

        # Count current requests in window
        pipe.zcard(redis_key)

        # Add current request with timestamp as score
        pipe.zadd(redis_key, {str(current_time): current_time})

        # Set expiry on the key
        pipe.expire(redis_key, window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]

        remaining = max(0, max_requests - current_count - 1)
        reset_time = window_seconds

        if current_count >= max_requests:
            return False, 0, reset_time

        return True, remaining, reset_time

    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        # On error, allow the request
        return True, -1, 0


def get_client_identifier(request: Request, user_id: Optional[str] = None) -> str:
    """
    Get a unique identifier for the client.

    Uses user_id if authenticated, otherwise falls back to IP address.
    """
    if user_id:
        return f"user:{user_id}"

    # Get client IP, considering X-Forwarded-For for proxied requests
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        client_ip = forwarded.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"

    return f"ip:{client_ip}"


async def rate_limit_request(
    request: Request,
    limit_type: str = "default",
    user_id: Optional[str] = None,
) -> None:
    """
    Apply rate limiting to a request.

    Raises HTTPException if rate limit exceeded.
    """
    client_id = get_client_identifier(request, user_id)
    is_allowed, remaining, reset_time = await check_rate_limit(client_id, limit_type)

    if not is_allowed:
        logger.warning(f"Rate limit exceeded for {client_id} ({limit_type})")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again in {reset_time} seconds.",
            headers={
                "X-RateLimit-Limit": str(RATE_LIMITS.get(limit_type, RATE_LIMITS["default"])["requests"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(reset_time),
            },
        )


async def rate_limit_chat(request: Request, user_id: Optional[str] = None) -> None:
    """
    Apply chat-specific rate limiting with burst protection.

    Checks both per-minute and burst limits.
    """
    # Check burst limit first (stricter)
    await rate_limit_request(request, "chat_burst", user_id)
    # Then check per-minute limit
    await rate_limit_request(request, "chat", user_id)
