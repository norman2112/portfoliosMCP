# Planview Portfolios MCP Server

A Model Context Protocol (MCP) server for integrating with Planview Portfolios, built with [FastMCP](https://github.com/jlowin/fastmcp). 

**🌐 FastMCP Cloud URL**: `https://portfolios-mcp.fastmcp.app/mcp`

This server is hosted on FastMCP Cloud, so no local installation is required. Simply configure your MCP client (e.g., Claude Desktop) to connect to the cloud instance with your Planview API credentials.

## Features

### Project & Portfolio Management
- **List Projects**: Query projects with filtering by portfolio, status, and more
- **Get Project**: Retrieve detailed information about a specific project
- **Create Project**: Create new projects with comprehensive configuration
- **Update Project**: Modify existing project details and settings

### Resource Management
- **List Resources**: Browse team members with filtering by department, role, and availability
- **Get Resource**: View detailed resource information including allocations and capacity
- **Allocate Resource**: Assign resources to projects with flexible allocation percentages

## Installation

### Prerequisites
- Planview Portfolios API credentials (OAuth client_id, client_secret, and tenant ID)
- Access to FastMCP Cloud (no local installation required)

### Obtaining API Credentials

To use the Planview Portfolios API, you'll need three pieces of information:

1. **Client ID** (`PLANVIEW_CLIENT_ID`)
2. **Client Secret** (`PLANVIEW_CLIENT_SECRET`)
3. **Tenant ID** (`PLANVIEW_TENANT_ID`)

**Where to find these credentials:**

- **Planview Admin Portal**: Log into your Planview Portfolios instance and navigate to:
  - Administration → API Settings or
  - Settings → Integrations → API Credentials
  - Look for "OAuth Client" or "API Application" settings

- **Contact your Planview Administrator**: If you don't have admin access, your organization's Planview administrator can:
  - Create an OAuth client application
  - Provide you with the Client ID and Client Secret
  - Share your organization's Tenant ID

- **Planview Developer Portal**: Check the [Planview Developer Portal](https://developer.planview.com) for:
  - API documentation
  - Registration process for API access
  - Support resources

**Note**: The Tenant ID is typically your organization's unique identifier in Planview. It may be visible in your Planview URL (e.g., `https://yourcompany.planview.com`) or provided by your administrator.

### Setup

This MCP server is hosted on FastMCP Cloud, so no local installation is required. You just need to configure your Claude Desktop or MCP client to connect to the cloud instance.

1. **Get your Planview API credentials**:
   - See the [Obtaining API Credentials](#obtaining-api-credentials) section above
   - **Need help finding your credentials?** See [CREDENTIALS.md](CREDENTIALS.md) for detailed instructions.

2. **Configure your MCP client** (see [Configuring with Claude Desktop](#configuring-with-claude-desktop) below)

## Usage

### Configuring with Claude Desktop

The Planview Portfolios MCP server is hosted on FastMCP Cloud. Add the following to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "url": "https://portfolios-mcp.fastmcp.app/mcp",
      "env": {
        "PLANVIEW_API_URL": "https://your-instance.pvcloud.com",
        "PLANVIEW_CLIENT_ID": "your_client_id",
        "PLANVIEW_CLIENT_SECRET": "your_client_secret",
        "PLANVIEW_TENANT_ID": "your_tenant_id",
        "USE_OAUTH": "true"
      }
    }
  }
}
```

**Note**: Replace the placeholder values with your actual Planview API credentials:
- `PLANVIEW_API_URL`: Your Planview instance base URL (e.g., `https://scdemo504.pvcloud.com` - without `/polaris` or trailing slashes)
- `PLANVIEW_CLIENT_ID`: Your OAuth client ID
- `PLANVIEW_CLIENT_SECRET`: Your OAuth client secret  
- `PLANVIEW_TENANT_ID`: Your tenant ID

The server will automatically handle OAuth token management (tokens are valid for 60 minutes and automatically refreshed).

### Local Development (Optional)

If you want to run the server locally for development or testing:

1. **Clone or navigate to the project directory**:
   ```bash
   cd planview-portfolios-mcp
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Planview API credentials
   ```

5. **Run the server**:
   ```bash
   python -m planview_portfolios_mcp.server
   ```

6. **Test OAuth token retrieval** (optional):
   ```bash
   python get_token.py
   ```

## Available Tools

### Project Management Tools

#### `list_projects`
List projects with optional filtering.

**Parameters:**
- `portfolio_id` (optional): Filter by portfolio ID
- `status` (optional): Filter by status (e.g., 'active', 'completed', 'on-hold')
- `limit` (default: 50): Maximum number of results

#### `get_project`
Get detailed information about a specific project.

**Parameters:**
- `project_id` (required): The unique identifier of the project

#### `create_project`
Create a new project.

**Parameters:**
- `name` (required): Project name
- `description` (optional): Project description
- `portfolio_id` (optional): Associated portfolio ID
- `start_date` (optional): Start date (ISO format: YYYY-MM-DD)
- `end_date` (optional): End date (ISO format: YYYY-MM-DD)
- `budget` (optional): Project budget

#### `update_project`
Update an existing project.

**Parameters:**
- `project_id` (required): The project to update
- `name` (optional): New project name
- `description` (optional): New description
- `status` (optional): New status
- `start_date` (optional): New start date
- `end_date` (optional): New end date
- `budget` (optional): New budget

### Resource Management Tools

#### `list_resources`
List available resources (team members).

**Parameters:**
- `department` (optional): Filter by department
- `role` (optional): Filter by role
- `available` (optional): Filter by availability (true/false)
- `limit` (default: 50): Maximum number of results

#### `get_resource`
Get detailed information about a specific resource.

**Parameters:**
- `resource_id` (required): The unique identifier of the resource

#### `allocate_resource`
Allocate a resource to a project.

**Parameters:**
- `resource_id` (required): The resource to allocate
- `project_id` (required): The target project
- `allocation_percentage` (required): Allocation percentage (0-100)
- `start_date` (required): Allocation start date (ISO format: YYYY-MM-DD)
- `end_date` (required): Allocation end date (ISO format: YYYY-MM-DD)
- `role` (optional): Role for this allocation

## Development

This section is for developers who want to contribute to or modify the server code.

### Running Tests

```bash
pytest
```

### Code Quality

Format code with Black:
```bash
black src/
```

Lint with Ruff:
```bash
ruff check src/
```

Type check with mypy:
```bash
mypy src/
```

### Project Structure

```
planview-portfolios-mcp/
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── src/
│   └── planview_portfolios_mcp/
│       ├── __init__.py
│       ├── server.py          # Main FastMCP server
│       ├── config.py           # Configuration management
│       ├── client.py           # Shared HTTP client with retry logic
│       ├── exceptions.py       # Custom exception types
│       ├── models.py           # Pydantic validation models
│       ├── logging_config.py   # Logging configuration
│       └── tools/
│           ├── __init__.py
│           ├── projects.py     # Project management tools
│           └── resources.py    # Resource management tools
└── tests/
    └── __init__.py
```

## Configuration

When connecting to the FastMCP Cloud instance, configure these environment variables in your MCP client (e.g., Claude Desktop's `claude_desktop_config.json`):

**Required for OAuth Authentication:**
- `PLANVIEW_CLIENT_ID`: OAuth client ID (required)
- `PLANVIEW_CLIENT_SECRET`: OAuth client secret (required)
- `PLANVIEW_TENANT_ID`: Your tenant identifier (required)

**Optional Configuration:**
- `PLANVIEW_API_URL`: Base URL for Planview API (default: https://api.planview.com)
- `USE_OAUTH`: Enable OAuth authentication (default: true)
- `PLANVIEW_API_KEY`: Legacy API key (deprecated, use OAuth instead)

**OAuth Token Management**: The FastMCP Cloud server automatically handles OAuth token lifecycle:
- Tokens are obtained using the `client_credentials` grant type
- Tokens are cached and automatically refreshed when they expire (60 minutes)
- Failed requests with 401 status will trigger automatic token refresh

**Note**: For local development, see the [Local Development](#local-development-optional) section above. The server also supports additional configuration options like `API_TIMEOUT` and `MAX_RETRIES` for local instances.

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted with Black before submitting.

## Support

For issues or questions about this MCP server, please open an issue on the repository.

For Planview Portfolios API documentation, visit the official Planview developer portal.
