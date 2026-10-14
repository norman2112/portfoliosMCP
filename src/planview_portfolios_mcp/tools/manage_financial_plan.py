"""Job tool: read, discover, upsert, or copy a financial plan."""

from __future__ import annotations

from typing import Any

from ..exceptions import PlanviewValidationError
from ..performance import log_performance
from ..utils.actions import normalize_action, require
from ..utils.key_uri import plan_entity_key
from .financial_plan import (
    discover_financial_plan_info,
    load_financial_plan_from_reference,
    read_financial_plan,
    upsert_financial_plan,
)

_ACTIONS = ("read", "discover", "upsert", "copy")
_DEFAULT_VERSION = "key://14/1"


def _entity_key(
    *,
    action: str,
    entity_key: str | None,
    project_id: str | None,
) -> str:
    if entity_key and entity_key.strip():
        return entity_key.strip()
    if project_id and project_id.strip():
        return plan_entity_key(project_id)
    raise PlanviewValidationError(
        f"manage_financial_plan action={action} requires project_id or entity_key."
    )


@log_performance
async def manage_financial_plan(
    action: str,
    project_id: str | None = None,
    entity_key: str | None = None,
    version_key: str = _DEFAULT_VERSION,
    include_entries: bool = False,
    summary: bool = False,
    fields: list[str] | None = None,
    reference_project_id: str | None = None,
    reference_entity_key: str | None = None,
    skip_target_read: bool = False,
    plan_data: dict[str, Any] | None = None,
    target_project_id: str | None = None,
    scale_factor: float = 1.0,
    confirm: bool = False,
) -> dict[str, Any]:
    """Show, write, or copy financials for a project (SOAP FinancialPlanService).

    Actions:
    - read: plan for project_id (or entity_key) + version_key (default Actual/Forecast
      key://14/1). include_entries=false by default to keep the payload small.
      SOAP may echo empty Lines even after a successful write — that is not a failure.
      Read returns SOAP envelopes (Lines.FinancialPlanLineDto); do not feed that
      straight into upsert without Entries — use discover key lists or
      include_entries=true.
    - discover: accounts + periods with fallback (target → reference → config).
      Returns data.accounts / data.periods as [{key, description}] (use these to
      pick months) plus bare account_keys / period_keys for upsert. Period ids
      are not contiguous across fiscal-year boundaries — never invent keys by
      incrementing. Source is tagged (target|reference|config).
      Use this when upsert says "No editable lines".
    - upsert: requires plan_data with Lines (AccountKey, Unit, Entries). Creates the
      plan if it does not exist yet. Accepts either a flat Lines list OR a SOAP/read
      envelope (FinancialPlanLineDto / EntryDto) — nested shapes are normalized.
      Preferred flat example:
        {"EntityKey":"key://2/$Plan/{id}","VersionKey":"key://14/1","Lines":[{
          "AccountKey":"key://2/$Account/...","Unit":"Currency",
          "Entries":[{"PeriodKey":"key://16/...","Value":10000}]}]}
      Build PeriodKey only from discover/read — do not assume sequential period ids.
    - copy: copy account structure and values from reference_project_id onto
      target_project_id. Dry-run unless confirm=true. Always preview first.

    No Anvi Prod equivalent exists for financial plans.
    """
    action = normalize_action(action, _ACTIONS, "manage_financial_plan")
    version = (version_key or _DEFAULT_VERSION).strip()

    if action == "read":
        key = _entity_key(action=action, entity_key=entity_key, project_id=project_id)
        result = await read_financial_plan(
            entity_key=key,
            version_key=version,
            include_entries=include_entries,
            summary=summary,
            fields=fields,
        )
        wrapped = dict(result) if isinstance(result, dict) else {"data": result}
        wrapped["action"] = "read"
        wrapped["echo_incomplete_is_normal"] = True
        wrapped["upsert_shape_hint"] = (
            "Read returns SOAP-shaped Lines (FinancialPlanLineDto). For upsert, "
            "prefer discover's account_keys/period_keys to build a flat Lines list, "
            "or re-read with include_entries=true (nested EntryDto is also accepted)."
        )
        return wrapped

    if action == "discover":
        key = _entity_key(action=action, entity_key=entity_key, project_id=project_id)
        ref = reference_entity_key
        if not ref and reference_project_id:
            ref = plan_entity_key(reference_project_id)
        result = await discover_financial_plan_info(
            entity_key=key,
            version_key=version,
            reference_entity_key=ref,
            skip_target_read=skip_target_read,
            include_entries=include_entries,
            summary=summary,
            fields=fields,
        )
        if result is None:
            return {
                "action": "discover",
                "ok": False,
                "hint": (
                    "No plan, reference, or config accounts were found. "
                    "Pass reference_project_id of a project that already has a financial plan."
                ),
            }
        wrapped = dict(result)
        wrapped["action"] = "discover"
        data = wrapped.get("data") if isinstance(wrapped.get("data"), dict) else {}
        source = wrapped.get("source") or (data.get("Source") if isinstance(data, dict) else None)
        if source:
            wrapped["source"] = source
        account_keys = data.get("account_keys") if isinstance(data, dict) else None
        period_keys = data.get("period_keys") if isinstance(data, dict) else None
        periods = data.get("periods") if isinstance(data, dict) else None
        wrapped["upsert_ready"] = bool(account_keys) and bool(period_keys)
        if not wrapped.get("hint"):
            if wrapped["upsert_ready"]:
                wrapped["hint"] = (
                    "Use data.periods ([{key, description}]) to pick months, then put "
                    "those keys in upsert Entries.PeriodKey. Bare period_keys are unlabeled. "
                    "Period ids skip across fiscal years — never invent by incrementing."
                )
            elif account_keys and not period_keys:
                wrapped["hint"] = (
                    "accounts present but periods empty. Pass a reference_project_id "
                    "with entries."
                )
        if isinstance(periods, list) and periods and not any(
            isinstance(p, dict) and p.get("description") for p in periods
        ):
            wrapped["period_label_hint"] = (
                "Period descriptions were not present on this source. Keys are still "
                "valid for upsert; use a reference read with entries if you need labels."
            )
        return wrapped

    if action == "upsert":
        require(action, "manage_financial_plan", plan_data=plan_data)
        if not isinstance(plan_data, dict):
            raise PlanviewValidationError("plan_data must be a JSON object.")
        payload = dict(plan_data)
        # Unwrap {success, data: {...}} if the model passed a read/discover response.
        nested = payload.get("data")
        if isinstance(nested, dict) and not any(
            k.lower() in {"lines", "key", "entitykey", "versionkey"} for k in payload
        ):
            payload = dict(nested)
        if not any(k.lower() in {"key", "entitykey"} for k in payload):
            key = _entity_key(action=action, entity_key=entity_key, project_id=project_id)
            payload["EntityKey"] = key
        if not any(k.lower() == "versionkey" for k in payload):
            payload["VersionKey"] = version
        result = await upsert_financial_plan(plan_data=payload)
        wrapped = dict(result) if isinstance(result, dict) else {"data": result}
        wrapped["action"] = "upsert"
        wrapped["echo_incomplete_is_normal"] = True
        wrapped["verify_hint"] = (
            "SOAP often returns empty Lines on success. Use action=read to verify values."
        )
        return wrapped

    target = target_project_id or project_id
    require(action, "manage_financial_plan", target_project_id=target, reference_project_id=reference_project_id)
    result = await load_financial_plan_from_reference(
        target_project_id=target,
        reference_project_id=reference_project_id,
        version_key=version,
        scale_factor=scale_factor,
        confirm=confirm,
    )
    wrapped = dict(result) if isinstance(result, dict) else {"data": result}
    wrapped["action"] = "copy"
    if not confirm:
        wrapped["hint"] = wrapped.get("message") or (
            "Dry-run only. Call again with confirm=true to write."
        )
    return wrapped
