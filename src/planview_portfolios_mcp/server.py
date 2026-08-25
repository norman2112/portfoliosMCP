"""MCP stdio server for Planview Portfolios (official MCP Python SDK)."""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from typing import Any

logging.basicConfig(stream=sys.stderr, level=logging.INFO, force=True)

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tool_registry import TOOL_NAMES, bind_arguments, build_tool_definitions

# Handle package imports (preferred) with a fallback for direct script execution.
try:
    from .client import close_client
    from .config import settings
    from .exceptions import PlanviewError
    from .logging_config import logger as app_logger
    from .soap_client import close_soap_client, get_soap_client
    from . import tools as _tools
except ImportError:  # pragma: no cover
    _current_dir = os.path.dirname(os.path.abspath(__file__))
    _src_dir = os.path.dirname(_current_dir)
    if _src_dir not in sys.path:
        sys.path.insert(0, _src_dir)

    from planview_portfolios_mcp.client import close_client
    from planview_portfolios_mcp.config import settings
    from planview_portfolios_mcp.exceptions import PlanviewError
    from planview_portfolios_mcp.logging_config import logger as app_logger
    from planview_portfolios_mcp.soap_client import close_soap_client, get_soap_client
    from planview_portfolios_mcp import tools as _tools


_COMPANION_SERVER_INSTRUCTIONS = (
    "Planview Portfolios — WRITE & ACTION tools (portfoliosMCP_v2). "
    "Call test_connection if authentication fails. "
    "Creating a project requires parent.structureCode from the Planview UI: "
    "the work-hierarchy ($Plan) folder one level above Primary Planning Level (PPL-1). "
    "Ask the user for that code. Do not guess. This server cannot list the Plan tree, "
    "portfolios, or the strategy hierarchy ($Strategy) — strategy is out of scope. "
    "Use manage_project to create/get/update/delete a project or list writable fields. "
    "Use inspect_work for a known project's WBS or to patch a work node. "
    "Use manage_tasks to add, read, or delete tasks. "
    "Use manage_financial_plan to read, discover, upsert, or copy financials "
    "(copy is dry-run until confirm=true). "
    "For listing portfolios, searching projects, strategy trees, resources, "
    "dependencies, and cross-tabs, use the companion Anvi Prod server."
)

TOOL_IMPLEMENTATIONS: dict[str, Callable[..., Awaitable[Any]]] = {
    "test_connection": _tools.test_connection,
    "manage_project": _tools.manage_project,
    "inspect_work": _tools.inspect_work,
    "manage_tasks": _tools.manage_tasks,
    "manage_financial_plan": _tools.manage_financial_plan,
}


def _make_server() -> Server:
    if set(TOOL_NAMES) != set(TOOL_IMPLEMENTATIONS.keys()):
        missing = set(TOOL_NAMES) - set(TOOL_IMPLEMENTATIONS.keys())
        extra = set(TOOL_IMPLEMENTATIONS.keys()) - set(TOOL_NAMES)
        raise RuntimeError(f"Tool registry mismatch. Missing: {missing}, extra: {extra}")

    server = Server(
        settings.server_name,
        version=settings.server_version,
        instructions=_COMPANION_SERVER_INSTRUCTIONS,
    )

    _tool_definitions = build_tool_definitions(TOOL_IMPLEMENTATIONS)

    @server.list_tools()
    async def _list_tools() -> list[types.Tool]:
        return _tool_definitions

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any] | None) -> dict[str, Any]:
        impl = TOOL_IMPLEMENTATIONS.get(name)
        if impl is None:
            raise ValueError(f"Unknown tool: {name}")
        bound = bind_arguments(impl, arguments)
        return await impl(**bound)

    return server


def cleanup() -> None:
    """Clean up resources on server shutdown."""
    try:
        try:
            from .performance import get_performance_summary

            if settings.mcp_performance_logging:
                summary = get_performance_summary()
                if summary.get("total_requests", 0) > 0:
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
            logging.getLogger(__name__).exception(
                "Performance summary logging failed during MCP cleanup"
            )
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(close_client())
            loop.create_task(close_soap_client())
        else:
            asyncio.run(close_client())
            asyncio.run(close_soap_client())
    except Exception:
        logging.getLogger(__name__).exception("MCP server cleanup failed")


atexit.register(cleanup)


async def run_mcp_server() -> None:
    """Run the MCP server over stdio (JSON-RPC)."""
    logger = logging.getLogger(__name__)
    if not settings.planview_ssl_verify and not settings.planview_ca_bundle:
        app_logger.warning(
            "SSL certificate verification is disabled (PLANVIEW_SSL_VERIFY=false). "
            "This is insecure and should only be used as a last resort."
        )
    logger.debug(
        "OAuth client configured: CLIENT_ID=%s, TENANT_ID=%s, API_URL=%s",
        "***" if settings.planview_client_id else "NOT SET",
        "***" if settings.planview_tenant_id else "NOT SET",
        settings.planview_api_url,
    )

    async def _warm_soap() -> None:
        try:
            async with get_soap_client():
                pass
        except PlanviewError as e:
            logger.debug("SOAP client warm skipped: %s", e)
        except Exception as e:
            logger.exception("Unexpected error during SOAP client warm (non-fatal)")
            logger.debug("SOAP client warm skipped: %s", e)

    await _warm_soap()

    server = _make_server()
    init = server.create_initialization_options()

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init, raise_exceptions=False)


def main() -> None:
    """Entry point for `python -m planview_portfolios_mcp.server` and console_scripts."""
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
