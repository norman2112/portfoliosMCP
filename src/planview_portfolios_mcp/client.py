"""Shared HTTP client for Planview API interactions with retry logic."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncContextManager

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from .config import settings
from .exceptions import (
    PlanviewAuthError,
    PlanviewConnectionError,
    PlanviewError,
    PlanviewNotFoundError,
    PlanviewRateLimitError,
    PlanviewServerError,
    PlanviewTimeoutError,
    PlanviewValidationError,
)

logger = logging.getLogger(__name__)


class PlanviewClient:
    """Manages HTTP client lifecycle with connection pooling."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> httpx.AsyncClient:
        """Create and return HTTP client with connection pooling."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.planview_api_url,
                timeout=settings.api_timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30,
                ),
                headers={
                    "Authorization": f"Bearer {settings.planview_api_key}",
                    "X-Tenant-Id": settings.planview_tenant_id,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Keep client alive for reuse across requests."""
        # Don't close - reuse across requests
        pass

    async def close(self):
        """Explicitly close client (call on server shutdown)."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global client instance
_client = PlanviewClient()


@asynccontextmanager
async def get_client() -> AsyncContextManager[httpx.AsyncClient]:
    """Get shared HTTP client with connection pooling."""
    async with _client as client:
        yield client


async def close_client():
    """Close shared HTTP client (call on shutdown)."""
    await _client.close()


def should_retry_status(status_code: int) -> bool:
    """Determine if HTTP status code should trigger retry."""
    return status_code in {429, 502, 503, 504}


def create_retry_decorator():
    """Create retry decorator with exponential backoff."""
    return retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError,
            )
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


@create_retry_decorator()
async def make_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """Make HTTP request with automatic retry on transient failures.

    Args:
        client: HTTP client instance
        method: HTTP method (GET, POST, PATCH, etc.)
        url: Request URL path (relative to base_url)
        **kwargs: Additional arguments passed to client.request()

    Returns:
        HTTP response

    Raises:
        PlanviewAuthError: Authentication failure (401/403)
        PlanviewNotFoundError: Resource not found (404)
        PlanviewValidationError: Invalid request (400)
        PlanviewRateLimitError: Rate limit exceeded (429)
        PlanviewServerError: Server error (500+)
        PlanviewTimeoutError: Request timeout
        PlanviewConnectionError: Network connection failure
    """
    try:
        response = await client.request(method, url, **kwargs)

        # Check if status code warrants retry
        if should_retry_status(response.status_code):
            raise httpx.HTTPStatusError(
                message=f"Retryable status: {response.status_code}",
                request=response.request,
                response=response,
            )

        # Raise for other HTTP errors
        response.raise_for_status()
        return response

    except httpx.TimeoutException as e:
        raise PlanviewTimeoutError(
            f"Request timed out after {settings.api_timeout}s: {str(e)}"
        ) from e
    except httpx.NetworkError as e:
        raise PlanviewConnectionError(
            f"Network error connecting to Planview API: {str(e)}"
        ) from e
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise PlanviewAuthError("Invalid API key or token expired") from e
        elif e.response.status_code == 403:
            raise PlanviewAuthError(
                f"Permission denied accessing {e.request.url.path}"
            ) from e
        elif e.response.status_code == 404:
            raise PlanviewNotFoundError(
                f"Resource not found: {e.request.url.path}"
            ) from e
        elif e.response.status_code == 400:
            try:
                error_detail = e.response.json().get("message", str(e))
            except Exception:
                error_detail = str(e)
            raise PlanviewValidationError(f"Invalid request: {error_detail}") from e
        elif e.response.status_code == 429:
            raise PlanviewRateLimitError(
                "Rate limit exceeded. Please retry after a delay."
            ) from e
        elif e.response.status_code >= 500:
            raise PlanviewServerError(
                f"Server error ({e.response.status_code}): {str(e)}"
            ) from e
        else:
            raise PlanviewError(f"HTTP {e.response.status_code}: {str(e)}") from e
