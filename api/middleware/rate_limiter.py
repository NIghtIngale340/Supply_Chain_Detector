from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class _InMemoryBackend:
    """Sliding-window rate limiter using per-process memory (single-replica only)."""

    def __init__(self) -> None:
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def is_rate_limited(self, key: str, max_requests: int, window: int) -> bool:
        now = time.time()
        bucket = self._requests[key]
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= max_requests:
            return True
        bucket.append(now)
        return False


class _RedisBackend:
    """Sliding-window rate limiter backed by Redis — safe for multi-replica deployments."""

    def __init__(self) -> None:
        import redis as _redis

        url = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
        self._client = _redis.from_url(url, decode_responses=True)
        # Validate connection early so caller can fall back to in-memory
        self._client.ping()

    def is_rate_limited(self, key: str, max_requests: int, window: int) -> bool:
        """Use a Redis sorted-set sliding window per client key."""
        import time as _time

        now = _time.time()
        redis_key = f"ratelimit:{key}"
        pipe = self._client.pipeline(transaction=True)
        pipe.zremrangebyscore(redis_key, 0, now - window)
        pipe.zadd(redis_key, {str(now): now})
        pipe.zcard(redis_key)
        pipe.expire(redis_key, window)
        results = pipe.execute()
        count = results[2]
        return count > max_requests


def _build_backend() -> _InMemoryBackend | _RedisBackend:
    backend_pref = os.getenv("RATE_LIMITER_BACKEND", "redis").lower()
    if backend_pref == "redis":
        try:
            backend = _RedisBackend()
            logger.info("Rate limiter using Redis backend")
            return backend
        except Exception:
            logger.warning("Redis unavailable for rate limiter — falling back to in-memory")
    else:
        logger.info("Rate limiter using in-memory backend (RATE_LIMITER_BACKEND=%s)", backend_pref)
    return _InMemoryBackend()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._backend = _build_backend()

    async def dispatch(self, request: Request, call_next) -> Response:
        client_host = request.client.host if request.client else "unknown"

        try:
            limited = self._backend.is_rate_limited(
                client_host, self.max_requests, self.window_seconds,
            )
        except Exception:
            # If Redis goes down mid-flight, allow the request rather than 500
            limited = False

        if limited:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please retry later."},
            )

        return await call_next(request)
