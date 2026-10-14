"""Planview key URI helpers. The model never sees this module."""

from __future__ import annotations

import uuid

from ..exceptions import PlanviewValidationError
from ..models import validate_task_key

_KEY_PREFIXES = ("key://", "ekey://", "search://")


def is_key_uri(value: str) -> bool:
    return isinstance(value, str) and value.startswith(_KEY_PREFIXES)


def plan_entity_key(project_id: str) -> str:
    """Turn a structureCode or existing key URI into key://2/$Plan/{id}."""
    raw = (project_id or "").strip()
    if not raw:
        raise PlanviewValidationError(
            "project_id is required. Pass a structureCode (e.g. '17286') "
            "or a key URI (key://2/$Plan/17286)."
        )
    if is_key_uri(raw):
        return raw
    return f"key://2/$Plan/{raw}"


def plan_id_from_entity_key(entity_key: str) -> str:
    """Best-effort structureCode from a $Plan key URI."""
    raw = (entity_key or "").strip()
    marker = "/$Plan/"
    if marker in raw:
        return raw.split(marker, 1)[1].split(":")[0].split("?")[0]
    return raw


def mint_task_ekey(namespace: str = "mcp") -> str:
    """External key so SOAP Create can be retried without duplicating tasks."""
    return f"ekey://2/{namespace}/{uuid.uuid4()}"


def coerce_task_keys(task_key: str | None, task_keys: list[str] | None) -> list[str]:
    keys: list[str] = []
    if task_key:
        keys.append(task_key)
    if task_keys:
        keys.extend(task_keys)
    if not keys:
        raise PlanviewValidationError(
            "Provide task_key or task_keys (key://, ekey://, or search://)."
        )
    validated: list[str] = []
    for i, key in enumerate(keys):
        try:
            validated.append(validate_task_key(key))
        except ValueError as e:
            raise PlanviewValidationError(f"task_keys[{i}] is invalid: {e}") from e
    return validated
