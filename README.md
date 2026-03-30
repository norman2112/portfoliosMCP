# Planview Portfolios MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) server for [Planview Portfolios](https://www.planview.com/products/portfolios/). Provides 24 tools for managing projects, work items, tasks (SOAP), financial plans (SOAP), resources, and OKR objectives directly from Claude Desktop or any MCP-compatible client. Built with [FastMCP](https://github.com/jlowin/fastmcp).

**Cloud URL**: `https://portfolios-mcp.fastmcp.app/mcp` — no local install required.

## Quick Start

### Option 1: FastMCP Cloud (recommended)

Add to your Claude Desktop config:

**macOS** — `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows** — `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "url": "https://portfolios-mcp.fastmcp.app/mcp",
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

### Option 2: Local Development

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -e .
```

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "/path/to/venv/bin/python3",
      "args": ["-m", "planview_portfolios_mcp.server"],
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

> **API URL format**: Must include `/polaris`, no trailing slash.
> ✅ `https://your-instance.pvcloud.com/polaris`
> ❌ `https://your-instance.pvcloud.com`
> ❌ `https://your-instance.pvcloud.com/polaris/`

Restart Claude Desktop after saving.

## Tools

### Projects (REST)

| Tool | Description |
|------|-------------|
| `list_projects` | List projects with optional filter and attributes |
| `get_project` | Get a single project by ID |
| `create_project` | Create a new project (auto-defaults dates if omitted) |
| `update_project` | Partial update of project fields |
| `get_project_attributes` | List available project attributes |
| `get_project_wbs` | Get project WBS as a nested tree |
| `list_field_reference` | Browse writable fields by category (for create/update) |

### Work Items (REST)

| Tool | Description |
|------|-------------|
| `list_work` | List work items using a filter string (e.g., `project.Id .eq 1906`) |
| `get_work` | Get a single work item by ID |
| `update_work` | Partial update of a work item |
| `get_work_attributes` | List available work attributes |

### Tasks (SOAP)

| Tool | Description |
|------|-------------|
| `create_task` | Create a task (PascalCase fields, key URI format) |
| `read_task` | Read a task by key (`key://`, `ekey://`, or `search://`) |
| `delete_task` | Delete a task (cascades to children) |
| `batch_create_tasks` | Create multiple tasks in a single SOAP call |
| `batch_delete_tasks` | Delete multiple tasks (returns per-key success/failure) |

Task **updates** are not exposed: the SOAP `Update` operation does not serialize reliably with zeep for this WSDL. To change a task, delete it and create a new one with the desired fields (or use the Planview UI).

> **SOAP quirks**: Response fields may be `null` even on success — this is normal. Use `read_task` to verify. See [SOAP_API_BEHAVIORS.md](SOAP_API_BEHAVIORS.md) for details.

### Financial Plans (SOAP)

| Tool | Description |
|------|-------------|
| `read_financial_plan` | Read plan structure, accounts, and periods |
| `upsert_financial_plan` | Create or update a financial plan (single-line optimized) |
| `discover_financial_plan_info` | Smart discovery with reference project fallback |
| `load_financial_plan_from_reference` | Copy account structure + values from a reference project (dry-run by default) |

> **Tip**: Use `discover_financial_plan_info` or `read_financial_plan` first to find valid account/period keys before calling `upsert_financial_plan`.

### Resources (REST)

| Tool | Description |
|------|-------------|
| `list_resources` | List resources with optional department/role/availability filter |
| `get_resource` | Get detailed resource info including allocations |
| `allocate_resource` | Allocate a resource to a project (percentage, date range) |

### OKRs (REST)

| Tool | Description |
|------|-------------|
| `list_objectives` | List objectives with pagination |
| `get_key_results_for_objective` | Get key results for a specific objective |
| `list_all_objectives_with_key_results` | Bulk fetch all objectives + their key results |

### Utility

| Tool | Description |
|------|-------------|
| `oauth_ping` | Verify OAuth credentials are working |

## Authentication

Uses OAuth 2.0 client credentials flow. Generate credentials in **Planview Admin → Settings → OAuth2 credentials tab**. The server handles token exchange, caching (60-minute lifetime), and automatic refresh.

Required environment variables:

| Variable | Description |
|----------|-------------|
| `PLANVIEW_API_URL` | Base URL including `/polaris` path |
| `PLANVIEW_CLIENT_ID` | OAuth Client ID |
| `PLANVIEW_CLIENT_SECRET` | OAuth Client Secret |
| `PLANVIEW_TENANT_ID` | Organization Tenant ID |

⚠️ The Client Secret is only shown once at creation. Store it securely.

## SOAP API Notes

This server uses both REST and SOAP APIs. SOAP is used for tasks (`TaskService`) and financial plans (`FinancialPlanService`).

Key things to know:

- **Response payloads may be incomplete** — the API confirms success but doesn't always echo back full data. Use the corresponding read tool to verify.
- **Warnings are non-fatal** — `InvalidStructureCode` and `InvalidDefaultValues` indicate configuration issues but don't prevent successful operations.
- **Field names are PascalCase** — `FatherKey`, not `father_key`.
- **Key URI formats**: `key://2/$Plan/12345` (direct), `ekey://2/namespace/id` (external), `search://2/$Plan?description=Name` (search).
- **`batch_delete_tasks`** has known SOAP response parsing reliability issues — verify deletions with `read_task`.

See [SOAP_API_BEHAVIORS.md](SOAP_API_BEHAVIORS.md) for the full rundown.

## Development

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Add your credentials

# Run
python -m planview_portfolios_mcp.server

# Test & lint
pytest
black src/ && ruff check src/ && mypy src/
```

## Project Structure

```
src/planview_portfolios_mcp/
├── server.py          # FastMCP server + tool registration
├── config.py          # Pydantic Settings (loads from .env)
├── client.py          # Shared HTTP client with retry logic
├── soap_client.py     # SOAP client (zeep) with retry logic
├── exceptions.py      # Custom exception hierarchy
├── models.py          # Pydantic input validation models
├── logging_config.py  # Structured logging
└── tools/
    ├── projects.py    # Project + work item tools
    ├── resources.py   # Resource management tools
    └── __init__.py    # Tool exports
```

## Requirements

- Python 3.10+
- Planview Portfolios instance with OAuth API access
- (Tools use `httpx` for REST, `zeep` for SOAP — see `pyproject.toml`)

## License

MIT