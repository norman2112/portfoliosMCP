# Planview Portfolios MCP Server

A Model Context Protocol (MCP) server for integrating with Planview Portfolios, built with [FastMCP](https://github.com/jlowin/fastmcp).

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
- Python 3.10 or higher
- Planview Portfolios API credentials (API key and tenant ID)

### Setup

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
   # Or for development:
   pip install -r requirements-dev.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Planview API credentials
   ```

5. **Edit `.env` with your credentials**:
   ```bash
   PLANVIEW_API_URL=https://api.planview.com
   PLANVIEW_API_KEY=your_actual_api_key
   PLANVIEW_TENANT_ID=your_actual_tenant_id
   ```

## Usage

### Running the Server

Start the MCP server:

```bash
python -m planview_portfolios_mcp.server
```

Or using the package directly:

```bash
python src/planview_portfolios_mcp/server.py
```

### Configuring with Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "planview-portfolios": {
      "command": "python",
      "args": [
        "-m",
        "planview_portfolios_mcp.server"
      ],
      "cwd": "/path/to/planview-portfolios-mcp",
      "env": {
        "PLANVIEW_API_KEY": "your_api_key",
        "PLANVIEW_TENANT_ID": "your_tenant_id"
      }
    }
  }
}
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
│       └── tools/
│           ├── __init__.py
│           ├── projects.py     # Project management tools
│           └── resources.py    # Resource management tools
└── tests/
    └── __init__.py
```

## Configuration

The server uses environment variables for configuration. See `.env.example` for all available options:

- `PLANVIEW_API_URL`: Base URL for Planview API
- `PLANVIEW_API_KEY`: Your API key for authentication
- `PLANVIEW_TENANT_ID`: Your tenant identifier
- `API_TIMEOUT`: Request timeout in seconds (default: 30)
- `MAX_RETRIES`: Maximum retry attempts for failed requests (default: 3)

## License

MIT

## Contributing

Contributions are welcome! Please ensure all tests pass and code is formatted with Black before submitting.

## Support

For issues or questions about this MCP server, please open an issue on the repository.

For Planview Portfolios API documentation, visit the official Planview developer portal.
