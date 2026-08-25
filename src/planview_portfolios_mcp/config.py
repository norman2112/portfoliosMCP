"""Configuration management for Planview Portfolios MCP server."""

from urllib.parse import urlparse, urlunparse

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_planview_api_url(url: str) -> str:
    """Strip whitespace, drop a trailing slash, and lowercase the host.

    Planview pvcloud hosts are case-sensitive in practice; uppercase URLs
    cause OAuth failures that look like bad credentials.
    """
    raw = (url or "").strip()
    if not raw:
        return raw
    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").rstrip("/")
    if not parsed.scheme or not host:
        return raw.rstrip("/")
    return urlunparse(
        (parsed.scheme.lower(), host, path, parsed.params, parsed.query, parsed.fragment)
    )


class PlanviewSettings(BaseSettings):
    """Settings for Planview Portfolios API connection."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Planview API Configuration
    planview_api_url: str = "https://api.planview.com"
    planview_tenant_id: str = ""

    # OAuth Configuration
    planview_client_id: str = ""
    planview_client_secret: str = ""
    use_oauth: bool = True

    @field_validator(
        "planview_api_url",
        "planview_tenant_id",
        "planview_client_id",
        "planview_client_secret",
        mode="before",
    )
    @classmethod
    def _strip_credential_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("planview_api_url", mode="after")
    @classmethod
    def _normalize_api_url(cls, value: str) -> str:
        return normalize_planview_api_url(value)

    # API request settings
    api_timeout: int = 30
    max_retries: int = 3
    planview_ssl_verify: bool = True
    planview_ca_bundle: str | None = None

    # SOAP API settings
    soap_timeout: int = 30
    soap_service_path: str = "/planview/services/TaskService.svc"

    # Server settings
    server_name: str = "portfoliosMCP_v2"
    server_version: str = "0.1.0"

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    log_file: str | None = None

    # Performance monitoring (opt-in)
    mcp_performance_logging: bool = False
    mcp_request_timeout_seconds: int = 30
    mcp_soap_timeout_seconds: int = 60
    mcp_strip_null_values: bool = True
    mcp_verbose_responses: bool = False

    # Caching
    mcp_cache_enabled: bool = True
    mcp_cache_ttl_seconds: int = 3600


# Global settings instance
settings = PlanviewSettings()


def get_httpx_verify_setting() -> bool | str:
    """Resolve httpx verify setting from configured SSL options."""
    if settings.planview_ca_bundle:
        return settings.planview_ca_bundle
    if not settings.planview_ssl_verify:
        return False
    return True
