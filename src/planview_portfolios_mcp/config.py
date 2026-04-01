"""Configuration management for Planview Portfolios MCP server."""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    
    # OKRs API Configuration
    # OKRs API URL (optional, defaults to https://api-us.okrs.planview.com/api/rest)
    planview_okr_api_url: str | None = None
    # OKRs OAuth Token URL (optional, defaults to https://us.id.planview.com/io/v1/oauth2/token)
    # For EU environment, use: https://eu.id.planview.com/io/v1/oauth2/token
    planview_okr_oauth_url: str | None = None
    # OKRs API Bearer Token (optional - if not provided, will use OAuth credentials to auto-refresh)
    planview_okr_bearer_token: str = ""
    # OKRs OAuth credentials (for automatic token refresh - preferred over static bearer token)
    planview_okr_client_id: str = ""
    planview_okr_client_secret: str = ""

    # OAuth Configuration
    planview_client_id: str = ""
    planview_client_secret: str = ""
    use_oauth: bool = True  # Set to False to use static API key

    # API request settings
    api_timeout: int = 30
    max_retries: int = 3

    # SOAP API settings
    soap_timeout: int = 30
    soap_service_path: str = "/planview/services/TaskService.svc"

    # Server settings
    server_name: str = "planview-portfolios-actions"
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
