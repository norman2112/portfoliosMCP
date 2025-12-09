"""Project and portfolio management tools for Planview Portfolios."""

import logging
from time import time
from typing import Any

from fastmcp import Context
from pydantic import ValidationError

from ..client import get_client, make_request
from ..exceptions import PlanviewValidationError
from ..models import (
    ListProjectsParams,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)

logger = logging.getLogger(__name__)


async def list_projects(
    ctx: Context,
    portfolio_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List projects and portfolios from Planview.

    Args:
        ctx: FastMCP context
        portfolio_id: Optional portfolio ID to filter projects
        status: Optional status filter (e.g., 'active', 'completed', 'on-hold')
        limit: Maximum number of projects to return (default: 50)

    Returns:
        List of project dictionaries with project details
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

    try:
        # Validate parameters
        validated_params = ListProjectsParams(
            portfolio_id=portfolio_id,
            status=status,
            limit=limit,
        )
    except ValidationError as e:
        logger.error(
            f"Invalid parameters for list_projects: {str(e)}",
            extra={"tool_name": "list_projects", "error_type": "ValidationError"},
        )
        raise PlanviewValidationError(f"Invalid parameters: {str(e)}") from e

    # Build query parameters
    params: dict[str, Any] = {"limit": validated_params.limit}
    if validated_params.portfolio_id:
        params["portfolio_id"] = validated_params.portfolio_id
    if validated_params.status:
        params["status"] = validated_params.status

    try:
        async with get_client() as client:
            response = await make_request(client, "GET", "/projects", params=params)
            projects = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                f"Successfully listed {len(projects)} projects",
                extra={
                    "tool_name": "list_projects",
                    "count": len(projects),
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


async def get_project(ctx: Context, project_id: str) -> dict[str, Any]:
    """Get detailed information about a specific project.

    Args:
        ctx: FastMCP context
        project_id: The unique identifier of the project

    Returns:
        Dictionary containing detailed project information
    """
    start_time = time()
    logger.info(
        "Getting project details",
        extra={"tool_name": "get_project", "project_id": project_id},
    )

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", f"/projects/{project_id}"
            )
            project_data = response.json()

            # Try to parse as typed response
            try:
                project = ProjectResponse.model_validate(project_data)
                result = project.model_dump(mode="json")
            except ValidationError as e:
                logger.warning(
                    f"API response validation failed: {e}",
                    extra={"tool_name": "get_project"},
                )
                # Return raw dict if validation fails (backward compatibility)
                result = project_data

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved project",
                extra={
                    "tool_name": "get_project",
                    "project_id": project_id,
                    "duration_ms": duration_ms,
                },
            )
            return result

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


async def create_project(
    ctx: Context,
    name: str,
    description: str | None = None,
    portfolio_id: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    budget: float | None = None,
) -> dict[str, Any]:
    """Create a new project in Planview Portfolios.

    Args:
        ctx: FastMCP context
        name: Project name
        description: Optional project description
        portfolio_id: Optional portfolio ID to associate the project with
        start_date: Optional project start date (ISO format: YYYY-MM-DD)
        end_date: Optional project end date (ISO format: YYYY-MM-DD)
        budget: Optional project budget

    Returns:
        Dictionary containing the created project details
    """
    start_time = time()
    logger.info(
        "Creating project",
        extra={"tool_name": "create_project", "project_name": name},
    )

    try:
        # Validate inputs
        validated = ProjectCreate(
            name=name,
            description=description,
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
        )
    except ValidationError as e:
        logger.error(
            f"Invalid project data: {str(e)}",
            extra={"tool_name": "create_project", "error_type": "ValidationError"},
        )
        raise PlanviewValidationError(f"Invalid project data: {str(e)}") from e

    # Convert to dict for API (with ISO date format)
    project_data = validated.model_dump(exclude_none=True, mode="json")

    try:
        async with get_client() as client:
            response = await make_request(
                client, "POST", "/projects", json=project_data
            )
            created_project = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully created project",
                extra={
                    "tool_name": "create_project",
                    "project_name": name,
                    "duration_ms": duration_ms,
                },
            )
            return created_project

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to create project: {str(e)}",
            extra={
                "tool_name": "create_project",
                "project_name": name,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def update_project(
    ctx: Context,
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    budget: float | None = None,
) -> dict[str, Any]:
    """Update an existing project in Planview Portfolios.

    Args:
        ctx: FastMCP context
        project_id: The unique identifier of the project to update
        name: Optional new project name
        description: Optional new project description
        status: Optional new project status
        start_date: Optional new start date (ISO format: YYYY-MM-DD)
        end_date: Optional new end date (ISO format: YYYY-MM-DD)
        budget: Optional new budget

    Returns:
        Dictionary containing the updated project details
    """
    start_time = time()
    logger.info(
        "Updating project",
        extra={"tool_name": "update_project", "project_id": project_id},
    )

    try:
        # Validate inputs
        validated = ProjectUpdate(
            name=name,
            description=description,
            status=status,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
        )
    except ValidationError as e:
        logger.error(
            f"Invalid update data: {str(e)}",
            extra={"tool_name": "update_project", "error_type": "ValidationError"},
        )
        raise PlanviewValidationError(f"Invalid update data: {str(e)}") from e

    # Convert to dict for API (with ISO date format)
    update_data = validated.model_dump(exclude_none=True, mode="json")

    try:
        async with get_client() as client:
            response = await make_request(
                client, "PATCH", f"/projects/{project_id}", json=update_data
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
