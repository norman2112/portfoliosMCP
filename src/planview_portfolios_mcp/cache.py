"""In-memory TTL cache for rarely-changing reference data."""

import hashlib
import json
import logging
import os
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from .config import settings

logger = logging.getLogger(__name__)

# Module-level cache: key -> (value, expires_at)
_cache: dict[str, tuple[Any, float]] = {}
_hits = 0
_misses = 0


def _cache_key(prefix: str, *args: Any, **kwargs: Any) -> str:
    """Generate a stable cache key from function name and arguments."""
    try:
        raw = f"{prefix}:{args!r}:{sorted(kwargs.items())!r}"
        return hashlib.sha256(raw.encode()).hexdigest()
    except (TypeError, ValueError, UnicodeEncodeError, MemoryError):
        logger.exception("Failed to build cache key from arguments")
        return f"{prefix}:{time.time()}"


def cached(ttl: int | None = None, key_prefix: str = "") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Cache decorator with TTL. Works with sync functions only (call from sync context)."""

    cache_ttl = ttl if ttl is not None else settings.mcp_cache_ttl_seconds

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        prefix = key_prefix or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            global _hits, _misses
            if not settings.mcp_cache_enabled:
                return func(*args, **kwargs)
            key = _cache_key(prefix, *args, **kwargs)
            now = time.time()
            if key in _cache:
                value, expires_at = _cache[key]
                if now < expires_at:
                    _hits += 1
                    logger.debug("Cache hit for %s", prefix)
                    return value
                del _cache[key]
            _misses += 1
            result = func(*args, **kwargs)
            _cache[key] = (result, now + cache_ttl)
            return result

        return wrapper

    return decorator


def clear_cache() -> None:
    """Clear all cached data. Exposed as optional tool for testing."""
    global _hits, _misses
    _cache.clear()
    _hits = 0
    _misses = 0
    logger.info("Cache cleared")


def cache_stats() -> dict[str, Any]:
    """Return hit/miss counts and current cache size."""
    total = _hits + _misses
    return {
        "size": len(_cache),
        "hits": _hits,
        "misses": _misses,
        "hit_rate_pct": round(100 * _hits / total, 2) if total else 0,
    }
