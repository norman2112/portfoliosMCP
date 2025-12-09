"""Project and portfolio management tools for Planview Portfolios."""

import logging
from time import time
from typing import Any

from fastmcp import Context

from ..client import get_client, make_request
from ..exceptions import PlanviewValidationError

logger = logging.getLogger(__name__)


def _format_attributes(attributes: list[str] | str | None) -> dict[str, str]:
    """Convert attributes list/string to query param dict."""
    if attributes is None:
        return {}
    if isinstance(attributes, str):
        return {"attributes": attributes}
    return {"attributes": ",".join(attributes)}


async def list_projects(
    ctx: Context,
    portfolio_id: str | None = None,
    status: str | None = None,
    limit: int | None = None,
    attributes: list[str] | str | None = None,
) -> list[dict[str, Any]]:
    """List projects (API support may vary by tenant)."""
    start_time = time()
    logger.info(
        "Listing projects",
        extra={
            "tool_name": "list_projects",
            "portfolio_id": portfolio_id,
            "status": status,
            "limit": limit,
        },
    )

    params: dict[str, Any] = {}
    if portfolio_id:
        params["portfolio_id"] = portfolio_id
    if status:
        params["status"] = status
    if limit is not None:
        params["limit"] = limit
    params.update(_format_attributes(attributes))

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/projects", params=params
            )
            projects = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully listed projects",
                extra={
                    "tool_name": "list_projects",
                    "count": len(projects) if isinstance(projects, list) else 0,
                    "duration_ms": duration_ms,
                },
            )
            return projects

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to list projects: {str(e)}",
            extra={
                "tool_name": "list_projects",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def get_project(
    ctx: Context, project_id: str, attributes: list[str] | str | None = None
) -> dict[str, Any]:
    """Get a single project by id."""
    start_time = time()
    logger.info(
        "Getting project details",
        extra={"tool_name": "get_project", "project_id": project_id},
    )

    params = _format_attributes(attributes)

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "GET",
                f"/public-api/v1/projects/{project_id}",
                params=params,
            )
            project_data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved project",
                extra={
                    "tool_name": "get_project",
                    "project_id": project_id,
                    "duration_ms": duration_ms,
                },
            )
            return project_data

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to get project: {str(e)}",
            extra={
                "tool_name": "get_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def get_project_attributes(ctx: Context) -> dict[str, Any]:
    """List available project attributes."""
    start_time = time()
    logger.info("Getting project attributes", extra={"tool_name": "get_project_attributes"})

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/projects/attributes/available"
            )
            data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved project attributes",
                extra={
                    "tool_name": "get_project_attributes",
                    "duration_ms": duration_ms,
                },
            )
            return data

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to get project attributes: {str(e)}",
            extra={
                "tool_name": "get_project_attributes",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def create_project(
    ctx: Context,
    data: dict[str, Any],
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
    """Create a new project (raw payload passthrough)."""
    start_time = time()
    logger.info("Creating project", extra={"tool_name": "create_project"})

    if not isinstance(data, dict):
        raise PlanviewValidationError("data must be a JSON object")

    params = _format_attributes(attributes)

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "POST",
                "/public-api/v1/projects",
                params=params,
                json=data,
            )
            created_project = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully created project",
                extra={"tool_name": "create_project", "duration_ms": duration_ms},
            )
            return created_project

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to create project: {str(e)}",
            extra={
                "tool_name": "create_project",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def update_project(
    ctx: Context,
    project_id: str,
    updates: dict[str, Any],
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
    """Update an existing project (partial payload)."""
    start_time = time()
    logger.info(
        "Updating project",
        extra={"tool_name": "update_project", "project_id": project_id},
    )

    if not isinstance(updates, dict):
        raise PlanviewValidationError("updates must be a JSON object")

    params = _format_attributes(attributes)

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "PATCH",
                f"/public-api/v1/projects/{project_id}",
                params=params,
                json=updates,
            )
            updated_project = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully updated project",
                extra={
                    "tool_name": "update_project",
                    "project_id": project_id,
                    "duration_ms": duration_ms,
                },
            )
            return updated_project

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to update project: {str(e)}",
            extra={
                "tool_name": "update_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
