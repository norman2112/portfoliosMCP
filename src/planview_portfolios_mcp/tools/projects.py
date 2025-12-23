"""Project and portfolio management tools for Planview Portfolios."""

import logging
from datetime import datetime, timedelta
from time import time
from typing import Any

from fastmcp import Context

from ..client import get_client, make_request
from ..exceptions import PlanviewValidationError

logger = logging.getLogger(__name__)


def extract_project_info(project_response: dict[str, Any]) -> dict[str, Any]:
    """Extract project information from create_project response.
    
    The API returns a nested structure: {"data": [{"structureCode": "...", ...}]}
    This helper normalizes the response to extract the project info dict.
    
    Args:
        project_response: Response dict from create_project
        
    Returns:
        Dict with project info (structureCode, shortName, description, etc.)
        
    Raises:
        ValueError: If response structure is invalid or structureCode is missing
    """
    project_data = project_response.get("data", [])
    
    # Handle array response (typical case)
    if isinstance(project_data, list) and len(project_data) > 0:
        project_info = project_data[0]
    # Handle direct dict response (less common)
    elif isinstance(project_data, dict):
        project_info = project_data
    else:
        raise ValueError(
            f"Invalid project response structure. Expected 'data' to be list or dict, "
            f"got: {type(project_data)}"
        )
    
    # Validate that we have a structure code with better error context
    if not project_info.get("structureCode"):
        import json
        error_context = (
            f"Project response missing required 'structureCode' field. "
            f"Available keys in response: {list(project_info.keys())}. "
        )
        # Include response snippet for debugging (truncated)
        try:
            response_snippet = json.dumps(project_info, indent=2, default=str)[:500]
            error_context += f"Response snippet: {response_snippet}..."
        except Exception:
            error_context += f"Response type: {type(project_info)}"
        
        raise ValueError(error_context)
    
    return project_info


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


async def _create_default_tasks(
    ctx: Context,
    project_structure_code: str,
    project_start_date: str | None = None,
    project_finish_date: str | None = None,
) -> list[dict[str, Any]]:
    """Create 5 default sample tasks for a new project.
    
    Args:
        ctx: FastMCP context
        project_structure_code: Project structure code
        project_start_date: Project start date (ISO format)
        project_finish_date: Project finish date (ISO format)
        
    Returns:
        List of created task results
    """
    try:
        # Import here to avoid circular dependency
        from .tasks import create_task
        
        father_key = f"key://2/$Plan/{project_structure_code}"
        
        # Calculate task dates if project dates provided
        start_date = None
        finish_date = None
        if project_start_date and project_finish_date:
            try:
                start_dt = datetime.fromisoformat(project_start_date.replace("Z", "+00:00"))
                finish_dt = datetime.fromisoformat(project_finish_date.replace("Z", "+00:00"))
                duration_days = (finish_dt - start_dt).days
                task_duration_days = max(1, duration_days // 5)  # Divide into 5 tasks
                
                # Generate dates for each task
                def get_task_dates(task_num: int) -> tuple[str, str]:
                    task_start = start_dt + timedelta(days=task_num * task_duration_days)
                    task_finish = min(task_start + timedelta(days=task_duration_days), finish_dt)
                    return (
                        task_start.isoformat(timespec='seconds').replace("+00:00", "Z"),
                        task_finish.isoformat(timespec='seconds').replace("+00:00", "Z")
                    )
            except Exception:
                get_task_dates = lambda n: (None, None)
        else:
            get_task_dates = lambda n: (None, None)
        
        # Default task templates
        default_tasks = [
            {
                "Description": "Project Setup and Planning",
                "ScheduleStartDate": get_task_dates(0)[0],
                "ScheduleFinishDate": get_task_dates(0)[1],
            },
            {
                "Description": "Requirements Gathering and Analysis",
                "ScheduleStartDate": get_task_dates(1)[0],
                "ScheduleFinishDate": get_task_dates(1)[1],
            },
            {
                "Description": "Design and Architecture",
                "ScheduleStartDate": get_task_dates(2)[0],
                "ScheduleFinishDate": get_task_dates(2)[1],
            },
            {
                "Description": "Development and Implementation",
                "ScheduleStartDate": get_task_dates(3)[0],
                "ScheduleFinishDate": get_task_dates(3)[1],
            },
            {
                "Description": "Testing and Deployment",
                "ScheduleStartDate": get_task_dates(4)[0],
                "ScheduleFinishDate": get_task_dates(4)[1],
            },
        ]
        
        created_tasks = []
        for i, task_template in enumerate(default_tasks):
            # Filter out None dates
            task_data = {
                "Description": task_template["Description"],
                "FatherKey": father_key,
            }
            
            if task_template.get("ScheduleStartDate"):
                task_data["ScheduleStartDate"] = task_template["ScheduleStartDate"]
            if task_template.get("ScheduleFinishDate"):
                task_data["ScheduleFinishDate"] = task_template["ScheduleFinishDate"]
            
            try:
                task_result = await create_task(ctx, task_data=task_data)
                created_tasks.append({
                    "task_number": i + 1,
                    "description": task_template["Description"],
                    "result": task_result,
                })
                logger.info(
                    f"Created default task {i + 1}/5: {task_template['Description']}",
                    extra={"project_structure_code": project_structure_code}
                )
            except Exception as e:
                logger.warning(
                    f"Failed to create default task {i + 1}: {e}",
                    extra={"project_structure_code": project_structure_code},
                    exc_info=True,
                )
                # Continue with other tasks even if one fails
                continue
        
        logger.info(
            f"Created {len(created_tasks)}/5 default tasks for project {project_structure_code}"
        )
        return created_tasks
        
    except Exception as e:
        logger.error(
            f"Error creating default tasks: {e}",
            extra={"project_structure_code": project_structure_code},
            exc_info=True,
        )
        return []


async def create_project(
    ctx: Context,
    data: dict[str, Any],
    attributes: list[str] | str | None = None,
    create_default_tasks: bool = False,
) -> dict[str, Any]:
    """Create a new project.
    
    Creates a project using the Planview Portfolios API. The payload should match
    the CreateProjectDtoPublic schema from the Swagger documentation.
    
    Projects MUST have defined start and finish dates. If dates are not provided,
    default dates will be set: start date = today, finish date = 6 months from today.
    
    Args:
        ctx: FastMCP context
        data: Project creation payload. Minimum required fields:
            - description: Project name/description (required)
            - parent: Object with structureCode (required)
            Optional fields:
            - scheduleStart: Start date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            - scheduleFinish: Finish date (ISO 8601 format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            If not provided, defaults to today and 6 months from today respectively.
        attributes: Optional list of attributes to return in response
        create_default_tasks: If True, automatically creates 5 default sample tasks
            (Project Setup, Requirements Gathering, Design, Development, Testing)
        
    Returns:
        Created project data from API response. The response may include warnings
        (e.g., "InvalidStructureCode", "InvalidDefaultValues") which are non-fatal.
        Projects are created successfully even with these warnings - they indicate
        configuration issues but don't prevent project creation.
        
    Example:
        {
            "description": "Jon's MCP Project",
            "parent": {"structureCode": "14170"}
        }
        
        With explicit dates:
        {
            "description": "My Project",
            "parent": {"structureCode": "14170"},
            "scheduleStart": "2024-01-01",
            "scheduleFinish": "2024-06-30"
        }
        
    Notes:
        - See Swagger docs at https://scdemo504.pvcloud.com/polaris/swagger/index.html
          for full schema details and additional optional fields like shortName, attributes, etc.
        - Warnings are non-fatal: Warnings like "InvalidStructureCode" or "InvalidDefaultValues"
          indicate Planview configuration issues (e.g., default region code not configured)
          but don't prevent successful project creation. Check response for warning details.
    """
    start_time = time()
    logger.info("Creating project", extra={"tool_name": "create_project"})

    if not isinstance(data, dict):
        raise PlanviewValidationError("data must be a JSON object")

    # Ensure we have a copy so we don't modify the original
    project_data = dict(data)
    
    # Always set default start and finish dates if not provided
    # Default: start today, finish 6 months from today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    default_finish = today + timedelta(days=180)  # 6 months (approximately 180 days)
    
    # Convert to ISO 8601 date format (YYYY-MM-DD)
    if "scheduleStart" not in project_data or project_data.get("scheduleStart") is None:
        project_data["scheduleStart"] = today.strftime("%Y-%m-%d")
        logger.info(f"Set default scheduleStart: {project_data['scheduleStart']}")
    
    if "scheduleFinish" not in project_data or project_data.get("scheduleFinish") is None:
        project_data["scheduleFinish"] = default_finish.strftime("%Y-%m-%d")
        logger.info(f"Set default scheduleFinish: {project_data['scheduleFinish']}")
    
    # Convert datetime objects to ISO 8601 strings if provided
    for date_field in ["scheduleStart", "scheduleFinish"]:
        if date_field in project_data and isinstance(project_data[date_field], datetime):
            project_data[date_field] = project_data[date_field].strftime("%Y-%m-%d")
            logger.info(f"Converted {date_field} from datetime to string: {project_data[date_field]}")

    params = _format_attributes(attributes)

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "POST",
                "/public-api/v1/projects",
                params=params,
                json=project_data,
            )
            created_project = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully created project",
                extra={"tool_name": "create_project", "duration_ms": duration_ms},
            )
            
            # Create default tasks if requested
            if create_default_tasks:
                try:
                    # Extract project info to get structure code
                    project_info = extract_project_info(created_project)
                    structure_code = project_info.get("structureCode")
                    
                    if structure_code:
                        logger.info(
                            f"Creating default tasks for project {structure_code}",
                            extra={"tool_name": "create_project"}
                        )
                        
                        # Get project dates for task scheduling
                        schedule_start = project_info.get("scheduleStart")
                        schedule_finish = project_info.get("scheduleFinish")
                        
                        default_tasks = await _create_default_tasks(
                            ctx,
                            structure_code,
                            schedule_start,
                            schedule_finish,
                        )
                        
                        # Add tasks info to response
                        if "data" in created_project and isinstance(created_project["data"], list):
                            # Add tasks info to the project data
                            if len(created_project["data"]) > 0:
                                created_project["data"][0]["defaultTasks"] = {
                                    "created": len(default_tasks),
                                    "tasks": [
                                        {
                                            "task_number": t["task_number"],
                                            "description": t["description"],
                                            "key": t["result"].get("data", {}).get("Key", "N/A"),
                                        }
                                        for t in default_tasks
                                    ],
                                }
                        
                        logger.info(
                            f"Created {len(default_tasks)} default tasks",
                            extra={"tool_name": "create_project", "project_structure_code": structure_code}
                        )
                    else:
                        logger.warning(
                            "Could not extract structure code for default task creation",
                            extra={"tool_name": "create_project"}
                        )
                except Exception as e:
                    logger.error(
                        f"Failed to create default tasks: {e}",
                        extra={"tool_name": "create_project"},
                        exc_info=True,
                    )
                    # Don't fail project creation if task creation fails
                    pass
            
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
