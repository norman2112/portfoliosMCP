"""Project and portfolio management tools for Planview Portfolios."""

import json
import logging
from datetime import datetime, timedelta
from time import time
from typing import Any

from ..client import get_client, make_request
from ..exceptions import PlanviewError, PlanviewValidationError
from ..performance import log_performance
from field_reference import FIELD_CATEGORIES, build_tool_description_appendix, get_fields_by_category

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
        error_context = (
            f"Project response missing required 'structureCode' field. "
            f"Available keys in response: {list(project_info.keys())}. "
        )
        # Include response snippet for debugging (truncated)
        try:
            response_snippet = json.dumps(project_info, indent=2, default=str)[:500]
            error_context += f"Response snippet: {response_snippet}..."
        except (TypeError, ValueError, OverflowError) as snippet_err:
            logger.debug(
                "Could not JSON-serialize project_info for error context: %s: %s",
                type(snippet_err).__name__,
                snippet_err,
            )
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


@log_performance
async def get_project(
    project_id: str, attributes: list[str] | str | None = None
) -> dict[str, Any]:
    """[LOCAL — single project read by ID. For listing/searching projects across a portfolio, use Beta MCP's listProjectsByPortfolioId or searchProjectByName instead.]

    Get a single project by id."""
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

    except (PlanviewError, json.JSONDecodeError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to get project",
            extra={
                "tool_name": "get_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to get project (unexpected error)",
            extra={
                "tool_name": "get_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


@log_performance
async def get_project_attributes() -> dict[str, Any]:
    """[LOCAL — raw attribute list. For natural-language attribute search, use Beta MCP's searchAttributes instead.]

    List available project attributes."""
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

    except (PlanviewError, json.JSONDecodeError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to get project attributes",
            extra={
                "tool_name": "get_project_attributes",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to get project attributes (unexpected error)",
            extra={
                "tool_name": "get_project_attributes",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


async def _create_default_tasks(
    project_structure_code: str,
    project_start_date: str | None = None,
    project_finish_date: str | None = None,
) -> list[dict[str, Any]]:
    """Create 5 default sample tasks in a single batch SOAP call.
    
    Uses batch_create_tasks for one round-trip instead of 5x create_task.
    
    Args:
        project_structure_code: Project structure code
        project_start_date: Project start date (ISO format)
        project_finish_date: Project finish date (ISO format)
        
    Returns:
        List of { task_number, description, result } for create_project response
    """
    try:
        from .tasks import batch_create_tasks

        father_key = f"key://2/$Plan/{project_structure_code}"

        if project_start_date and project_finish_date:
            try:
                start_dt = datetime.fromisoformat(project_start_date.replace("Z", "+00:00"))
                finish_dt = datetime.fromisoformat(project_finish_date.replace("Z", "+00:00"))
                duration_days = (finish_dt - start_dt).days
                task_duration_days = max(1, duration_days // 5)

                def get_task_dates(task_num: int) -> tuple[str | None, str | None]:
                    task_start = start_dt + timedelta(days=task_num * task_duration_days)
                    task_finish = min(task_start + timedelta(days=task_duration_days), finish_dt)
                    return (
                        task_start.isoformat(timespec="seconds").replace("+00:00", "Z"),
                        task_finish.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    )
            except (ValueError, TypeError, OSError) as date_err:
                logger.debug(
                    "Could not parse project dates for default task scheduling: %s: %s",
                    type(date_err).__name__,
                    date_err,
                )
                get_task_dates = lambda n: (None, None)
        else:
            get_task_dates = lambda n: (None, None)

        descriptions = [
            "Project Setup and Planning",
            "Requirements Gathering and Analysis",
            "Design and Architecture",
            "Development and Implementation",
            "Testing and Deployment",
        ]
        tasks = []
        for i, desc in enumerate(descriptions):
            start_d, finish_d = get_task_dates(i)
            task_data: dict[str, Any] = {"Description": desc, "FatherKey": father_key}
            if start_d:
                task_data["ScheduleStartDate"] = start_d
            if finish_d:
                task_data["ScheduleFinishDate"] = finish_d
            tasks.append(task_data)

        batch_result = await batch_create_tasks(tasks=tasks)
        successes = batch_result.get("successes") or []
        if not isinstance(successes, list):
            successes = []

        created_tasks = []
        for i, desc in enumerate(descriptions):
            item = successes[i] if i < len(successes) else None
            key = "N/A"
            if isinstance(item, dict):
                dto = item.get("dto") or item
                if isinstance(dto, dict):
                    key = dto.get("Key") or dto.get("key") or key
            created_tasks.append({
                "task_number": i + 1,
                "description": desc,
                "result": {"data": {"Key": key}},
            })

        logger.info(
            f"Created {len(created_tasks)}/5 default tasks for project {project_structure_code} (batch)",
            extra={"project_structure_code": project_structure_code},
        )
        return created_tasks

    except (
        PlanviewError,
        TypeError,
        ValueError,
        OSError,
        RuntimeError,
        KeyError,
    ):
        logger.exception(
            "Error creating default tasks",
            extra={"project_structure_code": project_structure_code},
        )
        return []
    except Exception:
        logger.exception(
            "Unexpected error creating default tasks",
            extra={"project_structure_code": project_structure_code},
        )
        return []


@log_performance
async def create_project(
    data: dict[str, Any],
    attributes: list[str] | str | None = None,
    create_default_tasks: bool = False,
) -> dict[str, Any]:
    """[LOCAL — write operation. Beta MCP is read-only and cannot create projects.]

    Create a new project.
    
    Creates a project using the Planview Portfolios API. The payload should match
    the CreateProjectDtoPublic schema from the Swagger documentation.
    
    Projects MUST have defined start and finish dates. If dates are not provided,
    default dates will be set: start date = today, finish date = 6 months from today.
    
    Args:
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
        - See your instance's Swagger docs at {PLANVIEW_API_URL}/swagger/index.html
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
                except (
                    PlanviewError,
                    TypeError,
                    ValueError,
                    OSError,
                    RuntimeError,
                    KeyError,
                ):
                    logger.exception(
                        "Failed to create default tasks",
                        extra={"tool_name": "create_project"},
                    )
                    # Don't fail project creation if task creation fails
                    pass
                except Exception:
                    logger.exception(
                        "Unexpected failure creating default tasks",
                        extra={"tool_name": "create_project"},
                    )
                    pass
            
            return created_project

    except (PlanviewError, json.JSONDecodeError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to create project",
            extra={
                "tool_name": "create_project",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to create project (unexpected error)",
            extra={
                "tool_name": "create_project",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


@log_performance
async def update_project(
    project_id: str,
    updates: dict[str, Any],
    attributes: list[str] | str | None = None,
) -> dict[str, Any]:
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
            try:
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
            except PlanviewValidationError as e:
                # 400s on PATCH frequently mean lifecycle-controlled/read-only fields.
                if len(updates) > 1:
                    blocked_fields: dict[str, str] = {}
                    succeeded_fields: set[str] = set()

                    for field_id, value in updates.items():
                        try:
                            await make_request(
                                client,
                                "PATCH",
                                f"/public-api/v1/projects/{project_id}",
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
                        f"Project update failed for project '{project_id}'. "
                        f"Planview error: {str(e)}. Potential blocked fields: {potential}."
                    ) from e

                # Single-field update (or isolation not possible): surface Planview error.
                raise PlanviewValidationError(
                    f"Project update failed for project '{project_id}'. Planview error: {str(e)}"
                ) from e

    except (PlanviewError, json.JSONDecodeError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to update project",
            extra={
                "tool_name": "update_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to update project (unexpected error)",
            extra={
                "tool_name": "update_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


@log_performance
async def delete_project(project_id: str) -> dict[str, Any]:
    """Delete a project by ID.

    Deletes a project from Planview Portfolios using the REST API.
    WARNING: This is destructive and will delete the project and all its
    child tasks, financial plans, and other associated data.

    Args:
        project_id: The structureCode/ID of the project to delete.

    Returns:
        Dict with deletion status.

    Raises:
        PlanviewNotFoundError: If the project doesn't exist.
        PlanviewAuthError: If authentication fails.
        PlanviewError: For other errors.
    """
    start_time = time()
    logger.info(
        "Deleting project",
        extra={"tool_name": "delete_project", "project_id": project_id},
    )

    try:
        async with get_client() as client:
            response = await make_request(
                client,
                "DELETE",
                f"/public-api/v1/projects/{project_id}",
            )

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully deleted project",
                extra={
                    "tool_name": "delete_project",
                    "project_id": project_id,
                    "duration_ms": duration_ms,
                    "status_code": response.status_code,
                },
            )

            # 204 No Content or empty body: success (raise_for_status already passed).
            return {"success": True, "deleted_project_id": project_id}

    except (PlanviewError, json.JSONDecodeError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to delete project",
            extra={
                "tool_name": "delete_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to delete project (unexpected error)",
            extra={
                "tool_name": "delete_project",
                "project_id": project_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


@log_performance
async def get_project_wbs(
    project_id: str,
    include_milestones: bool = True,
    max_depth: int | None = None,
) -> dict[str, Any]:
    """[LOCAL — nested WBS tree with schedule data. For a flat hierarchy view, Beta MCP's getWorkHierarchy is an alternative.]

    Get a project's WBS as a nested, lean tree.

    Calls `list_work` with `project.Id .eq {project_id}` and rebuilds the parent/child
    structure into a sorted tree.

    Node shape (lean): `structureCode`, `description`, `depth`, `place`, `isMilestone`,
    `hasChildren`, `scheduleStart`, `scheduleFinish`, `status`, `constraintDate`,
    `constraintType`, and `children`.
    """

    from .work import list_work as list_work_tool

    # Ask list_work to strip each node down to the fields we need for the tree.
    work_fields = [
        "isMilestone",
        "hasChildren",
        "scheduleStart",
        "scheduleFinish",
        "status",
        "constraintDate",
        "constraintType",
    ]

    payload = await list_work_tool(
        filter=f"project.Id .eq {project_id}",
        fields=work_fields,
    )

    items = payload.get("data", [])
    if not isinstance(items, list):
        items = []

    # Build {structureCode: node}. Nodes are intentionally lean.
    lookup: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        code = item.get("structureCode")
        if code is None:
            continue
        code_str = str(code)
        lookup[code_str] = {
            "structureCode": code_str,
            "description": item.get("description"),
            "depth": item.get("depth"),
            "place": item.get("place"),
            "isMilestone": bool(item.get("isMilestone")),
            "hasChildren": bool(item.get("hasChildren")),
            "scheduleStart": item.get("scheduleStart"),
            "scheduleFinish": item.get("scheduleFinish"),
            "status": item.get("status"),
            "constraintDate": item.get("constraintDate"),
            "constraintType": item.get("constraintType"),
            "children": [],
        }

    root_code = str(project_id)
    root = lookup.get(root_code)
    if root is None:
        return {"error": f"Project {project_id} not found in work items"}

    # Link each item to its parent by parent.structureCode when possible.
    for item in items:
        if not isinstance(item, dict):
            continue
        code = item.get("structureCode")
        if code is None:
            continue
        code_str = str(code)
        if code_str == root_code:
            continue  # root stays top-level

        parent = item.get("parent")
        if not isinstance(parent, dict):
            continue
        parent_code = parent.get("structureCode")
        if parent_code is None:
            continue
        parent_code_str = str(parent_code)
        parent_node = lookup.get(parent_code_str)
        if parent_node is None:
            continue

        child_node = lookup.get(code_str)
        if child_node is None:
            continue

        parent_node["children"].append(child_node)

    def _place_val(node: dict[str, Any]) -> int:
        try:
            return int(node.get("place") or 0)
        except (TypeError, ValueError) as place_err:
            logger.debug(
                "Invalid place value on WBS node: %s: %s",
                type(place_err).__name__,
                place_err,
            )
            return 0

    # Optionally remove milestone nodes (and promote their children).
    def _prune_milestones(node: dict[str, Any]) -> None:
        if include_milestones:
            # Still recurse to sort later.
            for child in node.get("children", []):
                _prune_milestones(child)
            return

        pruned_children: list[dict[str, Any]] = []
        for child in node.get("children", []):
            _prune_milestones(child)
            if child.get("isMilestone"):
                # Promote grandchildren.
                pruned_children.extend(child.get("children", []))
            else:
                pruned_children.append(child)
        node["children"] = pruned_children

    # Apply milestone pruning then sorting.
    _prune_milestones(root)

    def _sort_tree(node: dict[str, Any]) -> None:
        node["children"].sort(key=_place_val)
        for child in node["children"]:
            _sort_tree(child)

    _sort_tree(root)

    # Apply max_depth relative to root (node depth_from_root==0 is the project root).
    if max_depth is not None:
        if max_depth < 0:
            max_depth = 0

        def _trim_by_depth(node: dict[str, Any], depth_from_root: int) -> None:
            if depth_from_root >= max_depth:
                node["children"] = []
                return
            for child in node.get("children", []):
                _trim_by_depth(child, depth_from_root + 1)

        _trim_by_depth(root, 0)

        # Re-sort since trimming can empty children lists.
        _sort_tree(root)

    # Stats based on the node flags.
    def _count(node: dict[str, Any], depth_from_root: int) -> tuple[int, int, int, int, int]:
        total = 1
        milestones = 1 if node.get("isMilestone") else 0
        phases = 0
        tasks = 0

        if not milestones:
            if node.get("hasChildren"):
                phases = 1
            else:
                tasks = 1

        deepest = depth_from_root
        for child in node.get("children", []):
            ct, cp, ctask, cm, cd = _count(child, depth_from_root + 1)
            total += ct
            phases += cp
            tasks += ctask
            milestones += cm
            deepest = max(deepest, cd)

        return total, phases, tasks, milestones, deepest

    total_nodes, phases, tasks, milestones, deepest = _count(root, 0)

    return {
        "project": root,
        "stats": {
            "total_nodes": total_nodes,
            "phases": phases,
            "tasks": tasks,
            "milestones": milestones,
            "max_depth": deepest,
        },
    }


async def list_field_reference(
    category: str | None = None,
) -> dict[str, Any]:
    """[LOCAL — field discovery for write operations. For read-side attribute discovery, use Beta MCP's searchAttributes instead.]

    List available writable project fields organized by category.

    Use this tool to discover which field IDs to pass to `update_project` or
    `create_project`.

    Args:
        category: Optional category filter. If not provided, returns all categories.
            Valid categories:
            core_identity, dates, progress, status_assessments, investment_scoring,
            strategic_classification, wsjf_safe, risk, business_case_text,
            lifecycle_roles, financial_metrics, agileplace_integration, swot
    """

    valid_categories = list(FIELD_CATEGORIES.keys())
    if category:
        fields = get_fields_by_category(category)
        if not fields:
            return {
                "error": f"Unknown category '{category}'. Valid: {valid_categories}"
            }

        cat_info = FIELD_CATEGORIES[category].get("_description", "")  # type: ignore[union-attr]
        return {
            "category": category,
            "description": cat_info,
            "fields": {
                fid: {"title": t, "type": ft, "default": d, "ppl_only": p}
                for fid, (t, ft, d, p) in fields.items()
            },
        }

    # Return all categories with field counts
    result: dict[str, Any] = {}
    for cat_name, cat_fields in FIELD_CATEGORIES.items():
        desc = cat_fields.get("_description", "")  # type: ignore[union-attr]
        fields = {k: v for k, v in cat_fields.items() if not k.startswith("_")}
        result[cat_name] = {
            "description": desc,
            "field_count": len(fields),
            "fields": {
                fid: {"title": t, "type": ft, "default": d, "ppl_only": p}
                for fid, (t, ft, d, p) in fields.items()
            },
        }
    return result


# --- Tool description augmentation (static curated field reference) ---
_CREATE_PROJECT_NOTE = (
    "\n\nNote: On create, you MUST provide 'description' (project name) and "
    "'parent' (structureCode of parent work item).\n"
    "Optional: scheduleStart, scheduleFinish (default to today and +6 months).\n"
    "For available writable fields, call `list_field_reference()` to browse by category:\n"
    "core_identity, dates, progress, status_assessments, investment_scoring,\n"
    "strategic_classification, wsjf_safe, risk, business_case_text,\n"
    "lifecycle_roles, financial_metrics, agileplace_integration, swot\n"
)

_UPDATE_PROJECT_DESCRIPTION_BASE = (
    "Update an existing project (partial payload).\n\n"
    "Send only the fields you want to change. Field IDs are case-sensitive.\n"
    "Planview business rules may override some values (e.g., dates get calendar-aligned).\n\n"
    "IMPORTANT CONSTRAINTS:\n"
    "- Duration is calculated from start/finish — don't send it directly\n"
    "- Lifecycle-controlled Work Status cannot be overridden via API\n"
    "- StructureCode fields: send {\"structureCode\": \"CODE\"} or "
    "{\"structureCode\": \"CODE\", \"description\": \"LABEL\"}\n"
    "- Fields marked PPL-only only work at Primary Planning Level (projects), not sub-tasks\n"
)

_FIELDS_POINTER = (
    "\nFor available writable fields, call `list_field_reference()` to browse by category:\n"
    "core_identity, dates, progress, status_assessments, investment_scoring,\n"
    "strategic_classification, wsjf_safe, risk, business_case_text,\n"
    "lifecycle_roles, financial_metrics, agileplace_integration, swot\n"
)

try:
    # Keep tool constraints small; callers can fetch the curated field list via `list_field_reference()`.
    create_project.__doc__ = (create_project.__doc__ or "").rstrip() + _CREATE_PROJECT_NOTE
    update_project.__doc__ = _UPDATE_PROJECT_DESCRIPTION_BASE + _FIELDS_POINTER
except Exception:
    # If doc augmentation fails for any reason, keep the original docstrings.
    logger.exception(
        "Failed to augment project tool descriptions with field reference"
    )
