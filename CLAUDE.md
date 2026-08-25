# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **local** Model Context Protocol (MCP) server for Planview Portfolios, built with the official `mcp` Python SDK (stdio transport). It exposes **write & action tools** — project CRUD, task management (SOAP), financial plans (SOAP), and work hierarchy access — that complement the read-only **Anvi Prod** server.

### Two-Server Architecture

| Server | Role | Tools | Transport |
|--------|------|-------|-----------|
| **Anvi Prod** | Read — portfolios, search, cross-tabs, strategies, resources, dependencies, hierarchy trees | read catalog | Remote |
| **Local MCP** (`portfoliosMCP_v2`) | Write — create/update/delete projects, SOAP tasks, financial plans, work node access | 5 | Local stdio |

**Routing rule:** All tool descriptions include `[LOCAL — ...]` hints. If a hint says "use Anvi Prod's X instead," prefer that tool for the read path. This server owns all writes and anything SOAP/financial-plan related.

**Create requires a UI parent code.** `manage_project` create needs `parent.structureCode` from the Planview UI: the **work hierarchy** ($Plan) folder one level above Primary Planning Level (PPL-1). This MCP cannot list the Plan tree. **Strategy hierarchy (`$Strategy`) is out of scope** — use Anvi Prod for strategy reads.

**Financial discover:** returns `accounts` / `periods` as `[{key, description}]` plus bare key lists. Period ids are not contiguous across fiscal years — never invent by incrementing. Region is optional on create; tenant `InvalidDefaultValues` for optional defaults is `demo_safe` — do not treat as create failure.

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
portfoliosMCP_v2  # console script if installed
```

The server speaks MCP JSON-RPC over stdin/stdout. It registers 5 job-shaped tools on startup.

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

**server.py**: MCP Server initialization (`Server(settings.server_name)` — default `portfoliosMCP_v2`), `@server.list_tools()` and `@server.call_tool()` handlers, stdio transport via `stdio_server()`. Includes SOAP warm-up on startup and `atexit` cleanup.

**tool_registry.py**: Central registry for the 5 model-facing tools. Contains `ROUTING_HINTS` (per-tool `[LOCAL — ...]` prefixes), `INPUT_SCHEMAS` (JSON Schema for each tool), `build_tool_definitions()` (returns `Tool` objects), `bind_arguments()` (maps incoming args to function params), and `TOOL_NAMES` ordering.

**config.py**: Centralized configuration using Pydantic Settings. The `PlanviewSettings` class loads from `.env` and provides validated config. A global `settings` instance is imported throughout.

**client.py**: Shared HTTP client with connection pooling, automatic retry (exponential backoff for 429, 502, 503, 504), and error handling. Provides `get_client()` context manager.

**soap_client.py**: SOAP client (zeep) with retry logic. Provides `get_soap_client()` context manager and `make_soap_request()` helper.

**exceptions.py**: Custom exception hierarchy for Planview API errors (auth, validation, rate limiting, server errors).

**models.py**: Pydantic models for input validation. Validates date ranges, numeric constraints, required fields.

**logging_config.py**: Structured logging with JSON formatter support.

**tools/**: Job-shaped MCP tools plus internal endpoint implementations:
- `ping.py`: `test_connection` OAuth diagnostic (registered)
- `manage_project.py` / `inspect_work.py` / `manage_tasks.py` / `manage_financial_plan.py`: registered dispatchers (`action` param)
- `projects.py`: Project CRUD + WBS + field reference (internal)
- `work.py`: Work hierarchy read/update (internal)
- `tasks.py`: Task CRUD via SOAP TaskService (internal)
- `financial_plan.py`: Financial plan read/write via SOAP FinancialPlanService (internal)
- `resources.py`: Shared REST helpers for `/public-api/v1/resources` (list/get/allocate)—kept for scripts, tests, or future use; **not** registered

### Tool Pattern

All tools follow a consistent async pattern:
1. Accept typed parameters directly (no `ctx` — this is not FastMCP)
2. Use Pydantic models from `models.py` for input validation
3. Use `get_client()` for REST or `get_soap_client()` for SOAP
4. Return typed data (`dict[str, Any]` or `list[dict[str, Any]]`)
5. Raise custom exceptions from `exceptions.py`

### Adding a New Tool
Prefer a new `action` on an existing job tool over a new `list_tools` name. If a new tool is required:
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
    "portfoliosMCP_v2": {
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

**Registered tools (model-facing):**
- `test_connection` → `POST /oauth/token` then `GET /oauth/ping`
- `manage_project` `create|get|update|delete|fields` → REST `/projects` (+ SOAP task seed on create)
- `inspect_work` `wbs|get|list|update` → REST `/work` (WBS composes list + tree)
- `manage_tasks` `create|read|delete` → SOAP `ITaskService3` Create/Read/Delete (lists; batch is internal)
- `manage_financial_plan` `read|discover|upsert|copy` → SOAP `IFinancialPlanService` Read/Upsert

**Internal helpers (not in `list_tools`):**
- REST: `GET/POST/PATCH/DELETE /projects/{id}`, `GET /work`, `GET/PATCH /work/{id}`
- SOAP: `ITaskService3.Create|Read|Delete`, `IFinancialPlanService.Read|Upsert`

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
    ├── ping.py
    ├── resources.py    # internal /resources REST helpers only
    └── __init__.py
```