"""Async circuit breaker pattern for external API calls."""

import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failing, requests are rejected
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Async circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker("openai", failure_threshold=5, recovery_timeout=60)

        @breaker
        async def call_openai():
            ...
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            half_open_max_calls: Max calls allowed in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    async def _check_state(self) -> CircuitState:
        """Check and potentially update circuit state."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time is not None:
                    time_since_failure = time.time() - self._last_failure_time
                    if time_since_failure >= self.recovery_timeout:
                        logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN (recovery timeout passed)")
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0

            return self._state

    async def _record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED (recovered)")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def _record_failure(self, exc: Exception) -> None:
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state reopens the circuit
                logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure during recovery)")
                self._state = CircuitState.OPEN

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.warning(
                        f"Circuit {self.name}: CLOSED -> OPEN "
                        f"(threshold {self.failure_threshold} reached)"
                    )
                    self._state = CircuitState.OPEN

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with circuit breaker protection.

        Raises:
            HTTPException: If circuit is open
        """
        current_state = await self._check_state()

        if current_state == CircuitState.OPEN:
            logger.warning(f"Circuit {self.name} is OPEN, rejecting request")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service temporarily unavailable. Please try again later.",
            )

        try:
            result = await func(*args, **kwargs)
            await self._record_success()
            return result
        except HTTPException:
            # Don't count HTTP exceptions from our own code as circuit failures
            raise
        except Exception as e:
            await self._record_failure(e)
            raise

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator form of circuit breaker."""
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await self.call(func, *args, **kwargs)
        return wrapper

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time,
        }


# Global circuit breakers for different services
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """Get or create a circuit breaker for the given service."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _circuit_breakers[name]


def get_all_circuit_statuses() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers."""
    return {name: cb.get_status() for name, cb in _circuit_breakers.items()}


# Pre-configured circuit breakers for common services
openai_circuit = get_circuit_breaker("openai", failure_threshold=5, recovery_timeout=60)
anthropic_circuit = get_circuit_breaker("anthropic", failure_threshold=5, recovery_timeout=60)
