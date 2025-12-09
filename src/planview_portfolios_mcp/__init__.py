"""Planview Portfolios MCP Server.

An MCP server for integrating with Planview Portfolios, providing tools for
project/portfolio management and resource management.
"""

__version__ = "0.1.0"

# Export the mcp instance for FastMCP Cloud
# This allows FastMCP Cloud to import: from planview_portfolios_mcp import mcp
from .server import mcp

__all__ = ["mcp", "__version__"]
