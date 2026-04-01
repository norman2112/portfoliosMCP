# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **local** Model Context Protocol (MCP) server for Planview Portfolios, built with the official `mcp` Python SDK (stdio transport). It exposes **write & action tools** — project CRUD, task management (SOAP), financial plans (SOAP), OKRs, and work hierarchy access — that complement the read-only **Beta MCP** server (`Planview Portfolios US`) hosted by Planview.

### Two-Server Architecture

| Server | Role | Tools | Transport |
|--------|------|-------|-----------|
| **Beta MCP** (`Planview Portfolios US`) | Read — portfolios, search, cross-tabs, strategies, resources, dependencies, hierarchy trees | 29 | Planview-hosted (remote) |
| **Local MCP** (`planview-portfolios-actions`) | Write — create/update/delete projects, SOAP tasks, financial plans, OKRs, work node access | 24 | Local stdio |

**Routing rule:** All tool descriptions include `[LOCAL — ...]` hints. If a hint says "use Beta MCP's X instead," prefer that tool for the read path. This server owns all writes and anything SOAP/OKR/financial-plan related.

## Development Commands

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e .
cp .env.example .env      # Add Planview API credentials
```

### Running the Server
```bash
# Standard (stdio transport — used by Claude Code)
python -m planview_portfolios_mcp

# Alternative entry points
python -m planview_portfolios_mcp.server
planview-portfolios-actions  # console script if installed
```

The server speaks MCP JSON-RPC over stdin/stdout. It registers 24 tools on startup.

### Testing
```bash
pytest                              # Run all tests
pytest -v                           # Verbose
pytest tests/test_filename.py       # Specific file
pytest --cov=src/planview_portfolios_mcp  # With coverage
```

### Code Quality
```bash
black src/ && ruff check src/ && mypy src/
```

## Architecture

### Core Components

**server.py**: MCP Server initialization (`Server(settings.server_name)` — default `planview-portfolios-actions`), `@server.list_tools()` and `@server.call_tool()` handlers, stdio transport via `stdio_server()`. Includes SOAP warm-up on startup and `atexit` cleanup.

**tool_registry.py**: Central registry for all 24 tools. Contains `ROUTING_HINTS` (per-tool `[LOCAL — ...]` prefixes), `INPUT_SCHEMAS` (JSON Schema for each tool), `build_tool_definitions()` (returns `Tool` objects), `bind_arguments()` (maps incoming args to function params), and `TOOL_NAMES` ordering.

**config.py**: Centralized configuration using Pydantic Settings. The `PlanviewSettings` class loads from `.env` and provides validated config. A global `settings` instance is imported throughout.

**client.py**: Shared HTTP client with connection pooling, automatic retry (exponential backoff for 429, 502, 503, 504), and error handling. Provides `get_client()` context manager.

**soap_client.py**: SOAP client (zeep) with retry logic. Provides `get_soap_client()` context manager and `make_soap_request()` helper.

**exceptions.py**: Custom exception hierarchy for Planview API errors (auth, validation, rate limiting, server errors).

**models.py**: Pydantic models for input validation. Validates date ranges, numeric constraints, required fields.

**logging_config.py**: Structured logging with JSON formatter support.

**tools/**: Tool implementations organized by domain:
- `projects.py`: Project CRUD + WBS + field reference
- `work.py`: Work hierarchy read/update
- `tasks.py`: Task CRUD via SOAP (TaskService)
- `financial_plan.py`: Financial plan read/write via SOAP (FinancialPlanService)
- `okrs.py`: OKR objectives and key results
- `ping.py`: OAuth health check
- `resources.py`: Shared REST helpers for `/public-api/v1/resources` (list/get/allocate)—kept for scripts, tests, or future use; **not** registered in `server.py` / `tool_registry.py`, so they never appear in MCP `list_tools`.

### Tool Pattern

All tools follow a consistent async pattern:
1. Accept typed parameters directly (no `ctx` — this is not FastMCP)
2. Use Pydantic models from `models.py` for input validation
3. Use `get_client()` for REST or `get_soap_client()` for SOAP
4. Return typed data (`dict[str, Any]` or `list[dict[str, Any]]`)
5. Raise custom exceptions from `exceptions.py`

### Adding a New Tool
1. Create async function in the appropriate `tools/` module
2. Add entry to `ROUTING_HINTS` in `tool_registry.py`
3. Add entry to `INPUT_SCHEMAS` in `tool_registry.py`
4. Add function name to `TOOL_NAMES` in `tool_registry.py`
5. Wire into `TOOL_IMPLEMENTATIONS` dict in `server.py`
6. Add tests

### Authentication Flow

OAuth 2.0 `client_credentials` flow with automatic token management:
- Tokens fetched on first HTTP client creation
- Cached in memory, reused until expiration (60 minutes)
- Auto-refreshed on expiry or 401
- Headers: `Authorization: Bearer {token}` + `X-Tenant-Id: {tenant_id}`

Required env vars:
- `PLANVIEW_API_URL`: Base URL including `/polaris` (e.g., `https://scdemo520.pvcloud.com/polaris`)
- `PLANVIEW_CLIENT_ID`: OAuth client ID
- `PLANVIEW_CLIENT_SECRET`: OAuth client secret
- `PLANVIEW_TENANT_ID`: Tenant ID

### Claude Code Config

```json
{
  "mcpServers": {
    "planview-portfolios-actions": {
      "command": "/path/to/venv/bin/python3",
      "args": ["-m", "planview_portfolios_mcp"],
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret",
        "PLANVIEW_TENANT_ID": "your_tenant_id",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

## API Integration Notes

### REST API
- Base URL pattern: `{PLANVIEW_API_URL}/public-api/v1/{endpoint}`
- Date format: ISO 8601 (`YYYY-MM-DD`)
- Case-sensitive attribute names and values

### SOAP API
- TaskService: `{PLANVIEW_API_URL}/planview/services/TaskService.svc`
- FinancialPlanService: `{PLANVIEW_API_URL}/planview/services/FinancialPlanService.svc`
- Service binding: `ITaskService3` (latest version)
- Same OAuth tokens as REST
- Key URI formats: `key://2/$Plan/12345` (direct), `search://2/$Plan?description=Name` (search), `ekey://2/namespace/id` (external)
- Response fields may be null even on success — this is normal SOAP behavior
- Task updates not exposed (`ITaskService3.Update` doesn't serialize reliably with zeep)

### Tool-to-API Mapping

**REST:**
- `get_project` → `GET /projects/{id}`
- `create_project` → `POST /projects`
- `update_project` → `PATCH /projects/{id}`
- `delete_project` → `DELETE /projects/{id}`
- `list_work` → `GET /work` (with filter)
- `get_work` → `GET /work/{id}`
- `update_work` → `PATCH /work/{id}`

**SOAP:**
- `create_task` / `batch_create_tasks` → `ITaskService3.Create`
- `read_task` → `ITaskService3.Read`
- `delete_task` / `batch_delete_tasks` → `ITaskService3.Delete`
- `read_financial_plan` → `IFinancialPlanService.Read`
- `upsert_financial_plan` → `IFinancialPlanService.Upsert`
- `load_financial_plan_from_reference` → `IFinancialPlanService.Read` + `Upsert`

**OKRs (REST):**
- `list_objectives` → `GET /okr/objectives`
- `list_all_objectives_with_key_results` → `GET /okr/objectives` + `/okr/objectives/{id}/key-results`
- `get_key_results_for_objective` → `GET /okr/objectives/{id}/key-results`

## Type Annotations

Modern Python 3.10+ syntax: `str | None`, `list[dict[str, Any]]`.

## Project Structure

```
src/planview_portfolios_mcp/
├── server.py           # MCP Server (stdio) + tool routing
├── tool_registry.py    # Tool definitions, routing hints, input schemas
├── __main__.py         # Entry point
├── config.py           # Pydantic Settings
├── client.py           # HTTP client + retry
├── soap_client.py      # SOAP client (zeep) + retry
├── exceptions.py       # Exception hierarchy
├── models.py           # Input validation
├── logging_config.py   # Structured logging
└── tools/
    ├── projects.py
    ├── work.py
    ├── tasks.py
    ├── financial_plan.py
    ├── okrs.py
    ├── ping.py
    ├── resources.py    # internal /resources REST helpers only
    └── __init__.py
```