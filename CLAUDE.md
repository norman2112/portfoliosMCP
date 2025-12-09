# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for integrating with Planview Portfolios, built with FastMCP. The server exposes Planview's project and resource management capabilities through MCP tools that can be used by Claude Desktop and other MCP clients.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Configure environment
cp .env.example .env
# Edit .env with Planview API credentials
```

### Running the Server
```bash
# Standard run
python -m planview_portfolios_mcp.server

# Alternative
python src/planview_portfolios_mcp/server.py
```

### Testing
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_filename.py

# Run with coverage
pytest --cov=src/planview_portfolios_mcp
```

### Code Quality
```bash
# Format code (Black)
black src/

# Lint code (Ruff)
ruff check src/

# Type checking (mypy)
mypy src/

# Run all quality checks
black src/ && ruff check src/ && mypy src/
```

## Architecture

### Core Components

**server.py**: FastMCP server initialization and tool registration. Creates a single FastMCP instance and registers all tool functions from the tools modules. The server's `main()` function runs the async event loop.

**config.py**: Centralized configuration using Pydantic Settings. The `PlanviewSettings` class automatically loads from `.env` file and provides validated configuration values. A global `settings` instance is imported throughout the codebase.

**tools/**: Contains tool implementations organized by domain:
- `projects.py`: Project and portfolio management tools (list, get, create, update)
- `resources.py`: Resource management tools (list, get, allocate)
- `__init__.py`: Exports all tool functions for registration

### Tool Pattern

All tools follow a consistent async pattern:
1. Accept a `ctx: Context` parameter from FastMCP (required first parameter)
2. Use httpx AsyncClient for API calls
3. Include authentication headers (Bearer token + X-Tenant-Id)
4. Return typed data (dict[str, Any] or list[dict[str, Any]])
5. Raise HTTP errors via `response.raise_for_status()`

### Authentication Flow

The current implementation uses Bearer token authentication with a tenant ID header:
- `Authorization: Bearer {settings.planview_api_key}`
- `X-Tenant-Id: {settings.planview_tenant_id}`

Note: The actual Planview API uses OAuth 2.0 client_credentials flow (see `portfolios-api.md`). Future implementations may need to implement token generation and refresh logic.

### Configuration Management

Settings are loaded from `.env` via Pydantic Settings with these behaviors:
- Case-insensitive environment variable matching
- Defaults provided for all settings except API credentials
- Extra environment variables are ignored
- UTF-8 encoding for .env file

## API Integration Notes

### Planview API Structure
- Base URL pattern: `{PLANVIEW_API_URL}/public-api/v1/{endpoint}`
- Authentication: OAuth 2.0 (tokens valid for 60 minutes)
- Rate limiting: One record at a time (no batching)
- Date format: ISO 8601 (YYYY-MM-DD)
- Case-sensitive: All attribute names and values

### Current Implementation Limitations
1. **Authentication**: Uses static API key instead of OAuth token generation
2. **Error Handling**: Basic HTTP error raising without retry logic (despite MAX_RETRIES setting)
3. **Pagination**: Not implemented (relies on limit parameter only)
4. **Batching**: Single-record operations only (matches API constraint)

### Tool-to-API Mapping
- `list_projects` → `GET /projects` (filter by portfolio_id, status)
- `get_project` → `GET /projects/{id}`
- `create_project` → `POST /projects`
- `update_project` → `PATCH /projects/{id}`
- `list_resources` → `GET /resources` (filter by department, role, available)
- `get_resource` → `GET /resources/{id}`
- `allocate_resource` → `POST /allocations`

Note: Actual Planview API endpoints use `/public-api/v1/` prefix. Current code assumes this is included in `PLANVIEW_API_URL`.

## Type Annotations

The project uses modern Python type annotations:
- Union types: `str | None` (not `Optional[str]`)
- Generics: `list[dict[str, Any]]` (not `List[Dict[str, Any]]`)
- Requires Python 3.10+ for this syntax

## Testing Approach

When creating tests:
1. Use pytest-asyncio for async tests
2. Mock httpx.AsyncClient for API calls
3. Test both success and error paths
4. Verify authentication headers are included
5. Test parameter validation and optional fields

## Common Modifications

### Adding a New Tool
1. Create async function in appropriate tools module
2. Follow tool pattern (ctx first, typed parameters, httpx async call)
3. Import and export in `tools/__init__.py`
4. Register with `mcp.tool()` decorator in `server.py`
5. Add tests for the new tool

### Adding New Configuration
1. Add field to `PlanviewSettings` class in `config.py`
2. Add default value or make required
3. Document in `.env.example`
4. Access via global `settings` instance

### Modifying API Calls
- All API calls use httpx AsyncClient with timeout from settings
- Headers must include both Authorization and X-Tenant-Id
- PATCH/POST requests need "Content-Type": "application/json"
- Use `response.raise_for_status()` for error handling
