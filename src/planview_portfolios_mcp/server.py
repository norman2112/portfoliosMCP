"""FastMCP server for Planview Portfolios integration."""

import asyncio
import atexit
import sys
import os

from fastmcp import FastMCP

# Handle both package and direct execution contexts
# If running as a script, add parent directories to path
if __name__ == "__main__" or not __package__:
    # Add src directory to path for absolute imports
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _src_dir = os.path.dirname(_current_dir)
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)
    # Use absolute imports when not in package context
    from planview_portfolios_mcp.client import close_client
    from planview_portfolios_mcp.config import settings
    from planview_portfolios_mcp.soap_client import close_soap_client
    from planview_portfolios_mcp.tools import (
        allocate_resource,
        batch_create_tasks,
        batch_update_tasks,
        create_project,
        create_task,
        delete_task,
        discover_financial_plan_info,
        get_key_results_for_objective,
        get_project,
        get_project_attributes,
        get_resource,
        get_work,
        get_work_attributes,
        list_all_objectives_with_key_results,
        list_objectives,
        list_projects,
        list_resources,
        list_work,
        oauth_ping,
        read_financial_plan,
        read_task,
        update_project,
        update_task,
        upsert_financial_plan,
    )
else:
    # Use relative imports when in package context
    from .client import close_client
    from .config import settings
    from .soap_client import close_soap_client
    from .tools import (
        allocate_resource,
        batch_create_tasks,
        batch_update_tasks,
        create_project,
        create_task,
        delete_task,
        discover_financial_plan_info,
        get_key_results_for_objective,
        get_project,
        get_project_attributes,
        get_resource,
        get_work,
        get_work_attributes,
        list_all_objectives_with_key_results,
        list_objectives,
        list_projects,
        list_resources,
        list_work,
        oauth_ping,
        read_financial_plan,
        read_task,
        update_project,
        update_task,
        upsert_financial_plan,
    )

# Initialize FastMCP server
mcp = FastMCP(
    name=settings.server_name,
    version=settings.server_version,
)

# Register tools
mcp.tool()(oauth_ping)
mcp.tool()(get_project_attributes)
mcp.tool()(get_work_attributes)
mcp.tool()(list_projects)
mcp.tool()(get_project)
mcp.tool()(create_project)
mcp.tool()(update_project)
mcp.tool()(list_work)
mcp.tool()(get_work)
mcp.tool()(list_resources)
mcp.tool()(get_resource)
mcp.tool()(allocate_resource)
# Task service tools (SOAP API)
mcp.tool()(create_task)
mcp.tool()(batch_create_tasks)
mcp.tool()(read_task)
mcp.tool()(update_task)
mcp.tool()(batch_update_tasks)
mcp.tool()(delete_task)
# Financial plan service tools (SOAP API)
mcp.tool()(discover_financial_plan_info)
mcp.tool()(read_financial_plan)
mcp.tool()(upsert_financial_plan)
# OKRs tools (REST API)
mcp.tool()(list_objectives)
mcp.tool()(get_key_results_for_objective)
mcp.tool()(list_all_objectives_with_key_results)


def cleanup():
    """Clean up resources on server shutdown."""
    try:
        # Run async cleanup in a new event loop if needed
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule cleanup for later
            loop.create_task(close_client())
            loop.create_task(close_soap_client())
        else:
            # Run cleanup immediately
            asyncio.run(close_client())
            asyncio.run(close_soap_client())
    except Exception:
        # Best effort cleanup
        pass


# Register cleanup handler
atexit.register(cleanup)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
