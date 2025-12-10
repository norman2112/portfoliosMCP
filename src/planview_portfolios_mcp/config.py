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
    planview_api_key: str = ""  # Deprecated: Use OAuth instead
    planview_tenant_id: str = ""

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
    server_name: str = "planview-portfolios-mcp"
    server_version: str = "0.1.0"

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    log_file: str | None = None


# Global settings instance
settings = PlanviewSettings()
