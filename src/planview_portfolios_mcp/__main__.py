"""Entry point for running the MCP server as a module (stdio JSON-RPC).

The process advertises MCP server name ``planview-portfolios-actions`` to clients.

    python -m planview_portfolios_mcp
"""

from .server import main

if __name__ == "__main__":
    main()

