# Planview Portfolios MCP Server

MCP server for Planview Portfolios. 24 tools for projects, tasks, financial plans, OKRs.

## Setup — macOS

**1. Install Python 3.10+ if you don't have it:**

```bash
brew install python3
```

**2. Clone and install:**

```bash
git clone https://github.com/norman2112/portfoliosMCP.git
cd portfoliosMCP
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

**3. Find your Python path (you'll need this):**

```bash
which python3
# Example output: /Users/yourname/portfoliosMCP/venv/bin/python3
```

**4. Open the Claude Desktop config file:**

```bash
# Press Cmd+Shift+G in Finder and paste this path:
~/Library/Application Support/Claude/claude_desktop_config.json

# Or from terminal:
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

If the file doesn't exist, create it.

**5. Paste this, replacing the placeholders:**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "/Users/yourname/portfoliosMCP/venv/bin/python3",
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

> Replace `/Users/yourname/portfoliosMCP/venv/bin/python3` with the output from step 3.

**6. Quit Claude Desktop (Cmd+Q) and reopen it.**

**7. Test it — ask Claude:** `"Use oauth_ping to check my Planview connection"`

---

## Setup — Windows

**1. Install Python 3.10+ if you don't have it:**

Download from [python.org](https://www.python.org/downloads/). Check **"Add Python to PATH"** during install.

**2. Clone and install (open Command Prompt or PowerShell):**

```
git clone https://github.com/norman2112/portfoliosMCP.git
cd portfoliosMCP
python -m venv venv
venv\Scripts\activate
pip install -e .
```

**3. Find your Python path (you'll need this):**

```
where python
# Example output: C:\Users\yourname\portfoliosMCP\venv\Scripts\python.exe
```

**4. Open the Claude Desktop config file:**

```
# Press Win+R, type this, hit Enter:
%APPDATA%\Claude
This can also be reached by going to Claude > Settings > Developer > Config
You are looking for the below file: 

# Open claude_desktop_config.json in Notepad
# If the file doesn't exist, create it
```

**5. Paste this, replacing the placeholders:**

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "C:\\Users\\yourname\\portfoliosMCP\\venv\\Scripts\\python.exe",
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

> Replace `C:\\Users\\yourname\\portfoliosMCP\\venv\\Scripts\\python.exe` with the output from step 3. Use `\\` (double backslashes) in paths.

**6. Close Claude Desktop completely and reopen it.**

**7. Test it — ask Claude:** `"Use oauth_ping to check my Planview connection"`

---

## Common Setup Issues

| Problem | Fix |
|---------|-----|
| Tools don't appear | Restart Claude Desktop (full quit, not just close window) |
| "Module not found" | Make sure you ran `pip install -e .` and the config points to the venv Python |
| Auth errors | Check `PLANVIEW_API_URL` ends with `/polaris` (no trailing slash) |
| 401 Unauthorized | Verify Client ID, Secret, and Tenant ID — no extra spaces when pasting |
| JSON syntax error | Validate your config at [jsonlint.com](https://jsonlint.com) |

## Getting Your Planview Credentials

1. Log into Planview as admin → **Administration** → **Settings** → **OAuth2 credentials** tab
2. Click **Create OAuth2 credentials**
3. Name it (e.g., "MCP Server"), select **Portfolios Integration**
4. Copy the **Client ID** and **Client Secret** (⚠️ secret is only shown once)
5. Find your **Tenant ID** in the admin panel or ask your Planview admin

---

## Tools

### Projects (REST)

| Tool | Description |
|------|-------------|
| `list_projects` | List projects with optional filter |
| `get_project` | Get a single project by ID |
| `create_project` | Create a new project |
| `update_project` | Partial update of project fields |
| `get_project_attributes` | List available project attributes |
| `get_project_wbs` | Get project WBS as a nested tree |
| `list_field_reference` | Browse writable fields by category |

### Work Items (REST)

| Tool | Description |
|------|-------------|
| `list_work` | List work items using a filter string |
| `get_work` | Get a single work item by ID |
| `update_work` | Partial update of a work item |
| `get_work_attributes` | List available work attributes |

### Tasks (SOAP)

| Tool | Description |
|------|-------------|
| `create_task` | Create a task |
| `read_task` | Read a task by key |
| `delete_task` | Delete a task (cascades to children) |
| `batch_create_tasks` | Create multiple tasks in one call |
| `batch_delete_tasks` | Delete multiple tasks |

> Task updates aren't supported via MCP (zeep/WSDL issue). Delete and recreate instead.
> Response fields may be `null` on success — that's normal. Use `read_task` to verify. See [SOAP_API_BEHAVIORS.md](SOAP_API_BEHAVIORS.md).

### Financial Plans (SOAP)

| Tool | Description |
|------|-------------|
| `read_financial_plan` | Read plan structure, accounts, and periods |
| `upsert_financial_plan` | Create or update a financial plan |
| `discover_financial_plan_info` | Smart discovery with reference project fallback |
| `load_financial_plan_from_reference` | Copy structure + values from a reference project |

> Use `discover_financial_plan_info` first to find valid account/period keys.

### OKRs (REST)

| Tool | Description |
|------|-------------|
| `list_objectives` | List objectives with pagination |
| `get_key_results_for_objective` | Get key results for an objective |
| `list_all_objectives_with_key_results` | Bulk fetch objectives + key results |

### Utility

| Tool | Description |
|------|-------------|
| `oauth_ping` | Verify credentials are working |

---

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
python -m planview_portfolios_mcp.server

# Test & lint
pytest
black src/ && ruff check src/ && mypy src/
```

## Requirements

- Python 3.10+
- Planview Portfolios instance with OAuth API access

## License

MIT
