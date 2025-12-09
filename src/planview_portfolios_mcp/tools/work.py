"""Work endpoint tools for Planview Portfolios."""

import logging
from time import time
from typing import Any

from fastmcp import Context

from ..client import get_client, make_request
from ..exceptions import PlanviewValidationError

logger = logging.getLogger(__name__)


def _format_attributes(attributes: list[str] | str | None) -> dict[str, str]:
    if attributes is None:
        return {}
    if isinstance(attributes, str):
        return {"attributes": attributes}
    return {"attributes": ",".join(attributes)}


async def get_work_attributes(ctx: Context) -> dict[str, Any]:
    """Get available work attributes."""
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


async def list_work(
    ctx: Context,
    filter: str,
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
    """List work items using a filter string (e.g., project.Id .eq 1906)."""
    start_time = time()
    logger.info("Listing work", extra={"tool_name": "list_work"})

    if not filter:
        raise PlanviewValidationError("filter is required")

    params: dict[str, Any] = {"filter": filter}
    params.update(_format_attributes(attributes))

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "GET",
                "/public-api/v1/work",
                params=params,
            )
            data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully listed work",
                extra={"tool_name": "list_work", "duration_ms": duration_ms},
            )
            return data

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


async def get_work(
    ctx: Context,
    work_id: str,
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
    """Get a single work item by id."""
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

