"""Job tool: create, get, update, delete a project, or list writable fields."""

from __future__ import annotations

from typing import Any

from ..exceptions import PlanviewValidationError
from ..performance import log_performance
from ..utils.actions import normalize_action, require
from .projects import (
    create_project,
    delete_project,
    get_project,
    get_project_attributes,
    list_field_reference,
    update_project,
)

_ACTIONS = ("create", "get", "update", "delete", "fields")


@log_performance
async def manage_project(
    action: str,
    project_id: str | None = None,
    data: dict[str, Any] | None = None,
    updates: dict[str, Any] | None = None,
    attributes: list[str] | str | None = None,
    create_default_tasks: bool = False,
    category: str | None = None,
    include_live_catalog: bool = False,
) -> dict[str, Any]:
    """Create, get, update, or delete a project, or list writable fields.

    Actions:
    - create: requires `data.description` and `data.parent.structureCode`.
      parent.structureCode is the work-hierarchy ($Plan) folder one level above
      Primary Planning Level (PPL-1). Copy it from the Planview UI (Plan
      structure). This MCP cannot list parents, portfolios, or the strategy
      hierarchy — ask the user; do not guess. Do not use a $Strategy code.
      Optional scheduleStart/scheduleFinish (defaults to today and +6 months).
      Do NOT invent StructureCode attribute values (Status, Region, RAG, etc.):
      the field catalog no longer ships send-on-create defaults — they are
      tenant-specific. Omit them and let Planview apply product defaults, or
      PATCH after create with codes verified for this tenant.
      Region (Wbs37) is optional — never required for create. Tenant
      InvalidDefaultValues on Region (or similar optional fields) leave the
      field unset; create still succeeded — continue the demo, do not retry.
      Create responses promote API warnings to top-level `warnings` with
      `create_ok` / `demo_safe` when only optional defaults failed.
      Set create_default_tasks=true to seed five sample tasks (SOAP). If that
      seed partially fails, the project still exists — check task_seed.
    - get: requires project_id (already known). Use after a write to verify.
      The response includes parent.structureCode for reuse on later creates.
    - update: requires project_id and updates (partial JSON). Field IDs are
      case-sensitive. Call action=fields first if you do not know the IDs.
      StructureCode values are tenant-specific — verify before sending.
    - delete: requires project_id. Destructive — removes the project and children.
    - fields: curated writable field catalog (~120 demo fields). Optional category
      filter. Catalog `example` values are NOT safe to send on create — they are
      instance-specific. Set include_live_catalog=true only if a field is missing.

    Out of scope: listing the work tree, browsing $Strategy, discovering a parent
    without a code from the UI. Use Anvi Prod for portfolio/strategy reads.
    """
    action = normalize_action(action, _ACTIONS, "manage_project")

    if action == "create":
        require(action, "manage_project", data=data)
        if not isinstance(data, dict):
            raise PlanviewValidationError("data must be a JSON object.")
        result = await create_project(
            data=data,
            attributes=attributes,
            create_default_tasks=create_default_tasks,
        )
        result = dict(result) if isinstance(result, dict) else {"data": result}
        _promote_create_warnings(result)
        if create_default_tasks:
            seed = _task_seed_from_create(result)
            result["task_seed"] = seed
            if seed["requested"] and seed["created"] < seed["requested"]:
                result["partial"] = True
        return result

    if action == "get":
        require(action, "manage_project", project_id=project_id)
        return await get_project(project_id=project_id, attributes=attributes)

    if action == "update":
        require(action, "manage_project", project_id=project_id, updates=updates)
        if not isinstance(updates, dict):
            raise PlanviewValidationError("updates must be a JSON object.")
        return await update_project(
            project_id=project_id,
            updates=updates,
            attributes=attributes,
        )

    if action == "delete":
        require(action, "manage_project", project_id=project_id)
        return await delete_project(project_id=project_id)

    # fields
    catalog = await list_field_reference(category=category)
    if include_live_catalog:
        live = await get_project_attributes()
        return {
            "catalog": catalog,
            "live_attributes": live,
            "hint": (
                "Catalog example values are tenant-specific demos and must not be "
                "sent on create. Prefer live_attributes or omit StructureCode fields."
            ),
        }
    if isinstance(catalog, dict):
        catalog = dict(catalog)
        catalog["hint"] = (
            "Do not send catalog example StructureCode values on create — they are "
            "often invalid on this tenant (InvalidDefaultValues). Omit attributes "
            "or verify codes via include_live_catalog=true / the Planview UI."
        )
    return catalog


# Optional StructureCodes Planview may try to default on create. Failures here
# must not be treated as create failures in demos (field simply stays unset).
_OPTIONAL_DEFAULT_HINTS = (
    "wbs37",
    "region",
    "2263",
    "invaliddefaultvalues",
    "invaliddefaultvalue",
)


def _warning_text(w: Any) -> str:
    if isinstance(w, dict):
        parts = [w.get("codeDesc"), w.get("code"), w.get("message")]
        return " ".join(str(p) for p in parts if p is not None).lower()
    return str(w).lower()


def _is_optional_default_warning(w: Any) -> bool:
    text = _warning_text(w)
    if "invaliddefault" in text.replace(" ", ""):
        return True
    return any(token in text for token in _OPTIONAL_DEFAULT_HINTS)


def _promote_create_warnings(result: dict[str, Any]) -> None:
    """Lift meta.warnings; mark optional-default noise as demo-safe."""
    meta = result.get("meta")
    raw: list[Any] = []
    if isinstance(meta, dict):
        warnings = meta.get("warnings")
        if isinstance(warnings, list):
            raw = [w for w in warnings if w not in (None, "", {})]
    top = result.get("warnings")
    if isinstance(top, list):
        for w in top:
            if w not in (None, "", {}) and w not in raw:
                raw.append(w)

    result["warnings"] = raw
    result["has_warnings"] = bool(raw)
    # Create HTTP succeeded if we got here with a project payload.
    result["create_ok"] = True
    if not raw:
        result["demo_safe"] = True
        return

    optional_only = all(_is_optional_default_warning(w) for w in raw)
    result["demo_safe"] = optional_only
    if optional_only:
        result["warning_hint"] = (
            "Create succeeded. Planview skipped one or more optional tenant "
            "defaults (often Region/Wbs37 — InvalidDefaultValues). Those fields "
            "are unset and are NOT required. Continue the demo; do not retry "
            "create and do not treat this as a failure."
        )
        return

    codes: list[str] = []
    for w in raw:
        if isinstance(w, dict):
            code = w.get("codeDesc") or w.get("code") or w.get("message")
            if code is not None:
                codes.append(str(code))
        else:
            codes.append(str(w))
    code_list = ", ".join(sorted(set(codes))) if codes else "see warnings"
    result["warning_hint"] = (
        "Project was created (create_ok=true), with non-fatal warnings "
        f"({code_list}). Do not retry create. Optional fields may be unset; "
        "PATCH via manage_project action=update only if the demo needs them."
    )


def _task_seed_from_create(result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data")
    project: dict[str, Any] = {}
    if isinstance(data, list) and data and isinstance(data[0], dict):
        project = data[0]
    elif isinstance(data, dict):
        project = data
    default_tasks = project.get("defaultTasks") or {}
    tasks = default_tasks.get("tasks") if isinstance(default_tasks, dict) else []
    if not isinstance(tasks, list):
        tasks = []
    created = default_tasks.get("created") if isinstance(default_tasks, dict) else len(tasks)
    try:
        created_n = int(created)
    except (TypeError, ValueError):
        created_n = len(tasks)
    return {
        "requested": 5,
        "created": created_n,
        "tasks": tasks,
        "hint": (
            None
            if created_n >= 5
            else "Project exists but some default tasks were not created. "
            "Use manage_tasks to add the rest; do not retry create."
        ),
    }
