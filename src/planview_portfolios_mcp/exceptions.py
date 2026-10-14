"""Custom exceptions for Planview Portfolios MCP server."""

from typing import Any


class PlanviewError(Exception):
    """Base exception for all Planview-related errors."""

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "ok": False,
            "error": str(self),
            "error_type": type(self).__name__,
        }
        payload.update(self.details)
        return payload


class PlanviewAuthError(PlanviewError):
    """Authentication or authorization failure (401/403)."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "auth",
        hint: str | None = None,
        status_code: int | None = None,
        endpoint: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        merged = dict(details or {})
        merged.setdefault("code", code)
        if hint:
            merged.setdefault("hint", hint)
        if status_code is not None:
            merged.setdefault("status_code", status_code)
        if endpoint:
            merged.setdefault("endpoint", endpoint)
        super().__init__(message, details=merged)
        self.code = code
        self.hint = hint
        self.status_code = status_code
        self.endpoint = endpoint


class PlanviewNotFoundError(PlanviewError):
    """Resource not found (404)."""

    pass


class PlanviewValidationError(PlanviewError):
    """Input validation failure or bad request (400)."""

    pass


class PlanviewRateLimitError(PlanviewError):
    """Rate limit exceeded (429)."""

    pass


class PlanviewServerError(PlanviewError):
    """Server-side error (500+)."""

    pass


class PlanviewTimeoutError(PlanviewError):
    """Request timeout."""

    pass


class PlanviewConnectionError(PlanviewError):
    """Network connection failure."""

    pass
