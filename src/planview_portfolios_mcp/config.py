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
    planview_api_key: str = ""
    planview_tenant_id: str = ""

    # API request settings
    api_timeout: int = 30
    max_retries: int = 3

    # Server settings
    server_name: str = "planview-portfolios-mcp"
    server_version: str = "0.1.0"

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    log_file: str | None = None


# Global settings instance
settings = PlanviewSettings()
