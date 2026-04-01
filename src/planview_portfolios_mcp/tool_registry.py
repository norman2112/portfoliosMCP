"""MCP tool definitions (names, routing hints, JSON input schemas) for the stdio server."""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from typing import Any

import mcp.types as types

# Routing hints (section 5 of product spec); prepended to each tool description.
ROUTING_HINTS: dict[str, str] = {
    "get_project": (
        "[LOCAL — single project read by ID. For listing/searching projects across a portfolio, "
        "use Beta MCP's listProjectsByPortfolioId or searchProjectByName instead.] "
    ),
    "create_project": (
        "[LOCAL — write operation. Beta MCP is read-only and cannot create projects.] "
    ),
    "update_project": (
        "[LOCAL — write operation. Beta MCP is read-only and cannot update projects.] "
    ),
    "delete_project": (
        "[LOCAL — write operation. Beta MCP is read-only and cannot delete projects. "
        "WARNING: destructive operation, deletes project and all child data.] "
    ),
    "get_project_attributes": (
        "[LOCAL — raw attribute list. For natural-language attribute search, use Beta MCP's "
        "searchAttributes instead.] "
    ),
    "get_project_wbs": (
        "[LOCAL — nested WBS tree with schedule data. For a flat hierarchy view, Beta MCP's "
        "getWorkHierarchy is an alternative.] "
    ),
    "list_field_reference": (
        "[LOCAL — field discovery for write operations. For read-side attribute discovery, use "
        "Beta MCP's searchAttributes instead.] "
    ),
    "get_work": (
        "[LOCAL — read any single work hierarchy node by ID (including portfolio-level nodes). "
        "For listing projects within a portfolio, use Beta MCP's listProjectsByPortfolioId.] "
    ),
    "list_work": (
        "[LOCAL — query work items with filter (e.g., project.Id .eq X). Limited filtering support. "
        "For portfolio-scoped project lists, use Beta MCP's listProjectsByPortfolioId instead.] "
    ),
    "update_work": (
        "[LOCAL — write operation. Beta MCP is read-only and cannot update work items.] "
    ),
    "get_work_attributes": (
        "[LOCAL — raw work attribute list. For natural-language attribute search, use Beta MCP's "
        "searchAttributes(entity='work').] "
    ),
    "create_task": "[LOCAL — write operation via SOAP. Beta MCP cannot create tasks.] ",
    "batch_create_tasks": (
        "[LOCAL — bulk write operation via SOAP. Beta MCP cannot create tasks.] "
    ),
    "read_task": (
        "[LOCAL — SOAP task read by key. For reading tasks with custom attributes by project or "
        "task ID, Beta MCP's getTasksByProjectIds or getTasksByTaskIds may be richer.] "
    ),
    "delete_task": "[LOCAL — write operation via SOAP. Beta MCP cannot delete tasks.] ",
    "batch_delete_tasks": (
        "[LOCAL — bulk write operation via SOAP. Beta MCP cannot delete tasks.] "
    ),
    "read_financial_plan": (
        "[LOCAL — SOAP financial plan read. No Beta MCP equivalent exists for financial plans.] "
    ),
    "upsert_financial_plan": (
        "[LOCAL — SOAP financial plan write. No Beta MCP equivalent exists.] "
    ),
    "discover_financial_plan_info": (
        "[LOCAL — financial plan discovery with smart fallback. No Beta MCP equivalent exists.] "
    ),
    "load_financial_plan_from_reference": (
        "[LOCAL — copy financial plan from reference project. No Beta MCP equivalent exists.] "
    ),
    "list_objectives": (
        "[LOCAL — OKR objectives list. No Beta MCP equivalent exists for OKRs.] "
    ),
    "list_all_objectives_with_key_results": (
        "[LOCAL — OKR objectives with key results. No Beta MCP equivalent exists.] "
    ),
    "get_key_results_for_objective": (
        "[LOCAL — OKR key results for a single objective. No Beta MCP equivalent exists.] "
    ),
    "oauth_ping": "[LOCAL — auth health check for this server's connection.] ",
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


# JSON Schema fragments per tool (parameters only; same shapes as pre-migration Python signatures).
INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "oauth_ping": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "get_project": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "Project id."},
            **_attrs_prop(),
        },
        "required": ["project_id"],
        "additionalProperties": False,
    },
    "get_project_attributes": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "create_project": {
        "type": "object",
        "properties": {
            "data": {
                **_obj(),
                "description": "Project creation payload (CreateProjectDtoPublic).",
            },
            **_attrs_prop(),
            "create_default_tasks": {
                "type": "boolean",
                "description": "If true, create five default sample tasks via SOAP.",
                "default": False,
            },
        },
        "required": ["data"],
        "additionalProperties": False,
    },
    "update_project": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string"},
            "updates": {**_obj(), "description": "Fields to patch (partial JSON object)."},
            **_attrs_prop(),
        },
        "required": ["project_id", "updates"],
        "additionalProperties": False,
    },
    "delete_project": {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The structureCode/ID of the project to delete.",
            },
        },
        "required": ["project_id"],
        "additionalProperties": False,
    },
    "list_field_reference": {
        "type": "object",
        "properties": {
            "category": {
                "type": ["string", "null"],
                "description": "Optional category filter (e.g. core_identity, dates).",
            },
        },
        "additionalProperties": False,
    },
    "get_project_wbs": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string"},
            "include_milestones": {"type": "boolean", "default": True},
            "max_depth": {"type": ["integer", "null"], "description": "Optional max tree depth."},
        },
        "required": ["project_id"],
        "additionalProperties": False,
    },
    "get_work": {
        "type": "object",
        "properties": {
            "work_id": {"type": "string"},
            **_attrs_prop(),
        },
        "required": ["work_id"],
        "additionalProperties": False,
    },
    "list_work": {
        "type": "object",
        "properties": {
            "filter": {
                "type": "string",
                "description": "Work API filter string (e.g. project.Id .eq 1906).",
            },
            **_attrs_prop(),
            "fields": {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "description": "Optional fields to include per item (trims payload).",
            },
        },
        "required": ["filter"],
        "additionalProperties": False,
    },
    "update_work": {
        "type": "object",
        "properties": {
            "work_id": {"type": "string"},
            "updates": {**_obj(), "description": "Fields to PATCH on the work item."},
            **_attrs_prop(),
        },
        "required": ["work_id", "updates"],
        "additionalProperties": False,
    },
    "get_work_attributes": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    "create_task": {
        "type": "object",
        "properties": {
            "task_data": {**_obj(), "description": "TaskDto2 fields (Description, FatherKey, ...)."},
            "options": {**_obj(), "description": "Optional WorkOptionsDto."},
        },
        "required": ["task_data"],
        "additionalProperties": False,
    },
    "batch_create_tasks": {
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {**_obj()},
                "description": "List of task dicts (each needs Description, FatherKey).",
            },
            "options": {**_obj(), "description": "Optional WorkOptionsDto for all tasks."},
        },
        "required": ["tasks"],
        "additionalProperties": False,
    },
    "read_task": {
        "type": "object",
        "properties": {"task_key": {"type": "string", "description": "key://, search://, or ekey://"}},
        "required": ["task_key"],
        "additionalProperties": False,
    },
    "delete_task": {
        "type": "object",
        "properties": {"task_key": {"type": "string"}},
        "required": ["task_key"],
        "additionalProperties": False,
    },
    "batch_delete_tasks": {
        "type": "object",
        "properties": {
            "task_keys": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["task_keys"],
        "additionalProperties": False,
    },
    "read_financial_plan": {
        "type": "object",
        "properties": {
            "entity_key": {"type": "string"},
            "version_key": {"type": "string"},
            "include_entries": {"type": "boolean", "default": False},
            "summary": {"type": "boolean", "default": False},
            "fields": {
                "type": ["array", "null"],
                "items": {"type": "string"},
                "description": "Optional top-level fields to keep.",
            },
        },
        "required": ["entity_key", "version_key"],
        "additionalProperties": False,
    },
    "upsert_financial_plan": {
        "type": "object",
        "properties": {
            "plan_data": {**_obj(), "description": "FinancialPlanDto-style payload with Lines."},
        },
        "required": ["plan_data"],
        "additionalProperties": False,
    },
    "discover_financial_plan_info": {
        "type": "object",
        "properties": {
            "entity_key": {"type": "string"},
            "version_key": {"type": "string", "default": "key://14/1"},
            "reference_entity_key": {"type": ["string", "null"]},
            "skip_target_read": {"type": "boolean", "default": False},
            "include_entries": {"type": "boolean", "default": False},
            "summary": {"type": "boolean", "default": False},
            "fields": {
                "type": ["array", "null"],
                "items": {"type": "string"},
            },
        },
        "required": ["entity_key"],
        "additionalProperties": False,
    },
    "load_financial_plan_from_reference": {
        "type": "object",
        "properties": {
            "target_project_id": {"type": "string"},
            "reference_project_id": {"type": "string"},
            "version_key": {"type": "string", "default": "key://14/1"},
            "scale_factor": {"type": "number", "default": 1.0},
            "confirm": {
                "type": "boolean",
                "default": False,
                "description": "Must be true to execute copy; false returns preview only.",
            },
        },
        "required": ["target_project_id", "reference_project_id"],
        "additionalProperties": False,
    },
    "list_objectives": {
        "type": "object",
        "properties": {
            "ids": {"type": ["string", "null"], "description": "Optional comma-separated objective ids."},
            "limit": {"type": "integer", "default": 10, "minimum": 1, "maximum": 500},
            "offset": {"type": "integer", "default": 0, "minimum": 0},
        },
        "additionalProperties": False,
    },
    "get_key_results_for_objective": {
        "type": "object",
        "properties": {"objective_id": {"type": "integer"}},
        "required": ["objective_id"],
        "additionalProperties": False,
    },
    "list_all_objectives_with_key_results": {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "default": 500, "minimum": 1, "maximum": 500},
            "include_key_results": {"type": "boolean", "default": True},
        },
        "additionalProperties": False,
    },
}

# Stable registration order (matches former server registration + logical grouping).
TOOL_NAMES: list[str] = [
    "oauth_ping",
    "get_project_attributes",
    "get_work_attributes",
    "get_project",
    "create_project",
    "update_project",
    "delete_project",
    "list_field_reference",
    "get_project_wbs",
    "list_work",
    "update_work",
    "get_work",
    "create_task",
    "batch_create_tasks",
    "batch_delete_tasks",
    "read_task",
    "delete_task",
    "discover_financial_plan_info",
    "load_financial_plan_from_reference",
    "read_financial_plan",
    "upsert_financial_plan",
    "list_objectives",
    "get_key_results_for_objective",
    "list_all_objectives_with_key_results",
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
