"""Task management tools for Planview Portfolios SOAP API."""

import asyncio
import logging
from datetime import datetime
from time import time
from typing import Any

from fastmcp import Context

from ..exceptions import PlanviewConnectionError, PlanviewValidationError
from ..models import TaskDto2, WorkOptionsDto
from ..performance import log_performance
from ..soap_client import (
    _handle_soap_result,
    _parse_opensuite_result,
    get_soap_client,
    make_soap_request,
)
from ..utils.soap_helpers import filter_and_sort_fields

logger = logging.getLogger(__name__)

# Service name and port for TaskService
# The WSDL defines service "TaskService" with port "BasicHttpBinding_ITaskService3"
TASK_SERVICE_NAME = "TaskService"
TASK_SERVICE_PORT = "BasicHttpBinding_ITaskService3"

TASK_DTO2_NS = (
    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
)


def _validate_task_fields(task_data: dict[str, Any]) -> None:
    """Validate required task fields.

    Args:
        task_data: Task data dictionary

    Raises:
        PlanviewValidationError: If required fields missing or invalid

    Notes:
        Required fields: Description, FatherKey (case-insensitive check)
    """
    if not isinstance(task_data, dict):
        raise PlanviewValidationError("task_data must be a dictionary")

    has_description = any(k.lower() == "description" for k in task_data)
    has_father_key = any(k.lower() == "fatherkey" for k in task_data)

    if not has_description:
        raise PlanviewValidationError("Description field is required")
    if not has_father_key:
        raise PlanviewValidationError("FatherKey field is required")


@log_performance
async def create_task(
    ctx: Context,
    task_data: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new task using SOAP TaskService.

    Creates a task (planning entity below PPL) in Planview Portfolios using the SOAP API.

    Args:
        ctx: FastMCP context
        task_data: Task data dictionary with TaskDto2 fields. Required fields:
            - Description: Task description (required)
            - FatherKey: Parent work entity key URI (required)
        Optional fields:
            - Key: External key URI (recommended to prevent duplicates)
            - ScheduleStartDate: Schedule start date (ISO 8601)
            - ScheduleFinishDate: Schedule finish date (ISO 8601)
            - Duration: Duration in minutes
            - CalendarKey: Calendar key URI
            - EnterProgress: Enable manual progress entry (bool)
            - IsMilestone: Is this a milestone (bool)
            - IsTicketable: Can create tickets (bool)
            - IsDeliverable: Is deliverable (bool)
            - PercentComplete: Percent complete (0-100)
            - WorkId: Work ID string
            - WorkStatusKey: Work status key URI
            - LifecycleAdminUserKey: Lifecycle admin user key URI
            - Notes: Task notes
            - Place: Task place/order
        options: Optional WorkOptionsDto dictionary:
            - CopyMissingValuesFromPlanview: Copy missing values from existing record (bool)
            - RollupActuals: Roll up actuals to parent (bool)
            - ClearStagingTableAfterRun: Clear staging table after run (bool, default: True)

    Returns:
        Dict with:
        - success: True if operation succeeded
        - data: Task DTO (may have null fields - this is normal SOAP API behavior)
        - warnings: List of non-fatal warnings
        
        Note: The SOAP API may return null for many fields (e.g., ScheduleStartDate, Duration)
        even though the task was created successfully with those values. This is expected behavior.
        Use read_task() to verify the task was created with the correct data.

    Raises:
        PlanviewValidationError: If task data is invalid
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors

    Examples:
        Minimal (required fields only):
            {"Description": "My Task", "FatherKey": "key://2/$Plan/12345"}

        With external key (recommended to prevent duplicates):
            {
                "Description": "My Task",
                "FatherKey": "key://2/$Plan/12345",
                "Key": "ekey://2/namespace/task-1"
            }

        With schedule dates:
            {
                "Description": "My Task",
                "FatherKey": "key://2/$Plan/12345",
                "ScheduleStartDate": "2024-01-01T08:00:00",
                "ScheduleFinishDate": "2024-01-15T17:00:00"
            }

    Notes:
        - Field names must use PascalCase (e.g., FatherKey, not father_key)
        - Date format: ISO 8601 (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD)
        - Fields are automatically sorted alphabetically (Planview requirement)
        - None values are automatically filtered
        - Use external key (ekey://) to prevent duplicate creation
    
    Known SOAP API Behaviors:
        - Response fields may be null: The SOAP API doesn't always populate all fields in the response
          DTO, even though the task was created successfully with those values. This is normal.
          The task IS created correctly in Planview - use read_task() to verify.
        - Warnings are non-fatal: Warnings indicate configuration issues but don't prevent creation.
          Check the warnings array in the response for details.
    """
    start_time = time()
    logger.info("Creating task", extra={"tool_name": "create_task"})

    try:
        # Validate required fields
        _validate_task_fields(task_data)

        # Filter non-None and sort (Planview requirement)
        task_payload = filter_and_sort_fields(task_data)
        logger.debug(f"Task payload after filtering: {list(task_payload.keys())}")

        # Set Duration to 0 for milestones (Planview requirement)
        if task_payload.get("IsMilestone") is True:
            task_payload["Duration"] = 0
            logger.debug("Set Duration to 0 for milestone task")
            # Planview requirement: milestones must have manual progress entry enabled.
            if "EnterProgress" not in task_payload:
                task_payload["EnterProgress"] = True

        # Convert datetime objects to ISO 8601 strings for zeep compatibility
        for key, value in task_payload.items():
            if isinstance(value, datetime):
                task_payload[key] = value.isoformat()

        # Make SOAP request
        # Note: options parameter exists for API compatibility but is not currently used
        async with get_soap_client() as client:
            # Get the service
            try:
                service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
            except (AttributeError, ValueError, KeyError, TypeError):
                service = client.service

            # Get the Create operation
            create_op = getattr(service, "Create")

            # Get TaskDto2 type factory
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
                )
            except Exception as e:
                raise PlanviewValidationError(f"TaskDto2 type not found in WSDL: {e}") from e

            # Verify required fields are present
            if "Description" not in task_payload:
                raise PlanviewValidationError("Description is required but missing from payload")
            if "FatherKey" not in task_payload:
                raise PlanviewValidationError("FatherKey is required but missing from payload")

            # Call SOAP Create operation
            # Try multiple approaches for compatibility
            # Note: Skip dict approach for milestones (zeep has issues with IsMilestone/Duration fields)
            is_milestone = task_payload.get("IsMilestone") is True
            result = None
            last_error = None
            
            # For milestones, skip dict approach and go straight to TaskDto2 object
            # (zeep incorrectly tries to pass dict keys to ArrayOfTaskDto2 constructor)
            if not is_milestone:
                # Approach 1: Try dict directly (works reliably for regular tasks)
                try:
                    result_direct = await asyncio.to_thread(create_op, dtos=[task_payload])
                    result = _handle_soap_result(result_direct)
                    logger.debug("Task creation succeeded using dict approach")
                except Exception as e1:
                    last_error = e1
                    logger.debug(f"Dict approach failed: {e1}, trying TaskDto2 object")
            
            # Approach 2: Create TaskDto2 object and pass as list (works for both regular tasks and milestones)
            if result is None:
                try:
                    task_dto_obj = task_dto_factory(**task_payload)
                    # Try with list of TaskDto2 object (zeep should handle conversion)
                    result_direct = await asyncio.to_thread(create_op, dtos=[task_dto_obj])
                    result = _handle_soap_result(result_direct)
                    logger.debug("Task creation succeeded using TaskDto2 object approach")
                except Exception as e2:
                    last_error = e2
                    logger.debug(f"TaskDto2 object approach failed: {e2}, trying ArrayOfTaskDto2 wrapper")
                    
                    # Approach 3: Try wrapping in ArrayOfTaskDto2 explicitly
                    try:
                        array_type = client.get_type(
                            "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}ArrayOfTaskDto2"
                        )
                        # Create array type with list of TaskDto2 objects
                        dtos_param = array_type([task_dto_obj])
                        result_direct = await asyncio.to_thread(create_op, dtos=dtos_param)
                        result = _handle_soap_result(result_direct)
                        logger.debug("Task creation succeeded using ArrayOfTaskDto2 wrapper approach")
                    except Exception as e3:
                        last_error = e3
                        logger.error(f"All task creation approaches failed. Last error: {e3}", exc_info=True)
                        dict_error_msg = f"Dict error: {last_error}" if not is_milestone else "Dict skipped for milestone"
                        raise PlanviewConnectionError(
                            f"Failed to create task: All serialization approaches failed. "
                            f"{dict_error_msg}. TaskDto2 error: {e2}. ArrayOfTaskDto2 error: {e3}"
                        ) from e3
            
            if result is None:
                raise PlanviewConnectionError(
                    f"Failed to create task: All approaches failed. Last error: {last_error}"
                ) from last_error

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully created task",
                extra={
                    "tool_name": "create_task",
                    "task_key": result.get("data", {}).get("Key"),
                    "duration_ms": duration_ms,
                },
            )

            return result

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to create task: {str(e)}",
            extra={
                "tool_name": "create_task",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


@log_performance
async def batch_create_tasks(
    ctx: Context,
    tasks: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Batch create multiple tasks in a single SOAP call.
    
    Much faster than calling create_task() multiple times. Creates all tasks
    in a single SOAP request, significantly reducing latency for bulk creation.
    
    Args:
        ctx: FastMCP context
        tasks: List of task creation dictionaries. Each dict must contain:
            - Description: Task description (required)
            - FatherKey: Parent work entity key URI (required)
            Optional fields: Key, ScheduleStartDate, ScheduleFinishDate, Duration, etc.
            (same as create_task)
        options: Optional WorkOptionsDto dictionary (applies to all tasks)
        
    Returns:
        Dict with per-task results (SOAP may partially succeed):
        - success: True only if all tasks succeeded
        - created: List of per-task entries in the same order as `tasks`:
            - description: task description (if available)
            - key: created task key (for succeeded tasks) or null (for failed tasks)
            - status: "success" | "failed"
            - error: present only for failed tasks
        - summary: {total, succeeded, failed}
        - warnings: optional list of warning messages
        
    Raises:
        PlanviewValidationError: If task data is invalid
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors
        
    Example:
        tasks = [
            {
                "Description": "Task 1",
                "FatherKey": "key://2/$Plan/12345",
                "ScheduleStartDate": "2024-01-01T08:00:00",
                "ScheduleFinishDate": "2024-01-15T17:00:00"
            },
            {
                "Description": "Task 2",
                "FatherKey": "key://2/$Plan/12345",
                "ScheduleStartDate": "2024-01-16T08:00:00",
                "ScheduleFinishDate": "2024-01-30T17:00:00"
            }
        ]
        result = await batch_create_tasks(ctx, tasks)
        
    Notes:
        - All tasks are created in a single SOAP call, making this much faster
          than individual create_task() calls
        - If some tasks fail, this tool still returns the successful ones so callers
          can avoid retrying the already-created tasks (which would create duplicates)
        - Response fields may be null - this is normal SOAP API behavior
        - Use read_task() to verify individual tasks if needed
        - Recommended to use external Key (ekey://) to prevent duplicates
    """
    start_time = time()
    logger.info(
        "Batch creating tasks",
        extra={"tool_name": "batch_create_tasks", "task_count": len(tasks)},
    )
    
    if not tasks:
        raise PlanviewValidationError("tasks list cannot be empty")
    
    if not isinstance(tasks, list):
        raise PlanviewValidationError("tasks must be a list")
    
    try:
        # Validate all tasks first
        for i, task_data in enumerate(tasks):
            if not isinstance(task_data, dict):
                raise PlanviewValidationError(
                    f"Task {i} must be a dictionary. Got: {type(task_data).__name__}"
                )
            _validate_task_fields(task_data)
        
        # Prepare options
        options_dict = None
        if options:
            try:
                options_dto = WorkOptionsDto.model_validate(options)
                options_dict = options_dto.model_dump(by_alias=True, exclude_none=True)
            except Exception as e:
                raise PlanviewValidationError(f"Invalid options: {str(e)}") from e
        
        # Build list of TaskDto2 objects for batch create
        task_dto_objects = []
        
        for i, task_data in enumerate(tasks):
            # Filter non-None and sort (Planview requirement)
            task_payload = filter_and_sort_fields(task_data)
            
            # Set Duration to 0 for milestones (Planview requirement)
            if task_payload.get("IsMilestone") is True:
                task_payload["Duration"] = 0
                logger.info(f"Task {i}: Set Duration to 0 for milestone")
                # Planview requirement: milestones must have manual progress entry enabled.
                if "EnterProgress" not in task_payload:
                    task_payload["EnterProgress"] = True
            
            # Convert datetime objects to ISO 8601 strings
            from datetime import datetime
            for key, value in task_payload.items():
                if isinstance(value, datetime):
                    task_payload[key] = value.isoformat()
            
            task_dto_objects.append(task_payload)
        
        # Make batch SOAP request with all tasks
        async with get_soap_client() as client:
            # Get the service
            try:
                service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
            except (AttributeError, ValueError, KeyError, TypeError):
                service = client.service
            
            # Get the Create operation
            create_op = getattr(service, "Create")
            
            # Get TaskDto2 type factory
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
                )
            except Exception as e:
                raise PlanviewConnectionError(f"TaskDto2 type not found in WSDL: {e}") from e
            
            # Create TaskDto2 objects for all tasks
            final_task_dtos = []
            for i, task_payload in enumerate(task_dto_objects):
                try:
                    task_dto_obj = task_dto_factory(**task_payload)
                    final_task_dtos.append(task_dto_obj)
                except Exception as e:
                    raise PlanviewValidationError(
                        f"Task {i} failed to create TaskDto2 object: {e}"
                    ) from e
            
            # Call Create operation with array of TaskDto2 objects
            logger.info(f"Batch creating {len(final_task_dtos)} tasks in single SOAP call")
            
            try:
                # Use ArrayOfTaskDto2 wrapper for reliability
                array_type = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}ArrayOfTaskDto2"
                )
                dtos_param = array_type(final_task_dtos)
            except Exception:
                # Fallback to plain list if ArrayOf wrapper fails
                dtos_param = final_task_dtos
            
            result_direct = await asyncio.to_thread(create_op, dtos=dtos_param)
            parsed = _parse_opensuite_result(result_direct)

            duration_ms = int((time() - start_time) * 1000)

            def _ci_get(d: dict[str, Any], name: str) -> Any:
                for k, v in d.items():
                    if isinstance(k, str) and k.lower() == name.lower():
                        return v
                return None

            def _dto_get_any(dto: dict[str, Any], names: list[str]) -> Any:
                for n in names:
                    val = _ci_get(dto, n)
                    if val is not None:
                        return val
                return None

            # Map successes/failures to original task index (SOAP SourceIndex).
            success_by_idx: dict[int, dict[str, Any]] = {}
            failure_by_idx: dict[int, dict[str, Any]] = {}

            for s in parsed.get("successes", []) or []:
                idx = s.get("source_index")
                if idx is None:
                    continue
                try:
                    success_by_idx[int(idx)] = s
                except Exception:
                    continue

            for f in parsed.get("failures", []) or []:
                idx = f.get("source_index")
                if idx is None:
                    continue
                try:
                    failure_by_idx[int(idx)] = f
                except Exception:
                    continue

            warnings_list = [
                w.get("error_message")
                for w in (parsed.get("warnings", []) or [])
                if w.get("error_message")
            ]
            if parsed.get("general_error_message"):
                warnings_list.append(parsed.get("general_error_message"))

            created: list[dict[str, Any]] = []
            succeeded = 0
            failed = 0

            for i, task_data in enumerate(tasks):
                task_desc = _ci_get(task_data, "Description")
                task_key = _ci_get(task_data, "Key")

                if i in success_by_idx:
                    succ = success_by_idx[i]
                    dto = succ.get("dto") or {}
                    key = _dto_get_any(dto, ["Key", "EntityKey"]) or task_key
                    desc = _dto_get_any(dto, ["Description", "EntityDescription"]) or task_desc
                    created.append(
                        {
                            "description": desc,
                            "key": key,
                            "status": "success",
                        }
                    )
                    succeeded += 1
                elif i in failure_by_idx:
                    fail = failure_by_idx[i]
                    dto = fail.get("dto") or {}
                    desc = _dto_get_any(dto, ["Description", "EntityDescription"]) or task_desc
                    created.append(
                        {
                            "description": desc,
                            "key": None,
                            "status": "failed",
                            "error": fail.get("error_message") or "Unknown failure",
                        }
                    )
                    failed += 1
                else:
                    created.append(
                        {
                            "description": task_desc,
                            "key": None,
                            "status": "failed",
                            "error": "SOAP did not provide success/failure entry for this task",
                        }
                    )
                    failed += 1

            logger.info(
                "Batch create completed (partial allowed)",
                extra={
                    "tool_name": "batch_create_tasks",
                    "task_count": len(final_task_dtos),
                    "duration_ms": duration_ms,
                    "succeeded": succeeded,
                    "failed": failed,
                },
            )

            return {
                "success": failed == 0,
                "created": created,
                "summary": {
                    "total": len(tasks),
                    "succeeded": succeeded,
                    "failed": failed,
                },
                "warnings": warnings_list,
            }
            
    except PlanviewValidationError:
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to batch create tasks: {str(e)}",
            extra={
                "tool_name": "batch_create_tasks",
                "task_count": len(tasks) if tasks else 0,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


@log_performance
async def read_task(ctx: Context, task_key: str) -> dict[str, Any]:
    """Read a task by key using SOAP TaskService.

    Reads a task from Planview Portfolios using the SOAP API.

    Args:
        ctx: FastMCP context
        task_key: Task key URI in key://, search://, or ekey:// format

    Returns:
        Dict with task data (full TaskDto2)

    Raises:
        PlanviewValidationError: If task_key is invalid
        PlanviewNotFoundError: If task is not found
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors

    Example:
        task_key: "key://2/$Plan/12345"
        or: "ekey://2/namespace/task-1"
        or: "search://2/$Plan?description=Task Name"
    """
    start_time = time()
    logger.info("Reading task", extra={"tool_name": "read_task", "task_key": task_key})

    try:
        # Validate key format
        from ..models import validate_task_key

        try:
            validated_key = validate_task_key(task_key)
        except ValueError as e:
            raise PlanviewValidationError(f"Invalid task key format: {str(e)}") from e

        # Make SOAP request
        async with get_soap_client() as client:
            # Read operation expects: keys (list of strings)
            request_params = {"keys": [validated_key]}

            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Read",
                port_name=TASK_SERVICE_PORT,
                **request_params,
            )

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully read task",
                extra={
                    "tool_name": "read_task",
                    "task_key": task_key,
                    "duration_ms": duration_ms,
                },
            )

            return result

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to read task: {str(e)}",
            extra={
                "tool_name": "read_task",
                "task_key": task_key,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


@log_performance
async def batch_delete_tasks(
    ctx: Context,
    task_keys: list[str],
) -> dict[str, Any]:
    """Delete multiple tasks in bulk using the SOAP TaskService.

    Planview SOAP operations are not guaranteed atomic. This tool therefore
    returns per-key success/failure information so callers can safely retry
    only the failed keys (without re-deleting ones that already succeeded).
    """

    start_time = time()
    logger.info(
        "Batch deleting tasks",
        extra={"tool_name": "batch_delete_tasks", "task_count": len(task_keys)},
    )

    if not task_keys:
        raise PlanviewValidationError("task_keys list cannot be empty")
    if not isinstance(task_keys, list):
        raise PlanviewValidationError("task_keys must be a list")

    from ..models import validate_task_key

    validated_keys: list[str] = []
    for i, task_key in enumerate(task_keys):
        if not isinstance(task_key, str):
            raise PlanviewValidationError(
                f"task_keys[{i}] must be a string. Got: {type(task_key).__name__}"
            )
        try:
            validated_keys.append(validate_task_key(task_key))
        except ValueError as e:
            raise PlanviewValidationError(
                f"task_keys[{i}] has invalid task key format: {str(e)}"
            ) from e

    # Choose a conservative chunk size for SOAP payloads.
    chunk_size = 50

    deleted: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    async with get_soap_client() as client:
        # Get the service
        try:
            service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
        except (AttributeError, ValueError, KeyError, TypeError):
            service = client.service

        delete_op = getattr(service, "Delete")

        for offset in range(0, len(validated_keys), chunk_size):
            chunk_keys = validated_keys[offset : offset + chunk_size]

            result_direct = await asyncio.to_thread(delete_op, keys=chunk_keys)
            parsed = _parse_opensuite_result(result_direct)

            # If we got a general error and no per-item statuses, fail the whole chunk.
            if parsed.get("general_error_message") and not parsed.get("successes") and not parsed.get("failures"):
                for k in chunk_keys:
                    failed.append({"key": k, "error": parsed["general_error_message"]})
                continue

            success_by_idx: dict[int, dict[str, Any]] = {}
            failure_by_idx: dict[int, dict[str, Any]] = {}

            for s in parsed.get("successes", []) or []:
                idx = s.get("source_index")
                if idx is None:
                    continue
                try:
                    success_by_idx[int(idx)] = s
                except Exception:
                    continue

            for f in parsed.get("failures", []) or []:
                idx = f.get("source_index")
                if idx is None:
                    continue
                try:
                    failure_by_idx[int(idx)] = f
                except Exception:
                    continue

            for local_idx, key in enumerate(chunk_keys):
                if local_idx in success_by_idx:
                    deleted.append({"key": key, "status": "success"})
                elif local_idx in failure_by_idx:
                    err = failure_by_idx[local_idx].get("error_message") or "Unknown failure"
                    failed.append({"key": key, "status": "failed", "error": err})
                else:
                    failed.append(
                        {
                            "key": key,
                            "status": "failed",
                            "error": "SOAP did not provide success/failure entry for this key",
                        }
                    )

    total = len(task_keys)
    succeeded = len(deleted)
    failed_count = len(failed)

    duration_ms = int((time() - start_time) * 1000)
    logger.info(
        "Batch delete completed",
        extra={
            "tool_name": "batch_delete_tasks",
            "task_count": total,
            "duration_ms": duration_ms,
            "succeeded": succeeded,
            "failed": failed_count,
        },
    )

    return {
        "deleted": deleted,
        "failed": failed,
        "summary": {
            "total": total,
            "succeeded": succeeded,
            "failed": failed_count,
        },
    }


@log_performance
async def delete_task(ctx: Context, task_key: str) -> dict[str, Any]:
    """Delete a task using SOAP TaskService.

    Deletes a task from Planview Portfolios using the SOAP API.
    Note: Deleting a task will also delete all its child tasks.

    Args:
        ctx: FastMCP context
        task_key: Task key URI in key://, search://, or ekey:// format

    Returns:
        Dict with deletion status

    Raises:
        PlanviewValidationError: If task_key is invalid
        PlanviewNotFoundError: If task is not found
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors
    """
    start_time = time()
    logger.info(
        "Deleting task",
        extra={"tool_name": "delete_task", "task_key": task_key},
    )

    try:
        # Validate key format
        from ..models import validate_task_key

        try:
            validated_key = validate_task_key(task_key)
        except ValueError as e:
            raise PlanviewValidationError(f"Invalid task key format: {str(e)}") from e

        # Make SOAP request
        async with get_soap_client() as client:
            # Delete operation expects: keys (list of strings)
            request_params = {"keys": [validated_key]}

            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Delete",
                port_name=TASK_SERVICE_PORT,
                **request_params,
            )

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully deleted task",
                extra={
                    "tool_name": "delete_task",
                    "task_key": task_key,
                    "duration_ms": duration_ms,
                },
            )

            return result

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to delete task: {str(e)}",
            extra={
                "tool_name": "delete_task",
                "task_key": task_key,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
