#!/usr/bin/env python3
"""Helper script to test OAuth token retrieval for Planview Portfolios API."""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import the package
sys.path.insert(0, str(Path(__file__).parent / "src"))

from planview_portfolios_mcp.config import settings
from planview_portfolios_mcp.oauth import get_oauth_token


async def main():
    """Test OAuth token retrieval."""
    print("Planview Portfolios OAuth Token Test")
    print("=" * 50)

    # Check configuration
    if not settings.planview_client_id:
        print("ERROR: PLANVIEW_CLIENT_ID not set")
        print("Set it in your .env file or environment variables")
        sys.exit(1)

    if not settings.planview_client_secret:
        print("ERROR: PLANVIEW_CLIENT_SECRET not set")
        print("Set it in your .env file or environment variables")
        sys.exit(1)

    print(f"API URL: {settings.planview_api_url}")
    print(f"Client ID: {settings.planview_client_id[:8]}...")
    print(f"Tenant ID: {settings.planview_tenant_id}")
    print()

    try:
        print("Requesting OAuth token...")
        token = await get_oauth_token()
        print("✅ Successfully obtained OAuth token!")
        print()
        print(f"Token: {token[:50]}...")
        print()
        print("You can now use this token for API requests.")
        print("The token is cached and will be automatically refreshed when it expires.")
    except Exception as e:
        print(f"❌ Failed to get OAuth token: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

