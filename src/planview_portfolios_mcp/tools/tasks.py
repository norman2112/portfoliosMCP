"""Task management tools for Planview Portfolios SOAP API."""

import asyncio
import logging
from datetime import datetime
from time import time
from typing import Any

from fastmcp import Context

from ..exceptions import PlanviewConnectionError, PlanviewValidationError
from ..models import TaskDto2, WorkOptionsDto
from ..soap_client import get_soap_client, make_soap_request, _handle_soap_result
from ..utils.soap_helpers import filter_and_sort_fields

logger = logging.getLogger(__name__)

# Service name and port for TaskService
# The WSDL defines service "TaskService" with port "BasicHttpBinding_ITaskService3"
TASK_SERVICE_NAME = "TaskService"
TASK_SERVICE_PORT = "BasicHttpBinding_ITaskService3"


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
        Dict with:
        - success: True if operation succeeded
        - data: List of created task data (may have null fields - normal SOAP behavior)
        - successes: List of successfully created tasks
        - failures: List of failed tasks (if any)
        - warnings: List of non-fatal warnings
        
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
        - If some tasks fail, they'll be in the failures array but other tasks
          will still be created
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
            result = _handle_soap_result(result_direct)
            
            # Enhanced result parsing for batch operations
            duration_ms = int((time() - start_time) * 1000)
            
            # Extract successes and failures from the result
            batch_result = {
                "success": result.get("success", True),
                "data": result.get("data", {}),
                "warnings": result.get("warnings", []),
            }
            
            # If result has multiple successes (from _handle_soap_result parsing),
            # include them in the response
            if "successes" in result:
                batch_result["successes"] = result["successes"]
            if "failures" in result:
                batch_result["failures"] = result["failures"]
            
            logger.info(
                f"Successfully batch created {len(final_task_dtos)} tasks",
                extra={
                    "tool_name": "batch_create_tasks",
                    "task_count": len(final_task_dtos),
                    "duration_ms": duration_ms,
                },
            )
            
            return batch_result
            
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

            result = await make_soap_request(client, TASK_SERVICE_NAME, "Read", **request_params)

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


async def update_task(
    ctx: Context,
    task_key: str,
    task_data: dict[str, Any],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update an existing task using SOAP TaskService.

    Updates a task in Planview Portfolios using the SOAP API.

    Args:
        ctx: FastMCP context
        task_key: Task key URI in key://, search://, or ekey:// format
        task_data: Partial task data dictionary with TaskDto2 fields to update.
            All fields are optional for updates.
        options: Optional WorkOptionsDto dictionary (same as create_task)

    Returns:
        Dict with updated task data

    Raises:
        PlanviewValidationError: If task_key or task_data is invalid
        PlanviewNotFoundError: If task is not found
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors
    """
    start_time = time()
    logger.info(
        "Updating task",
        extra={"tool_name": "update_task", "task_key": task_key},
    )

    try:
        # Validate key format
        from ..models import validate_task_key

        try:
            validated_key = validate_task_key(task_key)
        except ValueError as e:
            raise PlanviewValidationError(f"Invalid task key format: {str(e)}") from e

        # Validate task data
        if not isinstance(task_data, dict):
            raise PlanviewValidationError("task_data must be a dictionary")

        # Convert to TaskDto2 model (allows partial updates)
        try:
            # For updates, we need to include the key in the DTO
            task_data_with_key = {**task_data, "Key": validated_key}
            task_dto = TaskDto2.model_validate(task_data_with_key)
        except Exception as e:
            raise PlanviewValidationError(f"Invalid task data: {str(e)}") from e

        # Convert to dict for zeep (use PascalCase for SOAP)
        # Note: DTO fields must be in alphabetical order per Planview docs
        task_dict = task_dto.model_dump(by_alias=True, exclude_none=True)
        # Sort dict keys alphabetically to match Planview requirement
        task_dict = dict(sorted(task_dict.items()))

        # Map to TaskDto (2010 schema)
        mapped: dict[str, Any] = {}
        key_val = task_dict.get("Key")
        father_key_val = task_dict.get("FatherKey")
        if key_val:
            if str(key_val).startswith(("ekey://", "search://")):
                mapped["ExternalKey"] = key_val
            else:
                mapped["InternalKey"] = key_val
        if father_key_val:
            if str(father_key_val).startswith(("ekey://", "search://")):
                mapped["FatherExternalKey"] = father_key_val
            else:
                mapped["FatherInternalKey"] = father_key_val
        if "ScheduleStartDate" in task_dict:
            mapped["StartDate"] = task_dict["ScheduleStartDate"]
        if "ScheduleFinishDate" in task_dict:
            mapped["FinishDate"] = task_dict["ScheduleFinishDate"]
        if "ActualStartDate" in task_dict:
            mapped["ActualStart"] = task_dict["ActualStartDate"]
        if "ActualFinishDate" in task_dict:
            mapped["ActualFinish"] = task_dict["ActualFinishDate"]
        for src, dest in [
            ("Description", "Description"),
            ("Duration", "Duration"),
            ("EnterProgress", "EnterProgress"),
            ("IsDeliverable", "IsDeliverable"),
            ("IsMilestone", "IsMilestone"),
            ("IsTicketable", "IsTicketable"),
            ("PercentComplete", "PercentComplete"),
            ("Place", "Place"),
            ("Notes", "Notes"),
            ("Status", "Status"),
            ("CalendarKey", "Calendar"),
            ("ShortName", "ShortName"),
        ]:
            if src in task_dict:
                mapped[dest] = task_dict[src]

        # Use mapped dict going forward (drop original keys not supported by TaskDto)
        task_dict = dict(sorted(mapped.items()))

        # Prepare options
        options_dict = None
        if options:
            try:
                options_dto = WorkOptionsDto.model_validate(options)
                options_dict = options_dto.model_dump(by_alias=True)
            except Exception as e:
                raise PlanviewValidationError(f"Invalid options data: {str(e)}") from e

        # Make SOAP request
        async with get_soap_client() as client:
            # Get StructureKey type for key fields
            structure_key_factory = None
            try:
                structure_key_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/StructureKey/2010/01/01}StructureKey"
                )
            except Exception:
                pass

            def create_structure_key(key_uri: str):
                """Create StructureKey object or dict from key URI."""
                if structure_key_factory:
                    for prop_name in ["Key", "Uri", "Value", "KeyUri"]:
                        try:
                            return structure_key_factory(**{prop_name: key_uri})
                        except Exception:
                            continue
                    try:
                        return structure_key_factory(key_uri)
                    except Exception:
                        pass
                return {"Key": key_uri}

            # Convert key fields to StructureKey objects/dicts
            if "InternalKey" in task_dict:
                task_dict["InternalKey"] = create_structure_key(task_dict["InternalKey"])
            if "FatherInternalKey" in task_dict:
                task_dict["FatherInternalKey"] = create_structure_key(
                    task_dict["FatherInternalKey"]
                )
            if "ExternalKey" in task_dict:
                task_dict["ExternalKey"] = create_structure_key(task_dict["ExternalKey"])
            if "FatherExternalKey" in task_dict:
                task_dict["FatherExternalKey"] = create_structure_key(
                    task_dict["FatherExternalKey"]
                )

            # Use TaskDto (2010/01/01 namespace) as required by the service
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto/2010/01/01}TaskDto"
                )
            except Exception as e:
                raise PlanviewValidationError(f"TaskDto type not found in WSDL: {e}") from e

            try:
                task_dto_obj = task_dto_factory(**task_dict)
            except Exception as e:
                raise PlanviewValidationError(f"Failed to create TaskDto object: {e}") from e

            dtos_param = [task_dto_obj]
            kwargs = {"dtos": dtos_param}
            if options_dict:
                kwargs["options"] = options_dict

            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Update",
                port_name=TASK_SERVICE_PORT,
                **kwargs,
            )

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully updated task",
                extra={
                    "tool_name": "update_task",
                    "task_key": task_key,
                    "duration_ms": duration_ms,
                },
            )

            return result

    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to update task: {str(e)}",
            extra={
                "tool_name": "update_task",
                "task_key": task_key,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def batch_update_tasks(
    ctx: Context,
    tasks: list[dict[str, Any]],
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Batch update multiple tasks in a single SOAP call.
    
    Much faster than calling update_task() multiple times. Updates all tasks
    in a single SOAP request, significantly reducing latency for bulk updates.
    
    Args:
        ctx: FastMCP context
        tasks: List of task update dictionaries. Each dict must contain:
            - task_key: Task key URI (required) - identifies which task to update
            - task_data: Dict with TaskDto2 fields to update (optional fields only)
        options: Optional WorkOptionsDto dictionary (applies to all tasks)
        
    Returns:
        Dict with:
        - success: True if operation succeeded
        - data: List of updated task data (may have null fields - normal SOAP behavior)
        - successes: List of successfully updated tasks
        - failures: List of failed tasks (if any)
        - warnings: List of non-fatal warnings
        
    Raises:
        PlanviewValidationError: If task data is invalid
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors
        
    Example:
        tasks = [
            {
                "task_key": "key://2/$Plan/17346",
                "task_data": {
                    "PercentComplete": 50,
                    "Notes": "In progress"
                }
            },
            {
                "task_key": "key://2/$Plan/17347",
                "task_data": {
                    "PercentComplete": 100,
                    "Notes": "Completed"
                }
            }
        ]
        result = await batch_update_tasks(ctx, tasks)
        
    Notes:
        - All tasks are updated in a single SOAP call, making this much faster
          than individual update_task() calls
        - If some tasks fail, they'll be in the failures array but other tasks
          will still be updated
        - Response fields may be null - this is normal SOAP API behavior
        - Use read_task() to verify individual tasks if needed
    """
    start_time = time()
    logger.info(
        "Batch updating tasks",
        extra={"tool_name": "batch_update_tasks", "task_count": len(tasks)},
    )
    
    if not tasks:
        raise PlanviewValidationError("tasks list cannot be empty")
    
    if not isinstance(tasks, list):
        raise PlanviewValidationError("tasks must be a list")
    
    try:
        from ..models import validate_task_key
        
        # Prepare options
        options_dict = None
        if options:
            try:
                options_dto = WorkOptionsDto.model_validate(options)
                options_dict = options_dto.model_dump(by_alias=True, exclude_none=True)
            except Exception as e:
                raise PlanviewValidationError(f"Invalid options: {str(e)}") from e
        
        # Build list of TaskDto objects for batch update
        task_dto_objects = []
        task_keys = []  # Track keys for logging
        
        for i, task_update in enumerate(tasks):
            if not isinstance(task_update, dict):
                raise PlanviewValidationError(
                    f"Task {i} must be a dictionary. Got: {type(task_update).__name__}"
                )
            
            task_key = task_update.get("task_key") or task_update.get("taskKey")
            if not task_key:
                raise PlanviewValidationError(
                    f"Task {i} missing required 'task_key' field"
                )
            
            task_data = task_update.get("task_data") or task_update.get("taskData") or {}
            if not isinstance(task_data, dict):
                raise PlanviewValidationError(
                    f"Task {i} 'task_data' must be a dictionary. Got: {type(task_data).__name__}"
                )
            
            # Validate key format
            try:
                validated_key = validate_task_key(task_key)
            except ValueError as e:
                raise PlanviewValidationError(
                    f"Task {i} has invalid task_key format: {str(e)}"
                ) from e
            
            # Merge key into task_data for DTO creation
            task_data_with_key = {**task_data, "Key": validated_key}
            
            # Convert to TaskDto2 model (allows partial updates)
            try:
                task_dto = TaskDto2.model_validate(task_data_with_key)
            except Exception as e:
                raise PlanviewValidationError(
                    f"Task {i} has invalid task_data: {str(e)}"
                ) from e
            
            # Convert to dict for zeep (PascalCase, sorted alphabetically)
            task_dict = task_dto.model_dump(by_alias=True, exclude_none=True)
            task_dict = dict(sorted(task_dict.items()))
            
            # Map to TaskDto (2010 schema) - same logic as update_task
            mapped: dict[str, Any] = {}
            key_val = task_dict.get("Key")
            father_key_val = task_dict.get("FatherKey")
            if key_val:
                if str(key_val).startswith(("ekey://", "search://")):
                    mapped["ExternalKey"] = key_val
                else:
                    mapped["InternalKey"] = key_val
            if father_key_val:
                if str(father_key_val).startswith(("ekey://", "search://")):
                    mapped["FatherExternalKey"] = father_key_val
                else:
                    mapped["FatherInternalKey"] = father_key_val
            if "ScheduleStartDate" in task_dict:
                mapped["StartDate"] = task_dict["ScheduleStartDate"]
            if "ScheduleFinishDate" in task_dict:
                mapped["FinishDate"] = task_dict["ScheduleFinishDate"]
            if "ActualStartDate" in task_dict:
                mapped["ActualStart"] = task_dict["ActualStartDate"]
            if "ActualFinishDate" in task_dict:
                mapped["ActualFinish"] = task_dict["ActualFinishDate"]
            for src, dest in [
                ("Description", "Description"),
                ("Duration", "Duration"),
                ("EnterProgress", "EnterProgress"),
                ("IsDeliverable", "IsDeliverable"),
                ("IsMilestone", "IsMilestone"),
                ("IsTicketable", "IsTicketable"),
                ("PercentComplete", "PercentComplete"),
                ("Place", "Place"),
                ("Notes", "Notes"),
                ("Status", "Status"),
                ("CalendarKey", "Calendar"),
                ("ShortName", "ShortName"),
            ]:
                if src in task_dict:
                    mapped[dest] = task_dict[src]
            
            task_dict = dict(sorted(mapped.items()))
            task_keys.append(validated_key)
            
            # Store the mapped dict for later processing with client (before StructureKey conversion)
            task_dto_objects.append(task_dict)
        
        # Make batch SOAP request with all tasks
        async with get_soap_client() as client:
            # Get StructureKey type for key fields
            structure_key_factory = None
            try:
                structure_key_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/StructureKey/2010/01/01}StructureKey"
                )
            except Exception:
                pass
            
            def create_structure_key(key_uri: str):
                """Create StructureKey object or dict from key URI."""
                if structure_key_factory:
                    for prop_name in ["Key", "Uri", "Value", "KeyUri"]:
                        try:
                            return structure_key_factory(**{prop_name: key_uri})
                        except Exception:
                            continue
                    try:
                        return structure_key_factory(key_uri)
                    except Exception:
                        pass
                return {"Key": key_uri}
            
            # Get TaskDto factory
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto/2010/01/01}TaskDto"
                )
            except Exception as e:
                raise PlanviewConnectionError(f"TaskDto type not found in WSDL: {e}") from e
            
            # Process all tasks and create DTO objects
            final_task_dtos = []
            for i, task_dict in enumerate(task_dto_objects):
                # Make a copy to avoid modifying the original
                task_dict_copy = dict(task_dict)
                
                # Convert key fields to StructureKey objects/dicts
                if "InternalKey" in task_dict_copy:
                    task_dict_copy["InternalKey"] = create_structure_key(task_dict_copy["InternalKey"])
                if "FatherInternalKey" in task_dict_copy:
                    task_dict_copy["FatherInternalKey"] = create_structure_key(
                        task_dict_copy["FatherInternalKey"]
                    )
                if "ExternalKey" in task_dict_copy:
                    task_dict_copy["ExternalKey"] = create_structure_key(task_dict_copy["ExternalKey"])
                if "FatherExternalKey" in task_dict_copy:
                    task_dict_copy["FatherExternalKey"] = create_structure_key(
                        task_dict_copy["FatherExternalKey"]
                    )
                
                try:
                    task_dto_obj = task_dto_factory(**task_dict_copy)
                    final_task_dtos.append(task_dto_obj)
                except Exception as e:
                    raise PlanviewValidationError(
                        f"Task {i} failed to create TaskDto object: {e}"
                    ) from e
            
            dtos_param = final_task_dtos
            kwargs = {"dtos": dtos_param}
            if options_dict:
                kwargs["options"] = options_dict
            
            logger.info(f"Batch updating {len(final_task_dtos)} tasks in single SOAP call")
            
            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Update",
                port_name=TASK_SERVICE_PORT,
                **kwargs,
            )
            
            # Enhanced result parsing for batch operations
            # The result may contain multiple successes/failures
            duration_ms = int((time() - start_time) * 1000)
            
            # Extract successes and failures from the result
            batch_result = {
                "success": result.get("success", True),
                "data": result.get("data", {}),
                "warnings": result.get("warnings", []),
            }
            
            # If result has multiple successes (from _handle_soap_result parsing),
            # include them in the response
            if "successes" in result:
                batch_result["successes"] = result["successes"]
            if "failures" in result:
                batch_result["failures"] = result["failures"]
            
            logger.info(
                f"Successfully batch updated {len(final_task_dtos)} tasks",
                extra={
                    "tool_name": "batch_update_tasks",
                    "task_count": len(final_task_dtos),
                    "duration_ms": duration_ms,
                },
            )
            
            return batch_result
            
    except PlanviewValidationError:
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to batch update tasks: {str(e)}",
            extra={
                "tool_name": "batch_update_tasks",
                "task_count": len(tasks) if tasks else 0,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


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

            result = await make_soap_request(client, TASK_SERVICE_NAME, "Delete", **request_params)

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
