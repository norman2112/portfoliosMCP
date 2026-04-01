"""Work endpoint tools for Planview Portfolios."""

import logging
from time import time
from typing import Any

from ..client import get_client, make_request
from ..exceptions import PlanviewError, PlanviewValidationError
from ..performance import log_performance

logger = logging.getLogger(__name__)


def _format_attributes(attributes: list[str] | str | None) -> dict[str, str]:
    if attributes is None:
        return {}
    if isinstance(attributes, str):
        return {"attributes": attributes}
    return {"attributes": ",".join(attributes)}


@log_performance
async def get_work_attributes() -> dict[str, Any]:
    """[LOCAL — raw work attribute list. For natural-language attribute search, use Beta MCP's searchAttributes(entity='work').]

    Get available work attributes."""
    start_time = time()
    logger.info("Getting work attributes", extra={"tool_name": "get_work_attributes"})

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/work/attributes/available"
            )
            data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved work attributes",
                extra={
                    "tool_name": "get_work_attributes",
                    "duration_ms": duration_ms,
                },
            )
            return data

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to get work attributes: {str(e)}",
            extra={
                "tool_name": "get_work_attributes",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


@log_performance
async def list_work(
    filter: str,
    attributes: list[str] | str | None = None,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """[LOCAL — query work items with filter (e.g., project.Id .eq X). Limited filtering support. For portfolio-scoped project lists, use Beta MCP's listProjectsByPortfolioId instead.]

    List work items using a filter string (e.g., `project.Id .eq 1906`).

    If `fields` is provided, the response is trimmed per work item to reduce payload size.
    """
    start_time = time()
    logger.info("Listing work", extra={"tool_name": "list_work"})

    if not filter:
        raise PlanviewValidationError("filter is required")

    def _maybe_trim_fields(payload: dict[str, Any]) -> dict[str, Any]:
        if fields is None:
            return payload
        if not isinstance(payload, dict):
            return payload

        items = payload.get("data")
        if not isinstance(items, list):
            return payload

        always_keys = ["structureCode", "description", "parent", "depth", "place"]
        alias_map: dict[str, list[str]] = {
            "structureCode": ["structureCode", "StructureCode", "structurecode"],
            "description": ["description", "Description"],
            "parent": ["parent", "Parent"],
            "depth": ["depth", "Depth"],
            "place": ["place", "Place"],
            # Common extra fields (may be requested by callers)
            "isMilestone": ["isMilestone", "IsMilestone"],
            "hasChildren": ["hasChildren", "HasChildren"],
            "scheduleStart": ["scheduleStart", "ScheduleStart"],
            "scheduleFinish": ["scheduleFinish", "ScheduleFinish"],
            "scheduleDuration": ["scheduleDuration", "ScheduleDuration"],
            "actualStart": ["actualStart", "ActualStart"],
            "actualFinish": ["actualFinish", "ActualFinish"],
            "status": ["status", "Status"],
            "constraintDate": ["constraintDate", "ConstraintDate"],
            "constraintType": ["constraintType", "ConstraintType"],
        }

        sentinel = object()

        def get_val(item: dict[str, Any], canonical_key: str) -> Any:
            for alias in alias_map.get(canonical_key, [canonical_key]):
                if alias in item:
                    return item[alias]
            # Case-insensitive fallback.
            want = canonical_key.lower()
            for k, v in item.items():
                if isinstance(k, str) and k.lower() == want:
                    return v
            return sentinel

        trimmed_items: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue

            out: dict[str, Any] = {}
            for k in always_keys:
                v = get_val(item, k)
                out[k] = None if v is sentinel else v

            if fields:
                for k in fields:
                    v = get_val(item, k)
                    if v is not sentinel:
                        out[k] = v

            trimmed_items.append(out)

        payload = dict(payload)
        payload["data"] = trimmed_items
        return payload

    def _extract_eq_digits(flt: str) -> str | None:
        """Try to extract `.eq <digits>` from common filter patterns."""
        import re

        # e.g. project.Id .eq 3818 / project.Id .eq '3818'
        m = re.search(r"\.eq\s*'?(?P<val>\d+)'?", flt)
        if not m:
            return None
        return m.group("val")

    def _filter_variants(flt: str) -> list[str]:
        """Generate a small set of likely-accepted filter variants."""
        variants: list[str] = []
        seen: set[str] = set()

        def add(v: str) -> None:
            v2 = " ".join(v.split()).strip()
            if v2 and v2 not in seen:
                seen.add(v2)
                variants.append(v2)

        add(flt)

        # Field name fallbacks.
        if "project.Id" in flt:
            add(flt.replace("project.Id", "project.structureCode", 1))
            add(flt.replace("project.Id", "structureCode", 1))
        if "project.structureCode" in flt:
            add(flt.replace("project.structureCode", "structureCode", 1))

        # Quoted numeric value fallbacks (when it looks like `.eq 123`).
        digits = _extract_eq_digits(flt)
        if digits:
            import re

            # Apply quoting to all generated variants (not just the original filter).
            for v in list(variants):
                quoted = re.sub(r"(\.eq\s*)'?(\d+)'?", r"\1'\2'", v)
                add(quoted)

        return variants

    async def _do_request_with_httpx_params(client, flt: str) -> dict[str, Any]:
        req_params: dict[str, Any] = {"filter": flt}
        req_params.update(_format_attributes(attributes))
        response = await make_request(
            client,
            "GET",
            "/public-api/v1/work",
            params=req_params,
        )
        return response.json()

    async def _do_request_with_percent20_encoding(
        client, flt: str
    ) -> dict[str, Any]:
        """Retry by building the query string manually (spaces as %20)."""
        from urllib.parse import quote

        # Avoid double encoding by not passing `filter` via httpx `params=`.
        encoded_filter = quote(" ".join(flt.split()), safe="")

        query_parts = [f"filter={encoded_filter}"]
        attr_params = _format_attributes(attributes)
        for k, v in attr_params.items():
            encoded_v = quote(str(v), safe="")
            query_parts.append(f"{k}={encoded_v}")

        url_with_query = "/public-api/v1/work?" + "&".join(query_parts)
        response = await make_request(client, "GET", url_with_query)
        return response.json()

    try:
        async with get_client() as client:
            try:
                data = await _do_request_with_httpx_params(client, filter)
                duration_ms = int((time() - start_time) * 1000)
                logger.info(
                    "Successfully listed work",
                    extra={"tool_name": "list_work", "duration_ms": duration_ms},
                )
                return _maybe_trim_fields(data)
            except PlanviewValidationError as first_error:
                # Retry with small set of filter variants for common field-name issues.
                filter_variants = _filter_variants(filter)
                logger.warning(
                    "list_work initial filter failed; retrying with variants",
                    extra={
                        "tool_name": "list_work",
                        "filter": filter,
                        "attempted_variants": filter_variants,
                        "error_detail": str(first_error),
                    },
                )

                last_error: PlanviewValidationError = first_error

                # 1) Retry using normal httpx params encoding.
                for flt in filter_variants[1:]:
                    try:
                        data = await _do_request_with_httpx_params(client, flt)
                        duration_ms = int((time() - start_time) * 1000)
                        logger.info(
                            "Successfully listed work (retry)",
                            extra={
                                "tool_name": "list_work",
                                "duration_ms": duration_ms,
                                "used_filter": flt,
                            },
                        )
                        return _maybe_trim_fields(data)
                    except PlanviewValidationError as e:
                        last_error = e

                # 2) Last-resort: percent-encode spaces manually to avoid server quirks.
                for flt in filter_variants:
                    try:
                        data = await _do_request_with_percent20_encoding(client, flt)
                        duration_ms = int((time() - start_time) * 1000)
                        logger.info(
                            "Successfully listed work (percent20 retry)",
                            extra={
                                "tool_name": "list_work",
                                "duration_ms": duration_ms,
                                "used_filter": flt,
                            },
                        )
                        return _maybe_trim_fields(data)
                    except PlanviewValidationError as e:
                        last_error = e

                # All retries failed; re-raise the last validation error.
                raise last_error

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to list work: {str(e)}",
            extra={
                "tool_name": "list_work",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


@log_performance
async def get_work(
    work_id: str,
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
    """[LOCAL — read any single work hierarchy node by ID (including portfolio-level nodes). For listing projects within a portfolio, use Beta MCP's listProjectsByPortfolioId.]

    Get a single work item by id."""
    start_time = time()
    logger.info(
        "Getting work item", extra={"tool_name": "get_work", "work_id": work_id}
    )

    params = _format_attributes(attributes)

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "GET",
                f"/public-api/v1/work/{work_id}",
                params=params,
            )
            data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved work item",
                extra={
                    "tool_name": "get_work",
                    "work_id": work_id,
                    "duration_ms": duration_ms,
                },
            )
            return data

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to get work item: {str(e)}",
            extra={
                "tool_name": "get_work",
                "work_id": work_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


@log_performance
async def update_work(
    work_id: str,
    updates: dict[str, Any],
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
    """[LOCAL — write operation. Beta MCP is read-only and cannot update work items.]

    Update an existing work item (partial payload).

    Useful for updating phase/task fields like `ExecType` (execution type) on
    work items via PATCH `/public-api/v1/work/{id}`.

    Note: Some instances reject PATCH on `/work/{id}` with HTTP 405.
    In that case, this tool returns a clear limitation message.
    """
    start_time = time()
    logger.info(
        "Updating work item",
        extra={"tool_name": "update_work", "work_id": work_id},
    )

    if not isinstance(updates, dict):
        raise PlanviewValidationError("updates must be a JSON object")

    params = _format_attributes(attributes)

    try:
        async with get_client() as client:
            try:
                response = await make_request(
                    client,
                    "PATCH",
                    f"/public-api/v1/work/{work_id}",
                    params=params,
                    json=updates,
                )
                return response.json()
            except PlanviewValidationError as e:
                if "HTTP 405" in str(e):
                    raise PlanviewValidationError(
                        "This Planview instance does not allow PATCH on /public-api/v1/work/{id}. "
                        "Use update_project for PPL items, or update this work item in Planview UI."
                    ) from e
                # If we sent multiple fields, try isolating which one is blocked.
                if len(updates) > 1:
                    blocked_fields: dict[str, str] = {}
                    succeeded_fields: set[str] = set()

                    for field_id, value in updates.items():
                        try:
                            await make_request(
                                client,
                                "PATCH",
                                f"/public-api/v1/work/{work_id}",
                                params=params,
                                json={field_id: value},
                            )
                            succeeded_fields.add(field_id)
                        except PlanviewValidationError as fe:
                            blocked_fields[field_id] = str(fe)

                    if (
                        len(blocked_fields) == 1
                        and len(succeeded_fields) == (len(updates) - 1)
                    ):
                        field_id = next(iter(blocked_fields.keys()))
                        raise PlanviewValidationError(
                            f"Field '{field_id}' may be lifecycle-controlled and cannot be updated via API. "
                            f"Planview error: {blocked_fields[field_id]}"
                        ) from e

                    potential = (
                        ", ".join(blocked_fields.keys()) if blocked_fields else "unknown"
                    )
                    raise PlanviewValidationError(
                        f"Work update failed for work '{work_id}'. "
                        f"Planview error: {str(e)}. Potential blocked fields: {potential}."
                    ) from e

                raise PlanviewValidationError(
                    f"Work update failed for work '{work_id}'. Planview error: {str(e)}"
                ) from e
            except PlanviewError as e:
                if "HTTP 405" in str(e):
                    raise PlanviewValidationError(
                        "This Planview instance does not allow PATCH on /public-api/v1/work/{id}. "
                        "Use update_project for PPL items, or update this work item in Planview UI."
                    ) from e
                raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to update work: {str(e)}",
            extra={
                "tool_name": "update_work",
                "work_id": work_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise

