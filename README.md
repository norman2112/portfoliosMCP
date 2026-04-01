# Planview Portfolios Actions MCP Server

A Model Context Protocol server for Planview Portfolios — the **write & action companion** to the read-only [Planview Portfolios Beta MCP](https://claude.ai/chat/f88775d2-ca9b-4680-8517-793bf65f377b#two-server-architecture). Provides 24 tools for creating, updating, deleting, and managing projects, tasks (SOAP), financial plans (SOAP), OKRs, and work hierarchy nodes. Runs locally over stdio via the official `mcp` Python SDK.

## Two-Server Architecture

This server is designed to run **alongside** the Planview-hosted Beta MCP (`Planview Portfolios US`). Together they cover the full Portfolios surface:

| Server | Role | Tools | Transport |
| --- | --- | --- | --- |
| **Beta MCP** (`Planview Portfolios US`) | Read — portfolios, search, cross-tabs, strategies, resources, dependencies, hierarchy trees | 29 | Planview-hosted (remote) |
| **Local MCP** (`planview-portfolios-actions`) | Write — create/update/delete projects, SOAP tasks, financial plans, OKRs, work node access | 24 | Local stdio |

**Beta handles:** "Show me my portfolios," "List projects in Mobility," "How many projects are in-flight?," "Search for a project by name," "What's the strategy breakdown?"

**Local handles:** "Create a new project," "Add tasks to this project," "Set up a financial plan," "Show me OKRs," "Update project status," "Copy a financial plan from a reference project."

**Together:** Beta finds → Local acts. "Find all behind-schedule projects in Mobility" (beta) → "Update their status to At Risk" (local).

All tool descriptions include `[LOCAL — ...]` routing hints so Claude knows which server to use without guessing.

## Before You Start

You will need four things from your Planview admin **before** starting setup:

| Credential | Where to find it |
|---|---|
| **API URL** | Your Planview instance URL + `/polaris` (e.g., `https://scdemo508.pvcloud.com/polaris`) — **use lowercase** |
| **Client ID** | Administration → Settings → OAuth2 credentials |
| **Client Secret** | Shown once at OAuth credential creation — copy it immediately |
| **Tenant ID** | Ask your Planview admin or find it in the admin panel |

> ⚠️ **Have all four values ready before proceeding.** The Client Secret is only shown once at creation. The Tenant ID is not obvious — ask your admin (e.g., JD) if you don't know it.

---

## Setup — Windows

### 1. Install Python 3.10+

Download from [python.org](https://www.python.org/downloads/).

> ⚠️ **Check "Add Python to PATH"** during install. If you skip this, nothing below will work.

Verify it installed correctly — **close and reopen** your terminal, then:

```
python --version
pip --version
```

Both should return version numbers. If you get "not recognized," Python isn't on PATH.

### 2. Download and extract the repo

Download the zip from GitHub and extract it to a simple path like `C:\portfoliosMCP`. 

> ⚠️ **Avoid OneDrive, Desktop, or paths with spaces.** They cause escaping nightmares in JSON config files. `C:\portfoliosMCP` is ideal.

> ⚠️ **Watch for nested folders.** GitHub zips extract to `portfoliosMCP-main\portfoliosMCP-main`. Make sure your `pyproject.toml` is at the root of wherever you land — if it's one level deeper, `cd` into that folder.

### 3. Create the virtual environment and install

Open Command Prompt:

```
cd C:\portfoliosMCP
python -m venv venv
venv\Scripts\activate
pip install -e .
```

> `pip install -e .` installs the local package into the venv. `pip install -r requirements.txt` alone is **not enough** — the server won't start without the editable install.

### 4. Find your Python path

```
where python
```

Example output: `C:\portfoliosMCP\venv\Scripts\python.exe`

You'll need this for the next step.

### 5. Open the Claude Desktop config file

Press `Win+R`, type this, hit Enter:

```
%APPDATA%\Claude
```

Or: Claude Desktop → Settings → Developer → Config

Open `claude_desktop_config.json` in Notepad. If the file doesn't exist, create it.

### 6. Paste the config

```json
{
  "mcpServers": {
    "planview-portfolios-actions": {
      "command": "C:\\portfoliosMCP\\venv\\Scripts\\python.exe",
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

Replace the path with your output from step 4, and fill in all four credential values.

> ⚠️ **Windows JSON path rule:** All backslashes must be doubled. `C:\portfoliosMCP` becomes `C:\\portfoliosMCP`. Single backslashes will cause a "Bad escaped character" JSON parse error.

> ⚠️ **API URL must be lowercase.** `https://scdemo508.pvcloud.com/polaris` — not `SCDEMO508`. Mixed case can cause OAuth 400 errors.

### 7. Restart Claude Desktop

Full quit (`File → Exit` or system tray), not just close the window. Reopen.

### 8. Test it

Ask Claude: `"Use oauth_ping to check my Planview connection"`

---

## Setup — macOS

### 1. Install Python 3.10+

```bash
brew install python3
```

### 2. Clone and install

```bash
git clone https://github.com/norman2112/portfoliosMCP.git
cd portfoliosMCP
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Find your Python path

```bash
which python3
# Example output: /Users/yourname/portfoliosMCP/venv/bin/python3
```

### 4. Open the Claude Desktop config file

```bash
# Press Cmd+Shift+G in Finder and paste this path:
~/Library/Application Support/Claude/claude_desktop_config.json

# Or from terminal:
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

If the file doesn't exist, create it.

### 5. Paste the config

```json
{
  "mcpServers": {
    "planview-portfolios-actions": {
      "command": "/Users/yourname/portfoliosMCP/venv/bin/python3",
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

> Replace `/Users/yourname/portfoliosMCP/venv/bin/python3` with the output from step 3. Fill in all four credential values.

### 6. Quit Claude Desktop (Cmd+Q) and reopen it.

### 7. Test it

Ask Claude: `"Use oauth_ping to check my Planview connection"`

---

## Common Setup Issues

| Problem | Fix |
|---------|-----|
| `python` / `pip` not recognized (Windows) | Python isn't on PATH. Reinstall and check "Add Python to PATH" |
| "Bad escaped character in JSON" (Windows) | Use `\\` double backslashes in all paths in the JSON config |
| "No module named planview_portfolios_mcp" | You ran `pip install -r requirements.txt` but not `pip install -e .` — run the latter |
| Nested folder after unzip | GitHub zips create `portfoliosMCP-main/portfoliosMCP-main`. Make sure `pyproject.toml` is at your root |
| OAuth 400 error | Check all four credentials. Make sure API URL is **lowercase** and ends with `/polaris` (no trailing slash) |
| 401 Unauthorized | Verify Client ID, Secret, and Tenant ID — no extra spaces when pasting |
| Tools don't appear in Claude | Restart Claude Desktop (full quit, not just close window) |
| JSON syntax error | Validate your config at [jsonlint.com](https://jsonlint.com) |

## Getting Your Planview Credentials

1. Log into Planview as admin → **Administration** → **Settings** → **OAuth2 credentials** tab
2. Click **Create OAuth2 credentials**
3. Name it (e.g., "MCP Server"), select **Portfolios Integration**
4. Copy the **Client ID** and **Client Secret** (⚠️ secret is only shown once)
5. Find your **Tenant ID** in the admin panel or ask your Planview admin

---

## Tools

These sections list **every MCP tool this server registers** (24 total). Older drafts of this project mentioned `list_resources` / `get_resource` / `allocate_resource`; those helpers still exist in `tools/resources.py` as **optional, non-exposed** REST wrappers—they are **not** in `tool_registry.py` or `server.py` and clients will not see them.

### Projects (REST) — Read & Write

| Tool | Description |
| --- | --- |
| `get_project` | Get a single project by ID |
| `create_project` | Create a new project (auto-defaults dates if omitted) |
| `update_project` | Partial update of project fields |
| `delete_project` | Delete a project by ID (destructive — removes project and all child data) |
| `get_project_attributes` | List available project attributes |
| `get_project_wbs` | Get project WBS as a nested tree |
| `list_field_reference` | Browse writable fields by category (for create/update) |

> **For listing/searching projects across portfolios**, use Beta MCP's `listProjectsByPortfolioId`, `searchProjectByName`, or `getProjectsByPortfolioId`.

### Work Items (REST) — Read & Write

| Tool | Description |
| --- | --- |
| `list_work` | List work items using a filter string (e.g., `project.Id .eq 1906`) |
| `get_work` | Get a single work/hierarchy node by ID (including portfolio-level nodes) |
| `update_work` | Partial update of a work item |
| `get_work_attributes` | List available work attributes |

> **For portfolio-scoped project lists**, use Beta MCP's `listProjectsByPortfolioId`.

### Tasks (SOAP) — Write-Only

| Tool | Description |
| --- | --- |
| `create_task` | Create a task (PascalCase fields, key URI format) |
| `read_task` | Read a task by key (`key://`, `ekey://`, or `search://`) |
| `delete_task` | Delete a task (cascades to children) |
| `batch_create_tasks` | Create multiple tasks in a single SOAP call |
| `batch_delete_tasks` | Delete multiple tasks (returns per-key success/failure) |

> Task updates are not exposed: the SOAP Update operation does not serialize reliably with zeep. To change a task, delete and recreate it (or use the Planview UI).

> **For reading tasks with custom attributes**, Beta MCP's `getTasksByProjectIds` or `getTasksByTaskIds` may be richer.

### Financial Plans (SOAP) — Local-Only

| Tool | Description |
| --- | --- |
| `read_financial_plan` | Read plan structure, accounts, and periods |
| `upsert_financial_plan` | Create or update a financial plan (single-line optimized) |
| `discover_financial_plan_info` | Smart discovery with reference project fallback |
| `load_financial_plan_from_reference` | Copy account structure + values from a reference project (dry-run by default) |

> **Tip:** Use `discover_financial_plan_info` or `read_financial_plan` first to find valid account/period keys before calling `upsert_financial_plan`.

> No Beta MCP equivalent exists for financial plans.

### OKRs (REST) — Local-Only

| Tool | Description |
| --- | --- |
| `list_objectives` | List objectives with pagination |
| `get_key_results_for_objective` | Get key results for a specific objective |
| `list_all_objectives_with_key_results` | Bulk fetch all objectives + their key results |

> No Beta MCP equivalent exists for OKRs.

### Utility

| Tool | Description |
| --- | --- |
| `oauth_ping` | Verify OAuth credentials are working |

## Authentication

| Variable | Description |
| --- | --- |
| `PLANVIEW_API_URL` | Base URL including `/polaris` path (lowercase) |
| `PLANVIEW_CLIENT_ID` | OAuth Client ID |
| `PLANVIEW_CLIENT_SECRET` | OAuth Client Secret |
| `PLANVIEW_TENANT_ID` | Organization Tenant ID |

> The Client Secret is only shown once at creation. Store it securely.

## SOAP API Notes

This server uses both REST and SOAP APIs. SOAP is used for tasks (`TaskService`) and financial plans (`FinancialPlanService`).

Key things to know:

- **Response payloads may be incomplete** — the API confirms success but doesn't always echo back full data. Use the corresponding read tool to verify.
- **Warnings are non-fatal** — `InvalidStructureCode` and `InvalidDefaultValues` indicate configuration issues but don't prevent successful operations.
- **Field names are PascalCase** — `FatherKey`, not `father_key`.
- **Key URI formats:** `key://2/$Plan/12345` (direct), `ekey://2/namespace/id` (external), `search://2/$Plan?description=Name` (search).
- `batch_delete_tasks` has known SOAP response parsing reliability issues — verify deletions with `read_task`.

See `SOAP_API_BEHAVIORS.md` for the full rundown.

## Known Limitations

- **`list_projects` without a filter** — some instances require a filter (e.g., `project.Id .eq 3817`)
- **`update_work`** — returns 405 on some instances. Use `update_project` for project-level items
- **Task updates** — not supported. Workaround: delete + recreate
- **`batch_delete_tasks`** — SOAP response parsing is flaky. Verify with `read_task`

## Development

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Add your credentials

# Run
python -m planview_portfolios_mcp
planview-portfolios-actions   # console script (same server; MCP name planview-portfolios-actions)

# Test & lint
pytest
black src/ && ruff check src/ && mypy src/
```

## Project Structure

```
src/planview_portfolios_mcp/
├── server.py          # MCP Server (stdio) + tool routing
├── tool_registry.py   # Tool definitions, routing hints, input schemas
├── __main__.py        # Entry point (python -m planview_portfolios_mcp)
├── config.py          # Pydantic Settings (loads from .env)
├── client.py          # Shared HTTP client with retry logic
├── soap_client.py     # SOAP client (zeep) with retry logic
├── exceptions.py      # Custom exception hierarchy
├── models.py          # Pydantic input validation models
├── logging_config.py  # Structured logging
└── tools/
    ├── projects.py    # Project tools
    ├── work.py        # Work hierarchy tools
    ├── tasks.py       # Task tools (SOAP)
    ├── financial_plan.py  # Financial plan tools (SOAP)
    ├── okrs.py        # OKR tools
    ├── ping.py        # OAuth ping
    ├── resources.py   # Internal REST helpers for /resources (not MCP-exposed)
    └── __init__.py
```

## Requirements

- Python 3.10+
- Planview Portfolios instance with OAuth API access
- `mcp>=1.0.0` for MCP SDK (stdio transport)
- `httpx` for REST, `zeep` for SOAP — see `pyproject.toml`

## License

MIT
