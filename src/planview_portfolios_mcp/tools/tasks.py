"""Task management tools for Planview Portfolios SOAP API."""

import asyncio
import logging
from time import time
from typing import Any

from fastmcp import Context

from ..exceptions import PlanviewValidationError
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
        Dict with created task data including Key

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
    """
    start_time = time()
    logger.info("Creating task", extra={"tool_name": "create_task"})

    try:
        # Validate required fields
        _validate_task_fields(task_data)

        # Filter non-None and sort (Planview requirement)
        task_payload = filter_and_sort_fields(task_data)

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

            # Call SOAP Create operation (dict-first approach from test script)
            logger.info(f"Creating task with fields: {list(task_payload.keys())}")
            try:
                # Try dict directly (test script line 148 - works reliably)
                result_direct = await asyncio.to_thread(create_op, dtos=[task_payload])
                result = _handle_soap_result(result_direct)
            except Exception as e:
                # Fallback to TaskDto2 object
                logger.warning(f"Dict approach failed: {e}, trying TaskDto2 object")
                try:
                    task_dto_obj = task_dto_factory(**task_payload)
                    result_direct = await asyncio.to_thread(create_op, dtos=[task_dto_obj])
                    result = _handle_soap_result(result_direct)
                except Exception as e2:
                    logger.error(f"TaskDto2 object approach also failed: {e2}", exc_info=True)
                    raise

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
