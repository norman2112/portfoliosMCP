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

_servers = config.get("mcpServers", {})
_entry = _servers.get("portfoliosMCP_v2") or _servers.get("planview-portfolios-actions") or {}
env = _entry.get("env", {})
for k, v in env.items():
    os.environ[k] = str(v)

# Now import (reads from os.environ via settings)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from planview_portfolios_mcp.tools.ping import test_connection


async def main():
    print("Planview API connection test (using claude_desktop_config_corrected.json)\n")
    result = await test_connection()
    for check in result.get("checks", []):
        status = "OK" if check.get("ok") else "FAIL"
        print(f"  [{status}] {check.get('name')}: {check.get('detail')}")
    if result.get("ok"):
        print("\nConnected.")
        return 0
    error = result.get("error") or {}
    print(f"\nFailed: {error.get('error') or error.get('message') or error}")
    if error.get("hint"):
        print(f"Hint: {error['hint']}")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
