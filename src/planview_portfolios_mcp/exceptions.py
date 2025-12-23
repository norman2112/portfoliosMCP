"""Custom exceptions for Planview Portfolios MCP server."""


class PlanviewError(Exception):
    """Base exception for all Planview-related errors."""

    pass


class PlanviewAuthError(PlanviewError):
    """Authentication or authorization failure (401/403)."""

    pass


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
