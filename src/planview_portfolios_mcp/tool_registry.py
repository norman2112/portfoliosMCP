"""MCP tool definitions (names, routing hints, JSON input schemas) for the stdio server."""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from typing import Any

import mcp.types as types

# Routing hints prepended to each tool description.
ROUTING_HINTS: dict[str, str] = {
    "test_connection": (
        "[LOCAL — diagnose this server's Planview OAuth connection. "
        "Returns structured checks (config, token, ping) instead of a bare 401.] "
    ),
    "manage_project": (
        "[LOCAL — create/get/update/delete a project, or list writable fields. "
        "Create requires parent.structureCode from the Planview UI (work hierarchy, "
        "PPL-1 folder). This server cannot list portfolios or the strategy hierarchy. "
        "Do not invent StructureCode attribute defaults on create — omit them or "
        "verify for this tenant. Region is optional; InvalidDefaultValues on "
        "optional defaults is demo_safe (create_ok) — continue, do not retry. "
        "Anvi Prod is read-only and cannot write. For listing/searching projects across "
        "a portfolio, use Anvi Prod's listProjectsByPortfolioId or searchProjectByName. "
        "For strategy trees, use Anvi Prod — $Strategy is out of scope here.] "
    ),
    "inspect_work": (
        "[LOCAL — WBS tree, work-node get/list, or PATCH a phase/task for a known "
        "project_id. This is the work hierarchy ($Plan), not strategy ($Strategy). "
        "Cannot enumerate the Plan tree or list parents without an id — get parent "
        "structure codes from the Planview UI. For portfolio-scoped project lists, "
        "use Anvi Prod's listProjectsByPortfolioId.] "
    ),
    "manage_tasks": (
        "[LOCAL — create/read/delete tasks via SOAP. Anvi Prod cannot write tasks. "
        "For task reads with custom attributes, Anvi Prod's getTasksByProjectIds may be richer.] "
    ),
    "manage_financial_plan": (
        "[LOCAL — read, discover, upsert, or copy a financial plan via SOAP. "
        "discover returns accounts/periods as [{key, description}] plus bare key lists. "
        "Period ids are not contiguous across fiscal years — never invent by incrementing. "
        "upsert accepts flat Lines or SOAP/read envelopes. "
        "No Anvi Prod equivalent exists for financial plans.] "
    ),
}

_LOCAL_LINE = re.compile(r"^\[LOCAL[^\]]*\]\s*\n*", re.MULTILINE)


def tool_description(fn: Callable[..., Any], name: str) -> str:
    """Prepend routing hint and drop a duplicate leading [LOCAL …] block from the function doc."""
    hint = ROUTING_HINTS.get(name, "").strip()
    raw = inspect.getdoc(fn) or ""
    body = _LOCAL_LINE.sub("", raw, count=1).strip()
    if hint:
        return f"{hint}\n\n{body}".strip()
    return body


def _obj(additional: bool = True) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": additional}


def _attrs_prop() -> dict[str, Any]:
    return {
        "attributes": {
            "description": "Optional attributes to return (comma-separated string or list of names).",
            "oneOf": [
                {"type": "array", "items": {"type": "string"}},
                {"type": "string"},
                {"type": "null"},
            ],
        }
    }


INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "test_connection": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "manage_project": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "get", "update", "delete", "fields"],
                "description": "create | get | update | delete | fields",
            },
            "project_id": {
                "type": ["string", "null"],
                "description": "Required for get, update, and delete. This is the project's structure code, not a strategy code.",
            },
            "data": {
                **_obj(),
                "description": (
                    "Create payload. Requires description and parent.structureCode. "
                    "parent.structureCode is the work-hierarchy folder one level above "
                    "Primary Planning Level (PPL-1). Copy it from the Planview UI "
                    "(Plan structure). This MCP cannot list parents. Do not use a "
                    "strategy-hierarchy ($Strategy) code."
                ),
            },
            "updates": {
                **_obj(),
                "description": "Partial fields to PATCH (update).",
            },
            **_attrs_prop(),
            "create_default_tasks": {
                "type": "boolean",
                "default": False,
                "description": "If true, seed five sample tasks via SOAP after create.",
            },
            "category": {
                "type": ["string", "null"],
                "description": "Optional fields-catalog category (core_identity, dates, status_assessments, ...).",
            },
            "include_live_catalog": {
                "type": "boolean",
                "default": False,
                "description": "If true with action=fields, also fetch the live attribute list.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
    "inspect_work": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["wbs", "get", "list", "update"],
                "default": "wbs",
                "description": "wbs (default) | get | list | update",
            },
            "project_id": {
                "type": ["string", "null"],
                "description": (
                    "Required for wbs. Preferred for list (builds project.Id .eq {id}). "
                    "Must already be known — this tool cannot discover project or parent ids."
                ),
            },
            "work_id": {
                "type": ["string", "null"],
                "description": "Required for get and update. Work-hierarchy structure code, not $Strategy.",
            },
            "filter": {
                "type": ["string", "null"],
                "description": (
                    "Raw work API filter. Prefer project_id. Documented form is "
                    "project.Id .eq {id}. Cannot list the Plan or strategy tree from here."
                ),
            },
            "updates": {**_obj(), "description": "Fields to PATCH (update)."},
            **_attrs_prop(),
            "fields": {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "description": "Optional per-item fields for list (trims payload).",
            },
            "include_milestones": {"type": "boolean", "default": True},
            "max_depth": {
                "type": ["integer", "null"],
                "description": "Optional max WBS tree depth from the project root.",
            },
        },
        "additionalProperties": False,
    },
    "manage_tasks": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "read", "delete"],
                "description": "create | read | delete",
            },
            "tasks": {
                "type": ["array", "null"],
                "items": {**_obj()},
                "description": "Create payload. Each item needs Description. FatherKey optional if project_id is set.",
            },
            "task_key": {
                "type": ["string", "null"],
                "description": "Single key://, ekey://, or search:// for read/delete.",
            },
            "task_keys": {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "description": "Multiple keys for read/delete.",
            },
            "project_id": {
                "type": ["string", "null"],
                "description": "Fills FatherKey on create when a task omits it.",
            },
            "options": {**_obj(), "description": "Optional WorkOptionsDto for create."},
        },
        "required": ["action"],
        "additionalProperties": False,
    },
    "manage_financial_plan": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["read", "discover", "upsert", "copy"],
                "description": "read | discover | upsert | copy (copy is dry-run unless confirm=true)",
            },
            "project_id": {
                "type": ["string", "null"],
                "description": "Target project structureCode for read/discover/upsert, or copy target if target_project_id omitted.",
            },
            "entity_key": {
                "type": ["string", "null"],
                "description": "SOAP entity key. Optional if project_id is set (becomes key://2/$Plan/{id}).",
            },
            "version_key": {
                "type": "string",
                "default": "key://14/1",
                "description": "Financial plan version. Default Actual/Forecast.",
            },
            "include_entries": {"type": "boolean", "default": False},
            "summary": {"type": "boolean", "default": False},
            "fields": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
            "reference_project_id": {
                "type": ["string", "null"],
                "description": "Reference project for discover fallback or copy source.",
            },
            "reference_entity_key": {
                "type": ["string", "null"],
                "description": "SOAP key for the reference project (optional if reference_project_id is set).",
            },
            "skip_target_read": {"type": "boolean", "default": False},
            "plan_data": {
                **_obj(),
                "description": (
                    "Upsert payload. Preferred flat shape: "
                    '{EntityKey, VersionKey, Lines:[{AccountKey, Unit, Entries:[{PeriodKey, Value}]}]}. '
                    "Also accepts SOAP/read envelopes (Lines.FinancialPlanLineDto, "
                    "Entries.EntryDto) — they are normalized. Prefer discover "
                    "account_keys + period_keys over feeding a stripped read back."
                ),
            },
            "target_project_id": {
                "type": ["string", "null"],
                "description": "Copy target. Defaults to project_id.",
            },
            "scale_factor": {"type": "number", "default": 1.0},
            "confirm": {
                "type": "boolean",
                "default": False,
                "description": "copy: false = preview only; true = write.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}

TOOL_NAMES: list[str] = [
    "test_connection",
    "manage_project",
    "inspect_work",
    "manage_tasks",
    "manage_financial_plan",
]


def build_tool_definitions(
    implementations: dict[str, Callable[..., Awaitable[Any]]],
) -> list[types.Tool]:
    """Build MCP Tool list from implementations (must cover every name in TOOL_NAMES)."""
    out: list[types.Tool] = []
    for name in TOOL_NAMES:
        fn = implementations[name]
        schema = INPUT_SCHEMAS[name]
        out.append(
            types.Tool(
                name=name,
                description=tool_description(fn, name),
                inputSchema=schema,
            )
        )
    return out


def bind_arguments(fn: Callable[..., Any], arguments: dict[str, Any] | None) -> dict[str, Any]:
    """Filter call arguments to parameters accepted by ``fn``."""
    params = inspect.signature(fn).parameters
    allowed = set(params.keys())
    args = arguments or {}
    return {k: v for k, v in args.items() if k in allowed}
