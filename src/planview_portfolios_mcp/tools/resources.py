"""Resource management tools for Planview Portfolios."""

import logging
from time import time
from typing import Any

from fastmcp import Context
from pydantic import ValidationError

from ..client import get_client, make_request
from ..exceptions import PlanviewValidationError
from ..models import (
    AllocationResponse,
    ListResourcesParams,
    ResourceAllocation,
    ResourceResponse,
)

logger = logging.getLogger(__name__)


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
    start_time = time()
    logger.info(
        "Listing resources",
        extra={
            "tool_name": "list_resources",
            "department": department,
            "role": role,
            "available": available,
            "limit": limit,
        },
    )

    try:
        # Validate parameters
        validated_params = ListResourcesParams(
            department=department,
            role=role,
            available=available,
            limit=limit,
        )
    except ValidationError as e:
        logger.error(
            f"Invalid parameters for list_resources: {str(e)}",
            extra={"tool_name": "list_resources", "error_type": "ValidationError"},
        )
        raise PlanviewValidationError(f"Invalid parameters: {str(e)}") from e

    # Build query parameters
    params: dict[str, Any] = {"limit": validated_params.limit}
    if validated_params.department:
        params["department"] = validated_params.department
    if validated_params.role:
        params["role"] = validated_params.role
    if validated_params.available is not None:
        params["available"] = str(validated_params.available).lower()

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/resources", params=params
            )
            resources = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                f"Successfully listed {len(resources)} resources",
                extra={
                    "tool_name": "list_resources",
                    "count": len(resources),
                    "duration_ms": duration_ms,
                },
            )
            return resources

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to list resources: {str(e)}",
            extra={
                "tool_name": "list_resources",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def get_resource(ctx: Context, resource_id: str) -> dict[str, Any]:
    """Get detailed information about a specific resource.

    Args:
        ctx: FastMCP context
        resource_id: The unique identifier of the resource

    Returns:
        Dictionary containing detailed resource information including
        current allocations, capacity, and skills
    """
    start_time = time()
    logger.info(
        "Getting resource details",
        extra={"tool_name": "get_resource", "resource_id": resource_id},
    )

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", f"/public-api/v1/resources/{resource_id}"
            )
            resource_data = response.json()

            # Try to parse as typed response
            try:
                resource = ResourceResponse.model_validate(resource_data)
                result = resource.model_dump(mode="json")
            except ValidationError as e:
                logger.warning(
                    f"API response validation failed: {e}",
                    extra={"tool_name": "get_resource"},
                )
                # Return raw dict if validation fails (backward compatibility)
                result = resource_data

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved resource",
                extra={
                    "tool_name": "get_resource",
                    "resource_id": resource_id,
                    "duration_ms": duration_ms,
                },
            )
            return result

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to get resource: {str(e)}",
            extra={
                "tool_name": "get_resource",
                "resource_id": resource_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


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
    start_time = time()
    logger.info(
        "Allocating resource",
        extra={
            "tool_name": "allocate_resource",
            "resource_id": resource_id,
            "project_id": project_id,
            "allocation_percentage": allocation_percentage,
        },
    )

    try:
        # Validate inputs
        validated = ResourceAllocation(
            resource_id=resource_id,
            project_id=project_id,
            allocation_percentage=allocation_percentage,
            start_date=start_date,
            end_date=end_date,
            role=role,
        )
    except ValidationError as e:
        logger.error(
            f"Invalid allocation data: {str(e)}",
            extra={"tool_name": "allocate_resource", "error_type": "ValidationError"},
        )
        raise PlanviewValidationError(f"Invalid allocation data: {str(e)}") from e

    # Convert to dict for API (with ISO date format)
    allocation_data = validated.model_dump(exclude_none=True, mode="json")

    try:
        async with get_client() as client:
            response = await make_request(
                client, "POST", "/public-api/v1/allocations", json=allocation_data
            )
            created_allocation = response.json()

            # Try to parse as typed response
            try:
                allocation = AllocationResponse.model_validate(created_allocation)
                result = allocation.model_dump(mode="json")
            except ValidationError as e:
                logger.warning(
                    f"API response validation failed: {e}",
                    extra={"tool_name": "allocate_resource"},
                )
                # Return raw dict if validation fails (backward compatibility)
                result = created_allocation

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully allocated resource",
                extra={
                    "tool_name": "allocate_resource",
                    "resource_id": resource_id,
                    "project_id": project_id,
                    "duration_ms": duration_ms,
                },
            )
            return result

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to allocate resource: {str(e)}",
            extra={
                "tool_name": "allocate_resource",
                "resource_id": resource_id,
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
