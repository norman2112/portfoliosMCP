"""FastMCP server for Planview Portfolios integration."""

import asyncio
import atexit

from fastmcp import FastMCP

from .client import close_client
from .config import settings
from .tools import (
    allocate_resource,
    create_project,
    get_project,
    get_resource,
    list_projects,
    list_resources,
    update_project,
)

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.server_name,
    version=settings.server_version,
)

# Register project management tools
mcp.tool()(list_projects)
mcp.tool()(get_project)
mcp.tool()(create_project)
mcp.tool()(update_project)

# Register resource management tools
mcp.tool()(list_resources)
mcp.tool()(get_resource)
mcp.tool()(allocate_resource)


def cleanup():
    """Clean up resources on server shutdown."""
    try:
        # Run async cleanup in a new event loop if needed
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule cleanup for later
            loop.create_task(close_client())
        else:
            # Run cleanup immediately
            asyncio.run(close_client())
    except Exception:
        # Best effort cleanup
        pass


# Register cleanup handler
atexit.register(cleanup)


def main() -> None:
    """Run the MCP server."""
    import asyncio

    asyncio.run(mcp.run())


if __name__ == "__main__":
    main()
