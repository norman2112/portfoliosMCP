"""MCP stdio server for Planview Portfolios (official MCP Python SDK)."""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
import sys
from collections.abc import Awaitable, Callable
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tool_registry import TOOL_NAMES, bind_arguments, build_tool_definitions

# Handle package imports (preferred) with a fallback for direct script execution.
try:
    from .client import close_client
    from .config import settings
    from .exceptions import PlanviewError
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
    from planview_portfolios_mcp.soap_client import close_soap_client, get_soap_client
    from planview_portfolios_mcp import tools as _tools


_COMPANION_SERVER_INSTRUCTIONS = (
    "Planview Portfolios — WRITE & ACTION tools. "
    "Use this server to CREATE, UPDATE, and DELETE projects, tasks, and financial plans, "
    "and to read OKRs. "
    "For READ operations like listing portfolios, searching projects, viewing strategies, "
    "resources, dependencies, and cross-tabs, use the companion 'Planview Portfolios US' (Beta MCP) server instead. "
    "This server covers: project CRUD, task CRUD (SOAP), financial plan read/write (SOAP), "
    "OKRs, work hierarchy node access, and field reference discovery. "
    "MCP server identifier: planview-portfolios-actions."
)

TOOL_IMPLEMENTATIONS: dict[str, Callable[..., Awaitable[Any]]] = {
    "oauth_ping": _tools.oauth_ping,
    "get_project_attributes": _tools.get_project_attributes,
    "get_work_attributes": _tools.get_work_attributes,
    "get_project": _tools.get_project,
    "create_project": _tools.create_project,
    "update_project": _tools.update_project,
    "delete_project": _tools.delete_project,
    "list_field_reference": _tools.list_field_reference,
    "get_project_wbs": _tools.get_project_wbs,
    "list_work": _tools.list_work,
    "update_work": _tools.update_work,
    "get_work": _tools.get_work,
    "create_task": _tools.create_task,
    "batch_create_tasks": _tools.batch_create_tasks,
    "batch_delete_tasks": _tools.batch_delete_tasks,
    "read_task": _tools.read_task,
    "delete_task": _tools.delete_task,
    "discover_financial_plan_info": _tools.discover_financial_plan_info,
    "load_financial_plan_from_reference": _tools.load_financial_plan_from_reference,
    "read_financial_plan": _tools.read_financial_plan,
    "upsert_financial_plan": _tools.upsert_financial_plan,
    "list_objectives": _tools.list_objectives,
    "get_key_results_for_objective": _tools.get_key_results_for_objective,
    "list_all_objectives_with_key_results": _tools.list_all_objectives_with_key_results,
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
    logger.debug(
        "OKR credentials configured: CLIENT_ID=%s, CLIENT_SECRET=%s, BEARER_TOKEN=%s",
        "***" if settings.planview_okr_client_id else "NOT SET",
        "***" if settings.planview_okr_client_secret else "NOT SET",
        "***" if settings.planview_okr_bearer_token else "NOT SET",
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
