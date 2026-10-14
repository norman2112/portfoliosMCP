"""Job tool: create, read, or delete tasks (SOAP)."""

from __future__ import annotations

from typing import Any

from ..exceptions import PlanviewValidationError
from ..performance import log_performance
from ..utils.actions import normalize_action, require
from ..utils.key_uri import coerce_task_keys, mint_task_ekey, plan_entity_key
from .tasks import batch_create_tasks, batch_delete_tasks, read_task

_ACTIONS = ("create", "read", "delete")


def _ci_get(task: dict[str, Any], name: str) -> Any:
    want = name.lower()
    for key, value in task.items():
        if isinstance(key, str) and key.lower() == want:
            return value
    return None


def _ensure_father_and_ekey(
    task: dict[str, Any],
    father_key: str | None,
) -> dict[str, Any]:
    out = dict(task)
    if _ci_get(out, "FatherKey") is None:
        if not father_key:
            raise PlanviewValidationError(
                "Each task needs FatherKey, or pass project_id so it can be filled "
                "(key://2/$Plan/{structureCode})."
            )
        out["FatherKey"] = father_key
    if _ci_get(out, "Key") is None:
        out["Key"] = mint_task_ekey()
    if _ci_get(out, "Description") is None:
        raise PlanviewValidationError("Each task requires Description.")
    return out


@log_performance
async def manage_tasks(
    action: str,
    tasks: list[dict[str, Any]] | None = None,
    task_key: str | None = None,
    task_keys: list[str] | None = None,
    project_id: str | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Add, read, or delete tasks on a project (SOAP TaskService).

    Actions:
    - create: requires `tasks` (list; length 1 is fine). Each item needs Description.
      FatherKey can be omitted if project_id is set. An ekey:// is minted when Key
      is missing so retries do not duplicate. SOAP Create is not atomic — the
      response lists per-task success/failure. Retry only the failed items.
    - read: requires task_key or task_keys. SOAP responses often have null fields
      even on success; that does not mean create failed.
    - delete: requires task_key or task_keys. Cascades to children. Per-key results
      so you can retry only failures.

    Task updates are not supported via SOAP. Delete and recreate, or use the UI.
    For task reads with custom attributes, Anvi Prod getTasksByProjectIds may be richer.
    """
    action = normalize_action(action, _ACTIONS, "manage_tasks")

    if action == "create":
        require(action, "manage_tasks", tasks=tasks)
        if not isinstance(tasks, list):
            raise PlanviewValidationError("tasks must be a list of objects.")
        father = plan_entity_key(project_id) if project_id else None
        prepared = [_ensure_father_and_ekey(t, father) for t in tasks]
        result = await batch_create_tasks(tasks=prepared, options=options)
        result = dict(result)
        result["action"] = "create"
        if result.get("summary", {}).get("failed"):
            result["partial"] = True
            result["retry_hint"] = (
                "Retry only tasks with status=failed. Successful keys must not be resent."
            )
        return result

    keys = coerce_task_keys(task_key, task_keys)

    if action == "read":
        if len(keys) == 1:
            payload = await read_task(task_key=keys[0])
            return {"action": "read", "tasks": [payload], "echo_incomplete_is_normal": True}
        collected: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        for key in keys:
            try:
                collected.append(await read_task(task_key=key))
            except Exception as e:
                failed.append({"key": key, "error": str(e)})
        return {
            "action": "read",
            "tasks": collected,
            "failed": failed,
            "partial": bool(failed),
            "echo_incomplete_is_normal": True,
        }

    deleted = await batch_delete_tasks(task_keys=keys)
    deleted = dict(deleted)
    deleted["action"] = "delete"
    if deleted.get("summary", {}).get("failed"):
        deleted["partial"] = True
        deleted["retry_hint"] = "Retry only keys in failed[]. Do not resend successful deletes."
    return deleted
