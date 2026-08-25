"""Shared action-tool helpers. The model never sees this module."""

from __future__ import annotations

from typing import Any

from ..exceptions import PlanviewValidationError


def normalize_action(action: str | None, allowed: tuple[str, ...], tool: str) -> str:
    value = (action or "").strip().lower()
    if value not in allowed:
        raise PlanviewValidationError(
            f"{tool} action must be one of: {', '.join(allowed)}. Got {action!r}."
        )
    return value


def require(action: str, tool: str, **fields: Any) -> None:
    missing = [name for name, value in fields.items() if value in (None, "", [], {})]
    if missing:
        raise PlanviewValidationError(
            f"{tool} action={action} requires {', '.join(missing)}."
        )
