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
) -> dict[str, Any]:
    """List projects using the work endpoint with filters.
    
    Projects are accessed through the work endpoint. This function builds a filter
    query to list projects based on the provided criteria.
    
    Args:
        ctx: FastMCP context
        portfolio_id: Optional portfolio ID filter (e.g., "project.PortfolioId .eq 123")
        status: Optional status filter
        limit: Optional limit on number of results
        attributes: Optional list of attributes to return
        
    Returns:
        Response from work endpoint containing project data
        
    Note:
        The Planview API uses the work endpoint for listing projects. Projects are
        work items at the Primary Planning Level (PPL). Use filter syntax like:
        "project.Id .eq 1906" or "project.PortfolioId .eq 123"
    """
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

    # Build filter string for work endpoint
    filter_parts = []
    if portfolio_id:
        # Try to handle both structure code and filter string formats
        if " ." in portfolio_id or ".eq" in portfolio_id.lower():
            filter_parts.append(portfolio_id)
        else:
            filter_parts.append(f"project.PortfolioId .eq {portfolio_id}")
    
    if status:
        if " ." in status or ".eq" in status.lower():
            filter_parts.append(status)
        else:
            filter_parts.append(f"project.Status .eq {status}")
    
    # Default filter to get projects (work items at PPL)
    if not filter_parts:
        filter_parts.append("project.Id .ne null")  # Get all projects
    
    filter_str = " AND ".join(filter_parts)
    
    params: dict[str, Any] = {"filter": filter_str}
    if limit is not None:
        params["limit"] = limit
    params.update(_format_attributes(attributes))

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/work", params=params
            )
            work_data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully listed projects",
                extra={
                    "tool_name": "list_projects",
                    "duration_ms": duration_ms,
                },
            )
            return work_data

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
    """Create a new project.
    
    Creates a project using the Planview Portfolios API. The payload should match
    the CreateProjectDtoPublic schema from the Swagger documentation.
    
    Args:
        ctx: FastMCP context
        data: Project creation payload. Minimum required fields:
            - description: Project name/description (required)
            - parent: Object with structureCode (required)
              Example: {"description": "My Project", "parent": {"structureCode": "14170"}}
        attributes: Optional list of attributes to return in response
        
    Returns:
        Created project data from API response
        
    Example:
        {
            "description": "Jon's MCP Project",
            "parent": {"structureCode": "14170"}
        }
        
    Note:
        See Swagger docs at https://scdemo504.pvcloud.com/polaris/swagger/index.html
        for full schema details and additional optional fields like scheduleStart,
        scheduleFinish, shortName, attributes, etc.
    """
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
