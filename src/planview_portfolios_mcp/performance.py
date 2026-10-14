"""Performance monitoring and timing instrumentation for MCP tool operations."""

import asyncio
import inspect
import json
import logging
import sys
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, TypeVar

from .config import settings

# Dedicated performance logger; logs to stderr when enabled (MCP standard)
_perf_logger = logging.getLogger("mcp.performance")
_perf_logger.setLevel(logging.INFO)
_perf_handler = logging.StreamHandler(sys.stderr)
_perf_handler.setLevel(logging.INFO)
_perf_logger.addHandler(_perf_handler)
_perf_logger.propagate = False

# In-memory stats for shutdown summary
_perf_stats: dict[str, list[float]] = {}
_api_call_stats: list[dict[str, Any]] = []


def _ensure_perf_enabled() -> None:
    """Configure performance logger only when performance logging is enabled."""
    if settings.mcp_performance_logging and not _perf_logger.handlers:
        _perf_logger.addHandler(_perf_handler)


def log_performance_metric(
    tool: str,
    duration_ms: float,
    success: bool,
    api_calls: list[dict[str, Any]] | None = None,
    error: str | None = None,
) -> None:
    """Emit a structured performance log entry."""
    if not settings.mcp_performance_logging:
        return
    _ensure_perf_enabled()
    # Track for shutdown summary
    if tool not in _perf_stats:
        _perf_stats[tool] = []
    _perf_stats[tool].append(duration_ms)
    if api_calls:
        _api_call_stats.extend(api_calls)
    payload = {
        "tool": tool,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if api_calls:
        payload["api_calls"] = api_calls
    if error:
        payload["error"] = error
    _perf_logger.info(json.dumps(payload))


def get_performance_summary() -> dict[str, Any]:
    """Return aggregate performance stats for shutdown summary."""
    total_requests = sum(len(times) for times in _perf_stats.values())
    if total_requests == 0:
        return {"total_requests": 0}
    all_times = [t for times in _perf_stats.values() for t in times]
    by_tool = {
        tool: {
            "count": len(times),
            "avg_ms": round(sum(times) / len(times), 2),
            "total_ms": round(sum(times), 2),
        }
        for tool, times in _perf_stats.items()
    }
    slowest = max(by_tool.items(), key=lambda x: x[1]["avg_ms"]) if by_tool else ("", {})
    return {
        "total_requests": total_requests,
        "average_duration_ms": round(sum(all_times) / len(all_times), 2),
        "by_tool": by_tool,
        "slowest_tool": slowest[0],
        "slowest_avg_ms": slowest[1].get("avg_ms", 0),
        "api_calls_count": len(_api_call_stats),
    }


def clear_performance_stats() -> None:
    """Reset in-memory performance stats (e.g. for tests)."""
    _perf_stats.clear()
    _api_call_stats.clear()


F = TypeVar("F", bound=Callable[..., Any])


def log_performance(func: F) -> F:
    """Decorator that logs tool execution time and optional api_calls. Works for async and sync."""

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        api_calls: list[dict[str, Any]] = []
        try:
            result = await func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            log_performance_metric(func.__name__, duration_ms, True, api_calls=api_calls or None)
            return result
        except Exception as e:
            logging.getLogger(__name__).exception(
                "Tool %s raised during performance logging",
                func.__name__,
            )
            duration_ms = (time.perf_counter() - start) * 1000
            log_performance_metric(
                func.__name__, duration_ms, False, api_calls=api_calls or None, error=str(e)
            )
            raise

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            log_performance_metric(func.__name__, duration_ms, True)
            return result
        except Exception as e:
            logging.getLogger(__name__).exception(
                "Sync tool %s raised during performance logging",
                func.__name__,
            )
            duration_ms = (time.perf_counter() - start) * 1000
            log_performance_metric(func.__name__, duration_ms, False, error=str(e))
            raise

    if inspect.iscoroutinefunction(func):
        return async_wrapper  # type: ignore[return-value]
    return sync_wrapper  # type: ignore[return-value]
