"""FastMCP server for Planview Portfolios integration."""

import asyncio
import atexit
import sys
import os

from fastmcp import FastMCP

# Handle package imports (preferred) with a fallback for direct script execution.
try:
    from .client import close_client
    from .config import settings
    from .soap_client import close_soap_client, get_soap_client
    from . import tools as _tools
except ImportError:  # pragma: no cover
    # If running as a script, add parent directories to path for absolute imports.
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _src_dir = os.path.dirname(_current_dir)
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

    from planview_portfolios_mcp.client import close_client
    from planview_portfolios_mcp.config import settings
    from planview_portfolios_mcp.soap_client import close_soap_client, get_soap_client
    from planview_portfolios_mcp import tools as _tools

# Pull tool functions into module namespace for FastMCP registration.
batch_create_tasks = _tools.batch_create_tasks
batch_delete_tasks = _tools.batch_delete_tasks
create_project = _tools.create_project
create_task = _tools.create_task
delete_task = _tools.delete_task
discover_financial_plan_info = _tools.discover_financial_plan_info
load_financial_plan_from_reference = _tools.load_financial_plan_from_reference
get_key_results_for_objective = _tools.get_key_results_for_objective
get_project = _tools.get_project
get_project_attributes = _tools.get_project_attributes
get_work = _tools.get_work
get_work_attributes = _tools.get_work_attributes
list_all_objectives_with_key_results = _tools.list_all_objectives_with_key_results
list_objectives = _tools.list_objectives
list_projects = _tools.list_projects
get_project_wbs = _tools.get_project_wbs
list_work = _tools.list_work
update_work = _tools.update_work
oauth_ping = _tools.oauth_ping
read_financial_plan = _tools.read_financial_plan
read_task = _tools.read_task
update_project = _tools.update_project
list_field_reference = _tools.list_field_reference
upsert_financial_plan = _tools.upsert_financial_plan

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
mcp.tool()(list_field_reference)
mcp.tool()(get_project_wbs)
mcp.tool()(list_work)
mcp.tool()(update_work)
mcp.tool()(get_work)
# Task service tools (SOAP API)
mcp.tool()(create_task)
mcp.tool()(batch_create_tasks)
mcp.tool()(batch_delete_tasks)
mcp.tool()(read_task)
mcp.tool()(delete_task)
# Financial plan service tools (SOAP API)
mcp.tool()(discover_financial_plan_info)
mcp.tool()(load_financial_plan_from_reference)
mcp.tool()(read_financial_plan)
mcp.tool()(upsert_financial_plan)
# OKRs tools (REST API)
mcp.tool()(list_objectives)
mcp.tool()(get_key_results_for_objective)
mcp.tool()(list_all_objectives_with_key_results)


def cleanup():
    """Clean up resources on server shutdown."""
    try:
        # Log performance summary if enabled and we have stats
        try:
            from .performance import get_performance_summary
            from .config import settings
            if settings.mcp_performance_logging:
                summary = get_performance_summary()
                if summary.get("total_requests", 0) > 0:
                    import logging
                    log = logging.getLogger("mcp.performance")
                    log.info(
                        "MCP Server Performance Summary: total_requests=%s avg_ms=%s slowest_tool=%s slowest_avg_ms=%s api_calls=%s",
                        summary.get("total_requests"),
                        summary.get("average_duration_ms"),
                        summary.get("slowest_tool"),
                        summary.get("slowest_avg_ms"),
                        summary.get("api_calls_count", 0),
                    )
        except Exception:
            pass
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
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(
        f"OKR credentials configured: "
        f"CLIENT_ID={'***' if settings.planview_okr_client_id else 'NOT SET'}, "
        f"CLIENT_SECRET={'***' if settings.planview_okr_client_secret else 'NOT SET'}, "
        f"BEARER_TOKEN={'***' if settings.planview_okr_bearer_token else 'NOT SET'}"
    )
    # Warm TaskService SOAP client so first create_project (and its batch_create_tasks) is fast
    async def _warm_soap():
        try:
            async with get_soap_client() as _:
                pass
        except Exception as e:
            logger.debug("SOAP client warm skipped: %s", e)

    try:
        asyncio.run(_warm_soap())
    except Exception:
        pass
    mcp.run()


if __name__ == "__main__":
    main()
