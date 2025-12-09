"""Entry point for running the MCP server as a module.

This allows the package to be run with:
    python -m planview_portfolios_mcp

This is required for FastMCP Cloud to properly handle relative imports.
"""

from .server import main

if __name__ == "__main__":
    main()

