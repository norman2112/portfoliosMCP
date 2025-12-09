"""Project and portfolio management tools for Planview Portfolios."""

from typing import Any

import httpx
from fastmcp import Context

from ..config import settings


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
    params: dict[str, Any] = {"limit": limit}
    if portfolio_id:
        params["portfolio_id"] = portfolio_id
    if status:
        params["status"] = status

    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.get(
            f"{settings.planview_api_url}/projects",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
            },
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def get_project(ctx: Context, project_id: str) -> dict[str, Any]:
    """Get detailed information about a specific project.

    Args:
        ctx: FastMCP context
        project_id: The unique identifier of the project

    Returns:
        Dictionary containing detailed project information
    """
    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.get(
            f"{settings.planview_api_url}/projects/{project_id}",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
            },
        )
        response.raise_for_status()
        return response.json()


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
    project_data: dict[str, Any] = {"name": name}
    if description:
        project_data["description"] = description
    if portfolio_id:
        project_data["portfolio_id"] = portfolio_id
    if start_date:
        project_data["start_date"] = start_date
    if end_date:
        project_data["end_date"] = end_date
    if budget is not None:
        project_data["budget"] = budget

    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.post(
            f"{settings.planview_api_url}/projects",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
                "Content-Type": "application/json",
            },
            json=project_data,
        )
        response.raise_for_status()
        return response.json()


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
    update_data: dict[str, Any] = {}
    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description
    if status:
        update_data["status"] = status
    if start_date:
        update_data["start_date"] = start_date
    if end_date:
        update_data["end_date"] = end_date
    if budget is not None:
        update_data["budget"] = budget

    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.patch(
            f"{settings.planview_api_url}/projects/{project_id}",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
                "Content-Type": "application/json",
            },
            json=update_data,
        )
        response.raise_for_status()
        return response.json()
