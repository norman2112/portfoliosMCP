"""Resource management tools for Planview Portfolios."""

from typing import Any

import httpx
from fastmcp import Context

from ..config import settings


async def list_resources(
    ctx: Context,
    department: str | None = None,
    role: str | None = None,
    available: bool | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List resources (team members) from Planview.

    Args:
        ctx: FastMCP context
        department: Optional department filter
        role: Optional role filter
        available: Optional filter for resource availability
        limit: Maximum number of resources to return (default: 50)

    Returns:
        List of resource dictionaries with resource details
    """
    params: dict[str, Any] = {"limit": limit}
    if department:
        params["department"] = department
    if role:
        params["role"] = role
    if available is not None:
        params["available"] = str(available).lower()

    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.get(
            f"{settings.planview_api_url}/resources",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
            },
            params=params,
        )
        response.raise_for_status()
        return response.json()


async def get_resource(ctx: Context, resource_id: str) -> dict[str, Any]:
    """Get detailed information about a specific resource.

    Args:
        ctx: FastMCP context
        resource_id: The unique identifier of the resource

    Returns:
        Dictionary containing detailed resource information including
        current allocations, capacity, and skills
    """
    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.get(
            f"{settings.planview_api_url}/resources/{resource_id}",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
            },
        )
        response.raise_for_status()
        return response.json()


async def allocate_resource(
    ctx: Context,
    resource_id: str,
    project_id: str,
    allocation_percentage: float,
    start_date: str,
    end_date: str,
    role: str | None = None,
) -> dict[str, Any]:
    """Allocate a resource to a project.

    Args:
        ctx: FastMCP context
        resource_id: The unique identifier of the resource to allocate
        project_id: The unique identifier of the project
        allocation_percentage: Percentage of resource capacity to allocate (0-100)
        start_date: Allocation start date (ISO format: YYYY-MM-DD)
        end_date: Allocation end date (ISO format: YYYY-MM-DD)
        role: Optional role for this allocation

    Returns:
        Dictionary containing the allocation details
    """
    allocation_data: dict[str, Any] = {
        "resource_id": resource_id,
        "project_id": project_id,
        "allocation_percentage": allocation_percentage,
        "start_date": start_date,
        "end_date": end_date,
    }
    if role:
        allocation_data["role"] = role

    async with httpx.AsyncClient(timeout=settings.api_timeout) as client:
        response = await client.post(
            f"{settings.planview_api_url}/allocations",
            headers={
                "Authorization": f"Bearer {settings.planview_api_key}",
                "X-Tenant-Id": settings.planview_tenant_id,
                "Content-Type": "application/json",
            },
            json=allocation_data,
        )
        response.raise_for_status()
        return response.json()
