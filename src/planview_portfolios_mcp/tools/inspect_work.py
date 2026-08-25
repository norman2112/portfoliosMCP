"""Job tool: show WBS, get/list work nodes, or patch a work item."""

from __future__ import annotations

from typing import Any

from ..exceptions import PlanviewValidationError
from ..performance import log_performance
from ..utils.actions import normalize_action, require
from .projects import get_project_wbs
from .work import get_work, list_work, update_work

_ACTIONS = ("wbs", "get", "list", "update")


@log_performance
async def inspect_work(
    action: str = "wbs",
    project_id: str | None = None,
    work_id: str | None = None,
    filter: str | None = None,
    updates: dict[str, Any] | None = None,
    attributes: list[str] | str | None = None,
    fields: list[str] | None = None,
    include_milestones: bool = True,
    max_depth: int | None = None,
) -> dict[str, Any]:
    """Inspect a project's work hierarchy ($Plan) or update a work node.

    This is the work / WBS tree, not the strategy hierarchy ($Strategy). Strategy
    is out of scope. Parent structure codes for create come from the Planview UI,
    not from this tool — list/wbs need a project_id you already have.

    Actions:
    - wbs (default): nested WBS tree for a known project_id. Demo read path.
    - get: one work node by work_id (structure code already known).
    - list: work items under a known project. Prefer project_id (filter is built
      for you). Raw `filter` is a fallback (e.g. project.Id .eq 1906). Cannot
      enumerate portfolios or PPL-1 parents.
    - update: PATCH a work node. Some instances return 405 — use manage_project
      for primary-planning-level (project) fields instead.
    """
    inferred = (action or "").strip().lower()
    if not inferred:
        if updates:
            inferred = "update"
        elif work_id:
            inferred = "get"
        elif filter:
            inferred = "list"
        else:
            inferred = "wbs"
    action = normalize_action(inferred, _ACTIONS, "inspect_work")

    if action == "wbs":
        require(action, "inspect_work", project_id=project_id)
        return await get_project_wbs(
            project_id=project_id,
            include_milestones=include_milestones,
            max_depth=max_depth,
        )

    if action == "get":
        require(action, "inspect_work", work_id=work_id)
        return await get_work(work_id=work_id, attributes=attributes)

    if action == "list":
        flt = filter
        if not flt:
            if not project_id:
                raise PlanviewValidationError(
                    "inspect_work action=list requires a known project_id (preferred) "
                    "or filter (project.Id .eq {id}). This MCP cannot list the work "
                    "hierarchy or strategy hierarchy. Copy parent structure codes from "
                    "the Planview UI (Plan structure, PPL-1 work folder)."
                )
            flt = f"project.Id .eq {project_id}"
        return await list_work(filter=flt, attributes=attributes, fields=fields)

    require(action, "inspect_work", work_id=work_id, updates=updates)
    if not isinstance(updates, dict):
        raise PlanviewValidationError("updates must be a JSON object.")
    return await update_work(
        work_id=work_id,
        updates=updates,
        attributes=attributes,
    )
