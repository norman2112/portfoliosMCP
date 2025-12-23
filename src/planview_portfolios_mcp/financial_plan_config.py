"""Configuration for financial plan account and period keys.

This module provides instance-specific account and period keys for different
Planview environments. Account keys vary by instance, so they need to be
configured per environment.

Usage:
    from planview_portfolios_mcp.financial_plan_config import get_account_key
    
    account_key = get_account_key("benefits")  # Gets instance-specific key
"""

import logging
from typing import Any

from .config import settings

logger = logging.getLogger(__name__)

# Instance-specific account configurations
# Map instance URL patterns to account keys
# Use environment variables or config files to override per instance
INSTANCE_ACCOUNTS: dict[str, dict[str, str]] = {
    # Default/fallback configuration
    "default": {
        "benefits": "key://2/$Account/2689",
        "capex_hardware": "key://2/$Account/3555",
        "capex_software": "key://2/$Account/3651",
        "capex_professional_services": "key://2/$Account/3652",
        "capex_other": "key://2/$Account/3653",
        "expense_hardware": "key://2/$Account/3513",
        "labor": "key://2/$Account/11086",
    },
    # scdemo520.pvcloud.com specific
    "scdemo520": {
        "benefits": "key://2/$Account/2689",
        "capex_hardware": "key://2/$Account/3555",
        "capex_software": "key://2/$Account/3651",
        "capex_professional_services": "key://2/$Account/3652",
        "capex_other": "key://2/$Account/3653",
        "expense_hardware": "key://2/$Account/3513",
        "labor": "key://2/$Account/11086",
    },
}

# Instance-specific period configurations
INSTANCE_PERIODS: dict[str, dict[str, str]] = {
    "default": {
        "dec_2025": "key://16/170",
    },
    "scdemo520": {
        "dec_2025": "key://16/170",
    },
}

# Account type descriptions for better error messages
ACCOUNT_DESCRIPTIONS: dict[str, str] = {
    "benefits": "Benefits",
    "capex_hardware": "Capital - Hardware",
    "capex_software": "Capital - Software",
    "capex_professional_services": "Capital - Professional Services",
    "capex_other": "Capital - Other",
    "expense_hardware": "Expense - Hardware",
    "labor": "Labor",
}


def _get_instance_key() -> str:
    """Get the instance key from API URL.
    
    Returns:
        Instance identifier (e.g., 'scdemo520') or 'default'
    """
    api_url = settings.planview_api_url or ""
    
    # Extract instance identifier from URL
    # e.g., https://scdemo520.pvcloud.com/polaris -> scdemo520
    for instance_key in INSTANCE_ACCOUNTS.keys():
        if instance_key == "default":
            continue
        if instance_key in api_url:
            return instance_key
    
    # Check for common patterns
    if "pvcloud.com" in api_url:
        # Try to extract subdomain
        try:
            # https://scdemo520.pvcloud.com -> scdemo520
            parts = api_url.split("//")[1].split(".")[0]
            if parts and parts not in ["https:", "http:"]:
                return parts
        except (IndexError, AttributeError):
            pass
    
    return "default"


def get_account_key(account_type: str, instance: str | None = None) -> str:
    """Get account key for a specific account type.
    
    Args:
        account_type: Type of account (e.g., 'benefits', 'capex_hardware')
        instance: Optional instance key. If not provided, auto-detects from settings.
        
    Returns:
        Account key URI (e.g., 'key://2/$Account/2689')
        
    Raises:
        ValueError: If account_type is unknown for the instance
        
    Example:
        >>> get_account_key("benefits")
        'key://2/$Account/2689'
        >>> get_account_key("capex_hardware")
        'key://2/$Account/3555'
    """
    instance_key = instance or _get_instance_key()
    
    # Get accounts for this instance
    instance_accounts = INSTANCE_ACCOUNTS.get(instance_key, {})
    
    # Fallback to default if account not found in instance-specific config
    if account_type not in instance_accounts:
        default_accounts = INSTANCE_ACCOUNTS.get("default", {})
        if account_type not in default_accounts:
            available = list(ACCOUNT_DESCRIPTIONS.keys())
            raise ValueError(
                f"Unknown account type: '{account_type}'. "
                f"Available types: {available}. "
                f"Instance: {instance_key}"
            )
        account_key = default_accounts[account_type]
        logger.warning(
            f"Using default account key for '{account_type}' "
            f"(not configured for instance '{instance_key}')"
        )
        return account_key
    
    return instance_accounts[account_type]


def get_period_key(period_name: str, instance: str | None = None) -> str:
    """Get period key for a specific period name.
    
    Args:
        period_name: Name of period (e.g., 'dec_2025')
        instance: Optional instance key. If not provided, auto-detects from settings.
        
    Returns:
        Period key URI (e.g., 'key://16/170')
        
    Raises:
        ValueError: If period_name is unknown for the instance
        
    Example:
        >>> get_period_key("dec_2025")
        'key://16/170'
    """
    instance_key = instance or _get_instance_key()
    
    # Get periods for this instance
    instance_periods = INSTANCE_PERIODS.get(instance_key, {})
    
    # Fallback to default
    if period_name not in instance_periods:
        default_periods = INSTANCE_PERIODS.get("default", {})
        if period_name not in default_periods:
            available = list(INSTANCE_PERIODS.get("default", {}).keys())
            raise ValueError(
                f"Unknown period name: '{period_name}'. "
                f"Available periods: {available}. "
                f"Instance: {instance_key}"
            )
        period_key = default_periods[period_name]
        logger.warning(
            f"Using default period key for '{period_name}' "
            f"(not configured for instance '{instance_key}')"
        )
        return period_key
    
    return instance_periods[period_name]


def get_account_description(account_type: str) -> str:
    """Get human-readable description for an account type.
    
    Args:
        account_type: Type of account
        
    Returns:
        Description string (e.g., 'Benefits', 'Capital - Hardware')
    """
    return ACCOUNT_DESCRIPTIONS.get(account_type, account_type.replace("_", " ").title())


def list_available_accounts(instance: str | None = None) -> dict[str, dict[str, Any]]:
    """List all available account types with their keys and descriptions.
    
    Args:
        instance: Optional instance key. If not provided, auto-detects from settings.
        
    Returns:
        Dict mapping account_type to {key, description}
        
    Example:
        >>> accounts = list_available_accounts()
        >>> accounts["benefits"]
        {'key': 'key://2/$Account/2689', 'description': 'Benefits'}
    """
    instance_key = instance or _get_instance_key()
    instance_accounts = INSTANCE_ACCOUNTS.get(instance_key, INSTANCE_ACCOUNTS.get("default", {}))
    
    return {
        account_type: {
            "key": account_key,
            "description": get_account_description(account_type),
        }
        for account_type, account_key in instance_accounts.items()
    }


def list_available_periods(instance: str | None = None) -> dict[str, str]:
    """List all available period names with their keys.
    
    Args:
        instance: Optional instance key. If not provided, auto-detects from settings.
        
    Returns:
        Dict mapping period_name to period_key
    """
    instance_key = instance or _get_instance_key()
    instance_periods = INSTANCE_PERIODS.get(instance_key, INSTANCE_PERIODS.get("default", {}))
    return dict(instance_periods)

