from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

import redis


@lru_cache(maxsize=1)
def _get_redis_client() -> redis.Redis | None:
    url = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    try:
        client = redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception:
        return None


def get_json(key: str) -> dict[str, Any] | None:
    client = _get_redis_client()
    if client is None:
        return None
    raw = client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def set_json(key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    client = _get_redis_client()
    if client is None:
        return
    client.setex(key, ttl_seconds, json.dumps(payload))
