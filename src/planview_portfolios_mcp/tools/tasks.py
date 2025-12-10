"""Task management tools for Planview Portfolios SOAP API."""

import logging
from time import time
from typing import Any

from fastmcp import Context

from ..exceptions import PlanviewValidationError
from ..models import TaskDto2, WorkOptionsDto
from ..soap_client import get_soap_client, make_soap_request

logger = logging.getLogger(__name__)

# Service name and port for TaskService
# The WSDL defines service "TaskService" with port "BasicHttpBinding_ITaskService3"
TASK_SERVICE_NAME = "TaskService"
TASK_SERVICE_PORT = "BasicHttpBinding_ITaskService3"


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

    Example:
        {
            "Description": "My Task",
            "FatherKey": "key://2/$Plan/12345",
            "Key": "ekey://2/namespace/task-1",
            "ScheduleStartDate": "2024-01-01T08:00:00",
            "ScheduleFinishDate": "2024-01-15T17:00:00"
        }
    """
    start_time = time()
    logger.info("Creating task", extra={"tool_name": "create_task"})

    try:
        # Validate task data
        if not isinstance(task_data, dict):
            raise PlanviewValidationError("task_data must be a dictionary")

        if "Description" not in task_data and "description" not in task_data:
            raise PlanviewValidationError(
                "task_data must include Description field"
            )
        if "FatherKey" not in task_data and "father_key" not in task_data:
            raise PlanviewValidationError(
                "task_data must include FatherKey field"
            )

        # Convert to TaskDto2 model (allows both snake_case and PascalCase)
        # Note: We validate but keep dates as strings (don't convert to datetime)
        # This matches the test script approach where dates are strings
        try:
            # Temporarily disable datetime parsing to keep as strings
            # We'll validate structure but not convert types
            task_dto = TaskDto2.model_validate(task_data, strict=False)
        except Exception as e:
            raise PlanviewValidationError(f"Invalid task data: {str(e)}") from e

        # Convert to dict for zeep (use PascalCase for SOAP)
        # Keep dates as strings - zeep expects ISO format strings, not datetime objects
        # Use mode='json' to ensure datetime objects (if any) are converted to strings
        task_dict = task_dto.model_dump(by_alias=True, exclude_none=True, mode='json')
        # Filter out None values explicitly (matches test script approach)
        # Sort keys alphabetically (Planview requires DTO fields in alphabetical order)
        task_dict = {k: v for k, v in sorted(task_dict.items()) if v is not None}
        
        # Ensure all date fields are strings (in case Pydantic converted them)
        # zeep needs ISO format strings like '2025-12-10T08:00:00'
        for key in ['ScheduleStartDate', 'ScheduleFinishDate', 'ActualStartDate', 'ActualFinishDate']:
            if key in task_dict and task_dict[key] is not None:
                if not isinstance(task_dict[key], str):
                    # Convert datetime to ISO string if somehow it's still a datetime
                    task_dict[key] = task_dict[key].isoformat()

        # Use TaskDto2 directly (2012/08 namespace) - matches SOAP examples in docs
        # TaskDto2 uses the same field names as our TaskDto2 model
        # No mapping needed - use task_dict directly
        task_payload = task_dict

        # Prepare options
        options_dict = None
        if options:
            try:
                options_dto = WorkOptionsDto.model_validate(options)
                options_dict = options_dto.model_dump(by_alias=True)
            except Exception as e:
                raise PlanviewValidationError(
                    f"Invalid options data: {str(e)}"
                ) from e

        # Make SOAP request
        async with get_soap_client() as client:
            # Get the service
            try:
                service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
            except (AttributeError, ValueError, KeyError, TypeError):
                service = client.service
            
            # Get the Create operation
            create_op = getattr(service, "Create")
            
            # Use TaskDto2 (2012/08 namespace) - matches SOAP examples in documentation
            # TaskDto2 uses fields like Description, FatherKey, Key, ScheduleStartDate, etc.
            # No StructureKey conversion needed - TaskDto2 accepts key URIs as strings
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2"
                )
            except Exception as e:
                raise PlanviewValidationError(
                    f"TaskDto2 type not found in WSDL: {e}"
                ) from e

            # Log payload before creating TaskDto2
            logger.debug(f"TaskDto2 payload has {len(task_payload)} fields: {list(task_payload.keys())}")
            
            # Verify required fields are present
            if "Description" not in task_payload:
                raise PlanviewValidationError("Description is required but missing from payload")
            if "FatherKey" not in task_payload:
                raise PlanviewValidationError("FatherKey is required but missing from payload")
            
            # Pass dict directly to zeep - it will serialize based on operation signature
            # zeep can handle dicts and convert them to TaskDto2 correctly
            logger.debug(f"Passing TaskDto2 as dict with {len(task_payload)} fields to zeep")
            
            # Create TaskDto2 object using factory
            # This is critical - zeep needs the typed object to serialize correctly
            try:
                logger.debug(f"Creating TaskDto2 with payload: {task_payload}")
                task_dto_obj = task_dto_factory(**task_payload)
                logger.debug(f"Created TaskDto2 typed object: {type(task_dto_obj)}")
                logger.debug(f"TaskDto2 fields count: {len(task_payload)}")
                # Verify the object has the required values
                desc = getattr(task_dto_obj, 'Description', None)
                father_key = getattr(task_dto_obj, 'FatherKey', None)
                logger.debug(f"TaskDto2.Description: {desc}")
                logger.debug(f"TaskDto2.FatherKey: {father_key}")
                if not desc:
                    raise PlanviewValidationError("TaskDto2 object missing Description after creation")
                if not father_key:
                    raise PlanviewValidationError("TaskDto2 object missing FatherKey after creation")
            except Exception as e:
                if isinstance(e, PlanviewValidationError):
                    raise
                logger.error(f"Failed to create TaskDto2 object: {e}", exc_info=True)
                raise PlanviewValidationError(
                    f"Failed to create TaskDto2 object: {e}"
                ) from e
            
            # Build request - pass dtos as array of TaskDto2 objects
            # zeep will serialize this correctly when the TaskDto2 object is properly created
            dtos_param = [task_dto_obj]
            logger.debug(f"Calling Create with dtos array containing {len(dtos_param)} TaskDto2 object(s)")
            logger.debug(f"dtos_param type: {type(dtos_param)}")
            logger.debug(f"dtos_param[0] type: {type(dtos_param[0])}")
            # Log the actual object attributes to verify it has values
            if hasattr(dtos_param[0], '__dict__'):
                logger.debug(f"TaskDto2 object __dict__ keys: {list(dtos_param[0].__dict__.keys())[:10]}")
            if hasattr(dtos_param[0], '__values__'):
                logger.debug(f"TaskDto2 object __values__: {dtos_param[0].__values__}")
            
            # Pass as keyword arguments matching WSDL parameter names
            kwargs = {"dtos": dtos_param}
            if options_dict:
                kwargs["options"] = options_dict

            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Create",
                port_name=TASK_SERVICE_PORT,
                **kwargs,
            )

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
    logger.info(
        "Reading task", extra={"tool_name": "read_task", "task_key": task_key}
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
            # Read operation expects: keys (list of strings)
            request_params = {"keys": [validated_key]}

            result = await make_soap_request(
                client, TASK_SERVICE_NAME, "Read", **request_params
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
                raise PlanviewValidationError(
                    f"Invalid options data: {str(e)}"
                ) from e

        # Make SOAP request
        async with get_soap_client() as client:
            # Bind service
            try:
                service = client.bind(TASK_SERVICE_NAME, port_name=TASK_SERVICE_PORT)
            except (AttributeError, ValueError, KeyError, TypeError):
                service = client.service

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
                task_dict["FatherInternalKey"] = create_structure_key(task_dict["FatherInternalKey"])
            if "ExternalKey" in task_dict:
                task_dict["ExternalKey"] = create_structure_key(task_dict["ExternalKey"])
            if "FatherExternalKey" in task_dict:
                task_dict["FatherExternalKey"] = create_structure_key(task_dict["FatherExternalKey"])

            # Use TaskDto (2010/01/01 namespace) as required by the service
            try:
                task_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto/2010/01/01}TaskDto"
                )
            except Exception as e:
                raise PlanviewValidationError(
                    f"TaskDto type not found in WSDL: {e}"
                ) from e

            try:
                task_dto_obj = task_dto_factory(**task_dict)
            except Exception as e:
                raise PlanviewValidationError(
                    f"Failed to create TaskDto object: {e}"
                ) from e

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

            result = await make_soap_request(
                client, TASK_SERVICE_NAME, "Delete", **request_params
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
