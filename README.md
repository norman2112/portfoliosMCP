# Planview Portfolios MCP Server (v2)

An MCP server that connects [Planview Portfolios](https://www.planview.com/products/portfolios/) (enterprise strategic portfolio management) to Claude Desktop or any MCP-compatible AI client. Five action-based tools covering projects, tasks, financial plans, and work hierarchy — bridging both REST and legacy SOAP APIs under a single MCP interface.

## Why This Exists

Planview Portfolios is an enterprise SPM platform used by large organizations to manage project portfolios, resource capacity, and strategic funding. Its API surface is split across REST (projects, work items) and SOAP (tasks, financial plans) with different auth models and data formats.

This server unifies both API layers behind MCP so Claude can create projects, build financial plans, manage tasks, and navigate work hierarchies through conversation.

This is the second MCP server I built for Planview products (the first was [AgilePlace MCP Server](https://github.com/norman2112/agileplaceMCPserver)). Same pattern, completely different APIs — AgilePlace is a modern REST API, Portfolios mixes REST with SOAP services that require different serialization, auth, and error handling.

## What Changed in v2

v1 exposed 24 tools. v2 exposes **5**.

Benchmark evidence is consistent that tool count degrades LLM tool-selection accuracy, and v1's surface had a lot of near-duplicates (`get_project` / `create_project` / `update_project` / `delete_project` → one `manage_project` with an `action` parameter). v2 collapses each domain into a single action-dispatched tool.

| v1 | v2 |
| --- | --- |
| `get_project`, `create_project`, `update_project`, `delete_project`, `get_project_attributes`, `list_field_reference` | `manage_project` (`create` / `get` / `update` / `delete` / `fields`) |
| `list_work`, `get_work`, `update_work`, `get_work_attributes`, `get_project_wbs` | `inspect_work` (`wbs` / `get` / `list` / `update`) |
| `create_task`, `read_task`, `delete_task`, `batch_create_tasks`, `batch_delete_tasks` | `manage_tasks` (`create` / `read` / `delete`, all batch-capable) |
| `read_financial_plan`, `upsert_financial_plan`, `discover_financial_plan_info`, `load_financial_plan_from_reference` | `manage_financial_plan` (`read` / `discover` / `upsert` / `copy`) |
| `oauth_ping` | `test_connection` (structured checks, not a bare 401) |

Other v2 changes:

- **OKR tools removed.** Out of scope for v2; not shipped.
- **Scope is stated inline.** Every tool description opens with a `[LOCAL — ...]` summary of what it does and does not cover, so Claude doesn't attempt discovery this server can't perform.
- **Warnings promoted.** Create responses surface Planview API warnings at the top level (`warnings`, `has_warnings`, `warning_hint`) instead of burying them in `meta`.
- **Discover returns labeled keys.** `manage_financial_plan action=discover` returns `accounts` and `periods` as `[{key, description}]`, so you can pick "Aug 2026" without a second call.
- **Upsert accepts both payload shapes.** Flat `Lines: [...]` or SOAP-style `Lines.FinancialPlanLineDto[...]` — nested envelopes are normalized on input.

## What It Does

- **Projects** — full CRUD, curated writable-field catalog, live attribute lookup
- **Work hierarchy** — WBS tree navigation, work-node read/update
- **Tasks (SOAP)** — create, read, delete via Planview's TaskService
- **Financial plans (SOAP)** — read, discover structure, upsert, copy from a reference project
- **Connection diagnostics** — structured config/token/ping checks

## Tech Stack

- **Runtime:** Python 3.10+
- **Protocol:** MCP over stdio (official `mcp` Python SDK)
- **APIs:** Planview REST (OAuth2 client credentials) + SOAP (zeep) — TaskService, FinancialPlanService
- **Validation:** Pydantic for config and input models
- **HTTP:** httpx (REST), zeep (SOAP)

## Architecture

```
Claude Desktop / MCP Client
        ↓ stdio
  Local MCP Server (Python)
    ├── Planview REST API (OAuth2 client credentials)
    │     ├── Projects
    │     └── Work Items
    └── Planview SOAP API (zeep + OAuth2)
          ├── TaskService
          └── FinancialPlanService
```

## Scope

This server is built for **acting on things you can already identify** — creating projects, writing financial plans, managing tasks, updating work nodes.

It deliberately does **not** do discovery. There is no "list all portfolios," no project search, no strategy-tree browsing. Every tool takes an id you already have. That keeps the surface small and the behavior predictable.

In practice you'll get ids from the Planview UI, from a previous call's response, or from another tool. If you use a read-oriented Planview MCP alongside this one, that pairing works fine — but nothing here depends on it.

## Before You Start — Checklist

Gather these **before** you touch anything. You will be stuck without them.

- [ ] **API URL** — Your Planview instance URL + `/polaris` (e.g., `https://scdemo5xx.pvcloud.com/polaris`) — must be **lowercase**
- [ ] **Client ID** — From Administration → Users → OAuth2 credentials
- [ ] **Client Secret** — Shown **once** at OAuth credential creation. If you didn't copy it, create a new one.
- [ ] **Global Tenant ID** — Not obvious in the UI. Ask your Planview admin.
- [ ] **Parent structure codes** — See [Work Hierarchy Setup](#work-hierarchy-setup-required-for-project-creation) below. You cannot create a project without one.

> ⚠️ **Do not skip this step.** You will get through the entire setup and hit a wall at the end if any of these are missing or wrong.

---

## Work Hierarchy Setup (Required for Project Creation)

`manage_project action=create` requires `data.parent.structureCode` — the work-hierarchy (`$Plan`) folder one level above Primary Planning Level. **This server cannot discover it**, so you need to grab it once from the Planview UI.

Do this before your first create and you won't have to think about it again.

1. In Planview, go to **Menu → Administration → Architecture → Primary Structures**
2. Find **Work Structure** in the list and click **(define levels)**
3. Screenshot the tree — each node shows its name with the structure code in parentheses
4. Paste it to Claude: *"Commit these structure codes to memory for [tenant name]"*

After that, project creation just works — Claude has the codes and picks the right parent.

> Requires admin access. If you don't have it, ask whoever administers your tenant for a screenshot of that page — it's a one-time ask.

**Two things to know:**

- **Codes are per-tenant.** Nothing carries between environments. Label the tenant when you commit them.
- **Resolve by code, never by name.** Duplicate folder names are common (one demo tenant has three departments named "Marketing" and two nodes named "Archived Area"). The code is the only unambiguous handle.

The layer you want is where projects hang directly — typically Department, one below Division:

```
PlanRoot (Enterprise)
└── Active Enterprise Area
    └── Information Technology      ← Division
        ├── Mobility                ← Department  ✅ use this code
        ├── System Development      ← Department  ✅
        └── Business Applications   ← Department  ✅
            └── [your project]
```

> Note: portfolio entity IDs are **not** work-hierarchy node IDs. The same business unit can be portfolio `5964` and work node `3787`. They are not interchangeable.

> Also distinct from **alternate structures** (Region, Line of Business, etc.), which live under **Administration → Attributes and Column Sets → Alternate Structures**. Both use structure codes; they are different trees.

---

## Setup — Windows

### Step 1: Install Python

If you've never installed Python before, that's fine. Go to [python.org/downloads](https://www.python.org/downloads/) and download the latest version.

When the installer opens, you'll see a checkbox at the bottom that says **"Add Python to PATH"**. **Check that box.** This is the most important part of the install.

After it finishes, **close any open Command Prompt windows** and open a fresh one:

1. Press the **Windows key**, type `cmd`, press **Enter**
2. Type these two commands, one at a time:

```
python --version
pip --version
```

You should see version numbers for both. If you see "not recognized," go back and reinstall Python with the PATH checkbox checked.

### Step 2: Download this repository

1. On the GitHub page, click the green **Code** button → **Download ZIP**
2. Extract the zip to `C:\portfoliosMCP`

> ⚠️ **Use a simple path like `C:\portfoliosMCP`.** Do NOT put this in OneDrive, your Desktop, or any folder with spaces in the name. It will cause problems later.

> ⚠️ **Check for a folder-inside-a-folder.** After unzipping, open `C:\portfoliosMCP`. If you see another folder called `portfoliosMCP-main` instead of files like `pyproject.toml`, move everything up one level so `pyproject.toml` sits directly inside `C:\portfoliosMCP`.

### Step 3: Install the server

1. Open Command Prompt (Windows key → type `cmd` → Enter)
2. Run these commands one at a time:

```
cd C:\portfoliosMCP
python -m venv venv
venv\Scripts\activate
pip install -e .
```

Wait for each command to finish before running the next one. The last command will download dependencies and may take a minute or two.

> ℹ️ **What does this do?** It creates an isolated Python environment (`venv`) and installs the server into it. You must use `pip install -e .` — running `pip install -r requirements.txt` alone is not enough and the server will fail to start.

### Step 4: Get your Python path

While still in Command Prompt, run:

```
where python
```

Copy the line that includes `venv\Scripts\python.exe`. It should look something like:

```
C:\portfoliosMCP\venv\Scripts\python.exe
```

You'll need this in the next step.

### Step 5: Configure Claude Desktop

1. Open Claude Desktop
2. Go to **Settings → Developer → Edit Config**

Or: press **Win+R**, type `%APPDATA%\Claude`, press Enter, and open `claude_desktop_config.json` in Notepad.

If the file doesn't exist, create a new text file with that exact name.

### Step 6: Paste this into the config file

```json
{
  "mcpServers": {
    "portfoliosMCP_v2": {
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

Replace:
- The `command` path with your output from Step 4
- All four `your_...` values with your actual Planview credentials from the checklist

**Two critical rules for this file:**

1. **Double every backslash in the path.** `C:\portfoliosMCP` must be written as `C:\\portfoliosMCP`. If you don't, you'll get a "Bad escaped character" error and Claude Desktop won't start properly.
2. **API URL must be lowercase.** `https://scdemo508.pvcloud.com/polaris` — not `SCDEMO508`. Uppercase can cause authentication failures.

### Step 7: Restart Claude Desktop

Close Claude Desktop completely — use **File → Exit** or right-click the icon in the system tray and quit. Just clicking the X may not fully close it. Then reopen it.

### Step 8: Test it

In Claude Desktop, type:

```
Use test_connection to check my Planview connection
```

You should get a structured result with config, token, and ping checks. If any check fails, the response tells you which one — see the troubleshooting table below.

---

## Setup — macOS

### Step 1: Install Python

```bash
brew install python3
```

### Step 2: Clone and install

```bash
git clone https://github.com/norman2112/portfoliosMCP.git
cd portfoliosMCP
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Step 3: Get your Python path

```bash
which python3
# Example output: /Users/yourname/portfoliosMCP/venv/bin/python3
```

### Step 4: Open the Claude Desktop config file

```bash
# Press Cmd+Shift+G in Finder and paste this path:
~/Library/Application Support/Claude/claude_desktop_config.json

# Or from terminal:
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

If the file doesn't exist, create it.

### Step 5: Paste the config

```json
{
  "mcpServers": {
    "portfoliosMCP_v2": {
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

Replace the Python path with your output from Step 3. Fill in all four credential values.

### Step 6: Quit Claude Desktop (Cmd+Q) and reopen it.

### Step 7: Test it

Ask Claude: `"Use test_connection to check my Planview connection"`

---

## Troubleshooting

| What you see | What's wrong | How to fix it |
|---|---|---|
| `python` or `pip` is "not recognized" | Python isn't installed or isn't on PATH | Reinstall Python from python.org — check **"Add Python to PATH"** |
| "Bad escaped character in JSON" | Single backslashes in the config file | Change every `\` to `\\` in the `command` path |
| "No module named planview_portfolios_mcp" | Package not installed into the venv | Run `pip install -e .` from the repo folder (not `pip install -r requirements.txt`) |
| `test_connection`: token OK, ping 401 | Tenant ID is wrong or empty | Almost never a stale secret — re-check `PLANVIEW_TENANT_ID` first |
| OAuth 400 error | Bad credentials or uppercase API URL | Double-check all four values. API URL must be **lowercase** and end with `/polaris` |
| 401 Unauthorized | Wrong Client ID, Secret, or Tenant ID | Re-verify all credentials. Watch for extra spaces when pasting |
| Tools don't show up in Claude | Claude Desktop didn't fully restart | Quit via File → Exit (not just X), then reopen |
| Tools vanish after an edit | Server crashed on startup | Check your terminal for a stack trace, then toggle the connector off/on |
| JSON syntax error on startup | Malformed config file | Copy your config into [jsonlint.com](https://jsonlint.com) to find the error |
| Folder has no `pyproject.toml` | Nested folder from GitHub zip | Look one folder deeper — move contents up so `pyproject.toml` is at your root path |

---

## Getting Your Planview Credentials

1. Log into Planview as admin → **Administration** → **Users** → **OAuth2 credentials** tab
2. Click **Create OAuth2 credentials**
3. Name it (e.g., "MCP Server"), select **Portfolios Integration**
4. Copy the **Client ID** and **Client Secret** (⚠️ secret is only shown once)
5. Find your **Tenant ID** in the admin panel or ask your Planview admin

---

## Tools

Five tools, action-dispatched. Every description opens with a `[LOCAL — ...]` summary stating what the tool covers and what it can't do.

### `test_connection`

No parameters. Runs three checks and always returns a structured result rather than throwing:

1. **Config** — API URL shape, client id/secret present, tenant id present. Detects a bearer JWT pasted into `PLANVIEW_CLIENT_SECRET`.
2. **Token** — tries multipart, then form, then JSON encoding.
3. **Ping** — secured ping with that token and `X-Tenant-Id`.

> Token succeeds but ping returns 401 → tenant ID is wrong or empty. Not a stale secret.

### `manage_project`

| Action | Notes |
| --- | --- |
| `create` | Requires `data.description` and `data.parent.structureCode`. Dates default to today and +6 months. `create_default_tasks=true` seeds five sample tasks via SOAP. |
| `get` | Requires `project_id`. Response includes `parent.structureCode` for reuse on later creates. |
| `update` | Partial PATCH. Field IDs are **case-sensitive** — call `action=fields` first if unsure. |
| `delete` | Destructive; removes the project and children. |
| `fields` | Curated writable-field catalog (~120 fields). Optional `category` filter. `include_live_catalog=true` fetches the live attribute list. |

> ⚠️ **Do not invent StructureCode values** (Status, Region, RAG, etc.) on create. They are tenant-specific and the catalog's `example` values are not safe to send. Omit them and let Planview apply product defaults, then PATCH with codes you've verified.

> Check `has_warnings` after every create. See [Warnings](#warnings-are-non-fatal-but-real) below.

**Not supported:** listing the work tree, browsing `$Strategy`, or discovering a parent code. Bring the id.

### `inspect_work`

| Action | Notes |
| --- | --- |
| `wbs` (default) | Nested WBS tree for a known `project_id`. Optional `max_depth`. |
| `get` | One work node by `work_id`. |
| `list` | Work items under a known project. Prefer `project_id` (the filter is built for you); raw `filter` is a fallback, e.g. `project.Id .eq 1906`. |
| `update` | PATCH a work node. Returns **405 on some instances** — use `manage_project` for project-level fields. |

> This is the work hierarchy (`$Plan`), not strategy (`$Strategy`). It cannot enumerate the Plan tree or list parents without an id.

### `manage_tasks`

| Action | Notes |
| --- | --- |
| `create` | Requires `tasks` (list; length 1 is fine). Each needs `Description`. `FatherKey` optional if `project_id` is set. An `ekey://` is minted when `Key` is missing so retries don't duplicate. |
| `read` | Requires `task_key` or `task_keys`. Null fields in the response do **not** mean the create failed. |
| `delete` | Requires `task_key` or `task_keys`. Cascades to children. Per-key results. |

> **Task updates are not supported.** SOAP Update doesn't serialize reliably with zeep. Delete and recreate, or use the UI.

> SOAP Create is **not atomic** — the response carries per-task success/failure. Retry only the failures.

### `manage_financial_plan`

| Action | Notes |
| --- | --- |
| `read` | Plan for `project_id` (or `entity_key`) + `version_key` (default Actual/Forecast `key://14/1`). `include_entries=false` by default to keep the payload small. |
| `discover` | Accounts and periods with fallback: target → reference project → config. Returns `accounts` / `periods` as `[{key, description}]` plus bare key lists. Source is tagged. Use this when upsert says "No editable lines." |
| `upsert` | Requires `plan_data` with `Lines`. Creates the plan if it doesn't exist. |
| `copy` | Copies account structure and values from `reference_project_id` onto `target_project_id`. **Dry-run unless `confirm=true`.** Always preview first. |

**Preferred upsert shape:**

```json
{
  "EntityKey": "key://2/$Plan/17696",
  "VersionKey": "key://14/1",
  "Lines": [{
    "AccountKey": "key://2/$Account/3653",
    "Unit": "Currency",
    "Entries": [
      { "PeriodKey": "key://16/183", "Value": 50000 },
      { "PeriodKey": "key://16/184", "Value": 50000 }
    ]
  }]
}
```

SOAP-style envelopes (`Lines.FinancialPlanLineDto`, `Entries.EntryDto`) are also accepted and normalized — so a `read` response can be fed back in after adding entries.

> ⚠️ **Never build PeriodKeys by incrementing.** Period ids skip across fiscal-year boundaries — one tenant runs `…181, 182, 183 … 187` then jumps to `193`. Only use keys returned by `discover` or `read`. Prefer the labeled `periods` array so you can see which month you're writing to.

---

## Behaviors Worth Knowing

### Warnings are non-fatal but real

Create responses promote Planview API warnings to top-level `warnings` / `has_warnings` / `warning_hint`. The project **does** exist — do not retry the create.

The common one is `InvalidDefaultValues` + `InvalidStructureCode`, meaning a tenant-configured attribute default points at a code Planview won't accept. The field is silently left unset. Example seen in the wild:

```
1020 InvalidStructureCode: (2263) is not a valid choice for Region
```

The attribute default is stored as a `code|label` pair captured when it was set (`2263|North America`). The label is a snapshot, not a live lookup — so a correct-looking label tells you nothing about whether the code still resolves. Fix it in **Administration → Attributes and Column Sets → Alternate Structures → [attribute] → Edit Attribute**, either by reactivating the code (**Show Deactivated Elements**) or repointing the Default list.

If nothing in your workflow reads that field, ignoring it is a legitimate choice.

### SOAP echoes are incomplete

`upsert` routinely returns `Lines: []` on success. This is normal, not a failure. **Always verify with `action=read`.** Same for tasks — null fields in a read response don't mean the write failed.

### Read and upsert are shaped differently

`read` passes SOAP's response through as-is, so collections arrive wrapped in typed envelopes (`Lines.FinancialPlanLineDto[]`). That wrapper is an artifact of XML→JSON conversion — XML has no array type, so a converter keys the list by its child element name. `upsert` normalizes both shapes on input, so the round trip works either way.

### Key URI formats

- `key://2/$Plan/12345` — direct
- `ekey://2/namespace/id` — external
- `search://2/$Plan?description=Name` — search

Field names in SOAP payloads are **PascalCase** (`FatherKey`, not `father_key`).

## Known Limitations

- **No discovery.** No portfolio lists, project search, or strategy browsing. Every tool needs an id you already have.
- **Parent structure codes** — must come from the Planview UI. See [Work Hierarchy Setup](#work-hierarchy-setup-required-for-project-creation).
- **`inspect_work action=update`** — 405 on some instances. Use `manage_project` for project-level items.
- **Task updates** — not supported. Delete and recreate.
- **`inspect_work action=list` without a filter** — some instances require one.

## Development

```bash
python -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # Add your credentials

# Run
python -m planview_portfolios_mcp

# Test & lint
pytest
black src/ && ruff check src/ && mypy src/
```

## Requirements

- Python 3.10+
- Planview Portfolios instance with OAuth API access
- `mcp>=1.0.0` for MCP SDK (stdio transport)
- `httpx` for REST, `zeep` for SOAP — see `pyproject.toml`

## License

MIT
