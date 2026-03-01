from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    llm_trigger_threshold: int
    cache_ttl_seconds: int
    result_ttl_seconds: int


def get_settings() -> Settings:
    threshold = int(os.getenv("LLM_TRIGGER_THRESHOLD", "20"))
    if threshold < 0 or threshold > 100:
        raise ValueError("LLM_TRIGGER_THRESHOLD must be in [0, 100]")

    cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "1800"))
    result_ttl = int(os.getenv("RESULT_TTL_SECONDS", "86400"))
    if cache_ttl <= 0 or result_ttl <= 0:
        raise ValueError("CACHE_TTL_SECONDS and RESULT_TTL_SECONDS must be > 0")

    return Settings(
        llm_trigger_threshold=threshold,
        cache_ttl_seconds=cache_ttl,
        result_ttl_seconds=result_ttl,
    )
