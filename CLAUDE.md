# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server for integrating with Planview Portfolios, built with FastMCP. The server is hosted on FastMCP Cloud at `https://portfolios-mcp.fastmcp.app/mcp` and exposes Planview's project and resource management capabilities through MCP tools that can be used by Claude Desktop and other MCP clients.

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

**Production**: The server is hosted on FastMCP Cloud at `https://portfolios-mcp.fastmcp.app/mcp`. No local server setup is required for end users.

**Local Development**:
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

**server.py**: FastMCP server initialization and tool registration. Creates a single FastMCP instance and registers all tool functions from the tools modules. The server's `main()` function runs the async event loop. Includes cleanup handlers for graceful shutdown.

**config.py**: Centralized configuration using Pydantic Settings. The `PlanviewSettings` class automatically loads from `.env` file and provides validated configuration values. A global `settings` instance is imported throughout the codebase.

**client.py**: Shared HTTP client with connection pooling, automatic retry logic, and comprehensive error handling. Provides `get_client()` context manager for tools to use. Implements exponential backoff retry for transient failures (429, 502, 503, 504).

**exceptions.py**: Custom exception hierarchy for Planview API errors. Provides specific exception types for different error scenarios (auth, validation, rate limiting, server errors, etc.) with clear error messages.

**models.py**: Pydantic models for input validation and type safety. Includes models for project creation/updates, resource allocation, and list parameters. Validates date ranges, numeric constraints, and required fields.

**logging_config.py**: Structured logging configuration with JSON formatter support. Configurable log levels and output formats (JSON or standard text). Supports file and console handlers.

**tools/**: Contains tool implementations organized by domain:
- `projects.py`: Project and portfolio management tools (list, get, create, update)
- `resources.py`: Resource management tools (list, get, allocate)
- `__init__.py`: Exports all tool functions for registration

### Tool Pattern

All tools follow a consistent async pattern:
1. Accept a `ctx: Context` parameter from FastMCP (required first parameter)
2. Use Pydantic models from `models.py` for input validation
3. Use `get_client()` context manager from `client.py` for HTTP requests
4. Use `make_request()` helper for automatic retry and error handling
5. Return typed data (dict[str, Any] or list[dict[str, Any]])
6. Raise custom exceptions from `exceptions.py` for clear error messages

### Authentication Flow

The current implementation uses OAuth 2.0 client_credentials flow with automatic token management:
- `Authorization: Bearer {oauth_token}` (automatically obtained and refreshed)
- `X-Tenant-Id: {settings.planview_tenant_id}`

OAuth tokens are automatically:
- Fetched when the HTTP client is first created
- Cached in memory and reused until expiration (60 minutes)
- Automatically refreshed when expired
- Refreshed on 401 errors with automatic retry

Required environment variables:
- `PLANVIEW_API_URL`: Base URL of Planview instance (e.g., `https://scdemo504.pvcloud.com`)
- `PLANVIEW_CLIENT_ID`: OAuth client ID
- `PLANVIEW_CLIENT_SECRET`: OAuth client secret
- `PLANVIEW_TENANT_ID`: Tenant ID

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
1. **Pagination**: Not implemented (relies on limit parameter only)
2. **Batching**: Single-record operations only (matches API constraint)

### Error Handling & Retry Logic

The implementation includes robust error handling:
- Automatic retry with exponential backoff for transient failures (429, 502, 503, 504)
- Custom exception types for different error scenarios
- Connection pooling and reuse for better performance
- Configurable retry attempts via `MAX_RETRIES` setting

### Tool-to-API Mapping

**REST API Tools:**
- `list_projects` → `GET /work` (uses filter parameter, projects are work items at PPL)
- `get_project` → `GET /projects/{id}`
- `create_project` → `POST /projects` (requires `description` and `parent.structureCode`)
- `update_project` → `PATCH /projects/{id}`
- `list_work` → `GET /work` (with filter parameter)
- `get_work` → `GET /work/{id}`
- `list_resources` → `GET /resources` (filter by department, role, available)
- `get_resource` → `GET /resources/{id}`
- `allocate_resource` → `POST /allocations`

**SOAP API Tools:**
- `create_task` / `batch_create_tasks` → `ITaskService3.Create` (SOAP operation)
- `read_task` → `ITaskService3.Read` (SOAP operation)
- `delete_task` / `batch_delete_tasks` → `ITaskService3.Delete` (SOAP operation)

Task **updates** are not exposed (`ITaskService3.Update`): zeep does not serialize the WSDL’s `dtos` input reliably. Workaround: delete and recreate the task (or use the Planview UI).

Note: Actual Planview API endpoints use `/public-api/v1/` prefix. The `PLANVIEW_API_URL` should be the base URL including the `/polaris` path but without the `/public-api/v1/` prefix (e.g., `https://scdemo504.pvcloud.com/polaris`).

### SOAP API Integration

The server supports both REST and SOAP APIs. SOAP operations use the TaskService web service.

**SOAP Endpoint Configuration:**
- SOAP service URL: `{PLANVIEW_API_URL}/planview/services/TaskService.svc`
- WSDL URL: `{PLANVIEW_API_URL}/planview/services/TaskService.svc?wsdl`
- Service binding: `ITaskService3` (latest version)
- Configurable via `SOAP_SERVICE_PATH` setting (default: `/planview/services/TaskService.svc`)

**SOAP Authentication:**
- Uses same OAuth 2.0 tokens as REST API
- Token added to SOAP header: `Authorization: Bearer {token}`
- `X-Tenant-Id` header also included
- Token refresh handled automatically (same as REST)

**SOAP Response Handling:**
- All SOAP operations return `OpenSuiteResult` structure:
  - `Successes`: List of successful operations (DTO contains keys only)
  - `Failures`: List of failed operations (DTO contains full data + error messages)
  - `Warnings`: List of warnings (DTO contains full data + warning messages)
  - `GeneralErrorMessage`: Non-task-specific errors (database, connectivity)
- Responses converted to consistent dict format matching REST API patterns
- Failures raise `PlanviewValidationError` with detailed error messages
- General errors raise `PlanviewServerError`

**Key URI Formats:**
SOAP operations support three key URI formats:
- `key://2/$Plan/12345` - Direct key reference (most efficient)
- `search://2/$Plan?description=Task Name` - Search-based lookup
- `ekey://2/namespace/external_key` - External key reference (recommended for creates)

**SOAP Client Pattern:**
- Use `get_soap_client()` context manager from `soap_client.py`
- Use `make_soap_request()` helper for automatic retry and error handling
- zeep library handles WSDL parsing and XML serialization
- AsyncTransport provides async support via httpx

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

**REST API Calls:**
- Use `get_client()` context manager to get shared HTTP client
- Use `make_request()` helper function for automatic retry and error handling
- All requests automatically include authentication headers (Authorization + X-Tenant-Id)
- PATCH/POST requests automatically include "Content-Type": "application/json"
- Custom exceptions are raised automatically based on HTTP status codes
- Use Pydantic models from `models.py` for input validation before API calls

**SOAP API Calls:**
- Use `get_soap_client()` context manager to get zeep Client instance
- Use `make_soap_request()` helper function for automatic retry and error handling
- All SOAP requests automatically include authentication headers (Authorization + X-Tenant-Id)
- zeep handles XML serialization and SOAP envelope construction
- Use Pydantic models from `models.py` for input validation (convert to dict with `model_dump(by_alias=True)`)
- Service name: `ITaskService3` (defined as constant in tools)
- Operations exposed as tools: Create, Read, Delete (Update is omitted for the reason above; method names otherwise match SOAP operation names)
