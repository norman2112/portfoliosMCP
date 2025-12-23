# Claude Desktop Quick Start

## Summary

The MCP server is ready for Claude Desktop. One fix was needed:

✅ **Fixed**: Added missing `discover_financial_plan_info` import to `server.py`

## Setup Steps

### 1. Verify Installation

```bash
cd /Users/ngarrett/Desktop/portfolios-mcp-financials
source venv/bin/activate
pip install -e .
python -m planview_portfolios_mcp.server --help
```

Should show FastMCP help/version info.

### 2. Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "/Users/ngarrett/Desktop/portfolios-mcp-financials/venv/bin/python3",
      "args": [
        "-m",
        "planview_portfolios_mcp.server"
      ],
      "env": {
        "PLANVIEW_API_URL": "https://scdemo520.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "Sk2TFV5otW4E7cQL9NHyk3Nse4wix",
        "PLANVIEW_CLIENT_SECRET": "7ff8b0f0-19d9-496c-9f0f-25c966afd7d0",
        "PLANVIEW_TENANT_ID": "p-5gxmkcah4x|plt",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**Important**: Use the full path to your venv's Python as shown above.

### 3. Restart Claude Desktop

After making changes, **restart Claude Desktop completely**.

### 4. Verify

Start a new conversation in Claude Desktop and test:

- "List my Planview projects"
- "Create a new project called 'Test Project'"
- "Read the financial plan for project 17293"

## Available Tools

Once configured, you'll have access to:

### Financial Plans (New!)
- `read_financial_plan` - Read financial plan structure
- `discover_financial_plan_info` - Smart discovery with fallback
- `upsert_financial_plan` - Create/update financial plan lines

### Projects
- `create_project` - Create projects (auto-sets dates)
- `list_projects`, `get_project`, `update_project`

### Tasks
- `create_task`, `read_task`, `update_task`, `delete_task`

### Resources
- `list_resources`, `get_resource`, `allocate_resource`

### Utilities
- `oauth_ping` - Test authentication

## What Changed

1. ✅ **Fixed import**: Added `discover_financial_plan_info` to server imports
2. ✅ **Server verified**: Confirmed server loads and runs correctly
3. ✅ **Config example**: Created `claude_desktop_config_example.json` for reference

## Troubleshooting

### Server not starting
- Check Python path matches your venv location
- Verify package installed: `pip show planview-portfolios-mcp`
- Test manually: `python -m planview_portfolios_mcp.server`

### Tools not appearing
- Restart Claude Desktop after config changes
- Check Claude Desktop logs/console for errors
- Verify credentials are correct in config

### Authentication errors
- Verify all env vars are set correctly in config
- Check that `PLANVIEW_API_URL` includes `/polaris`
- Test with: `python test_creds_simple.py`

## Notes

- The server runs via stdio (standard input/output)
- Claude Desktop will execute the Python command and communicate via stdio
- Environment variables from config are passed to the server process
- OAuth tokens are automatically managed and refreshed

