#!/usr/bin/env python3
"""Quick Planview API auth test using env from claude_desktop_config_corrected.json."""

import asyncio
import json
import os
import sys
from pathlib import Path

# Load config and set env before importing planview modules
config_path = Path(__file__).resolve().parent.parent / "claude_desktop_config_corrected.json"
if not config_path.exists():
    print(f"Config not found: {config_path}")
    sys.exit(1)

with open(config_path) as f:
    config = json.load(f)

env = config.get("mcpServers", {}).get("planview-portfolios-actions", {}).get("env", {})
for k, v in env.items():
    os.environ[k] = str(v)

# Now import (reads from os.environ via settings)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from planview_portfolios_mcp.oauth import get_oauth_token, get_okr_oauth_token
from planview_portfolios_mcp.exceptions import PlanviewAuthError, PlanviewError


async def main():
    print("Planview API auth test (using claude_desktop_config_corrected.json)\n")

    # 1. Portfolios REST API (OAuth)
    print("1. Portfolios API (PLANVIEW_*):")
    try:
        token = await get_oauth_token()
        print(f"   OK – got token ({token[:20]}...)")
    except (PlanviewAuthError, PlanviewError) as e:
        print(f"   FAIL – {e}")
        return 1

    # 2. OKR API (OAuth)
    print("2. OKR API (PLANVIEW_OKR_*):")
    try:
        okr_token = await get_okr_oauth_token()
        print(f"   OK – got token ({okr_token[:20]}...)")
    except (PlanviewAuthError, PlanviewError) as e:
        print(f"   FAIL – {e}")
        return 1

    print("\nAll Planview credentials accepted.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
