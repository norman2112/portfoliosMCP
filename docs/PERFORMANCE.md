# MCP Server Performance Guide

This guide describes how to enable and use performance instrumentation in the Planview Portfolios MCP server.

## Enabling Performance Logging

Set the following environment variable (e.g. in Claude Desktop config or `.env`):

```bash
MCP_PERFORMANCE_LOGGING=true
```

When enabled:

- **Timing**: Each MCP tool call is measured (start/end, duration in ms).
- **Output**: Structured JSON lines are written to **stderr** (MCP standard).
- **Shutdown**: On server exit, a short performance summary is logged if any requests were handled.

Example log line:

```json
{"tool": "create_project", "start_time": "2026-02-03T10:26:04.123Z", "duration_ms": 1333, "success": true}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PERFORMANCE_LOGGING` | `false` | Enable performance timing logs |
| `MCP_REQUEST_TIMEOUT_SECONDS` | `30` | REST API request timeout |
| `MCP_SOAP_TIMEOUT_SECONDS` | `60` | SOAP API request timeout |
| `MCP_CACHE_ENABLED` | `true` | Enable in-memory TTL cache |
| `MCP_CACHE_TTL_SECONDS` | `3600` | Cache TTL (1 hour) |
| `MCP_STRIP_NULL_VALUES` | `true` | Strip nulls from responses (when implemented) |
| `MCP_VERBOSE_RESPONSES` | `false` | Include full metadata in responses |

## Response Size Optimization

### Financial plan discovery

`discover_financial_plan_info` can return very large payloads. Use these parameters to reduce size:

- **`include_entries=False`** (default for this tool): Omits `EntryDto` arrays from each line. Use when you only need account/period structure.
- **`summary=True`**: Returns only `account_keys` and `period_keys` (minimal response).
- **`fields`**: List of top-level data fields to return (e.g. `["EntityKey", "VersionKey", "Lines"]`).

Example:

```python
# Structure only (accounts + periods, no entry values)
discover_financial_plan_info(ctx, entity_key="key://2/$Plan/17291", include_entries=False)

# Minimal (just keys)
discover_financial_plan_info(ctx, entity_key="key://2/$Plan/17291", summary=True)
```

### read_financial_plan

Same options are available: `include_entries`, `summary`, and `fields`. Default for `include_entries` is `True` so existing callers keep full data.

## Caching

Reference data (e.g. structure) can be cached in memory with a TTL:

- **Enabled**: `MCP_CACHE_ENABLED=true` (default).
- **TTL**: `MCP_CACHE_TTL_SECONDS=3600` (1 hour).
- **Clear**: Use the `clear_cache` tool (if registered) or restart the server.

Cache is process-local and is lost on restart.

## Interpreting Timing Metrics

- **duration_ms**: End-to-end time for the tool call.
- **success**: Whether the tool completed without raising.
- On shutdown, the server logs a short summary: total requests, average duration, slowest tool, and (if tracked) API call count.

## Troubleshooting Slow Operations

1. **Enable performance logging** and reproduce the slow flow; check which tool has the highest `duration_ms`.
2. **Financial plan tools**: Prefer `include_entries=False` or `summary=True` when you don’t need full entry values.
3. **Timeouts**: Increase `MCP_REQUEST_TIMEOUT_SECONDS` or `MCP_SOAP_TIMEOUT_SECONDS` for slow backends; fix underlying slowness where possible.
4. **Caching**: Ensure `MCP_CACHE_ENABLED=true` so repeated structure lookups can be served from cache.

## Performance Targets (Reference)

| Operation | Target |
|-----------|--------|
| create_project | < 2s |
| batch_create_tasks (5 tasks) | < 3s |
| discover_financial_plan_info (optimized) | < 1s |
| upsert_financial_plan | < 4s |
| list operations | < 1s |

These are goals for tuning; actual times depend on network and Planview instance.
