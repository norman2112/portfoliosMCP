# Claude Desktop Setup Guide

This guide explains how to configure the Planview Portfolios MCP server with Claude Desktop for local execution.

## Option 1: Local Installation (Recommended)

Run the MCP server locally on your machine. Claude Desktop will execute it via stdio.

### Prerequisites

1. Python 3.10 or higher
2. Virtual environment (recommended)
3. Planview API credentials

### Setup Steps

1. **Install the package** (if not already done):
   ```bash
   cd /path/to/portfolios-mcp-financials
   pip install -e .
   ```

2. **Create/verify `.env` file** with your credentials:
   ```bash
   PLANVIEW_API_URL=https://scdemo520.pvcloud.com/polaris
   PLANVIEW_CLIENT_ID=your_client_id
   PLANVIEW_CLIENT_SECRET=your_client_secret
   PLANVIEW_TENANT_ID=your_tenant_id
   USE_OAUTH=true
   ```

3. **Test the server locally**:
   ```bash
   python -m planview_portfolios_mcp.server
   ```
   It should start without errors (will wait for stdio input from Claude Desktop).

4. **Configure Claude Desktop** - Add to `claude_desktop_config.json`:

   **macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "planview-portfolios": {
         "command": "python3",
         "args": [
           "-m",
           "planview_portfolios_mcp.server"
         ],
         "env": {
           "PLANVIEW_API_URL": "https://scdemo520.pvcloud.com/polaris",
           "PLANVIEW_CLIENT_ID": "your_client_id",
           "PLANVIEW_CLIENT_SECRET": "your_client_secret",
           "PLANVIEW_TENANT_ID": "your_tenant_id",
           "USE_OAUTH": "true"
         }
       }
     }
   }
   ```

   **Important**: Make sure `python3` in the command points to the correct Python with the package installed. You can use the full path if needed:
   ```json
   "command": "/Users/ngarrett/Desktop/portfolios-mcp-financials/venv/bin/python3"
   ```

### Using Virtual Environment Python

If you're using a virtual environment, use the full path to the venv's Python:

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
        "PLANVIEW_CLIENT_ID": "your_client_id",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret",
        "PLANVIEW_TENANT_ID": "your_tenant_id",
        "USE_OAUTH": "true",
        "PLANVIEW_OKR_API_URL": "https://api-us.okrs.planview.com/api/rest",
        "PLANVIEW_OKR_BEARER_TOKEN": "your_okr_bearer_token"
      }
    }
  }
}
```

## Option 2: FastMCP Cloud (Alternative)

If you prefer not to run locally, you can use the FastMCP Cloud instance:

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "url": "https://portfolios-mcp.fastmcp.app/mcp",
      "env": {
        "PLANVIEW_API_URL": "https://scdemo520.pvcloud.com/polaris",
        "PLANVIEW_CLIENT_ID": "your_client_id",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret",
        "PLANVIEW_TENANT_ID": "your_tenant_id",
        "USE_OAUTH": "true",
        "PLANVIEW_OKR_API_URL": "https://api-us.okrs.planview.com/api/rest",
        "PLANVIEW_OKR_BEARER_TOKEN": "your_okr_bearer_token"
      }
    }
  }
}
```

## Verification

After configuring Claude Desktop:

1. **Restart Claude Desktop** (important!)
2. Start a new conversation
3. Check if the MCP server appears in Claude's available tools
4. Test with a simple command like:
   - "List my Planview projects"
   - "Create a new project called 'Test Project'"

## Troubleshooting

### Server not starting

- Check that Python path is correct
- Verify package is installed: `pip show planview-portfolios-mcp`
- Test manually: `python -m planview_portfolios_mcp.server`
- Check logs in Claude Desktop's console/debug output

### Authentication errors

- Verify `.env` file has correct credentials
- Check that `PLANVIEW_API_URL` includes `/polaris` path
- Test credentials with: `python test_creds_simple.py`

### Module not found errors

- Ensure package is installed: `pip install -e .`
- Check Python path matches the one in config
- Verify virtual environment is activated if using venv

### Tools not appearing

- Restart Claude Desktop after config changes
- Check Claude Desktop logs for MCP server errors
- Verify server starts without errors when run manually

## Available Tools

Once configured, you'll have access to:

- **Project Management**: `list_projects`, `get_project`, `create_project`, `update_project`
- **Financial Plans**: `read_financial_plan`, `discover_financial_plan_info`, `upsert_financial_plan`
- **Tasks**: `create_task`, `read_task`, `update_task`, `delete_task`
- **Resources**: `list_resources`, `get_resource`, `allocate_resource`
- **Work**: `list_work`, `get_work`
- **Utilities**: `oauth_ping`

See the README.md for detailed tool documentation.

