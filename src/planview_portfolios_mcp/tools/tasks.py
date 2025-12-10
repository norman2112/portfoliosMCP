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
        try:
            task_dto = TaskDto2.model_validate(task_data)
        except Exception as e:
            raise PlanviewValidationError(f"Invalid task data: {str(e)}") from e

        # Convert to dict for zeep (use PascalCase for SOAP)
        task_dict = task_dto.model_dump(by_alias=True, exclude_none=True)
    # Sort keys alphabetically (Planview requires DTO fields in alphabetical order)
    task_dict = dict(sorted(task_dict.items()))

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
            
            # Try to get TaskDto2 type from zeep's type system
            # Based on error message, zeep expects TaskDto (not TaskDto2) in some contexts
            # Try both TaskDto2 and TaskDto namespaces
            task_dto_factory = None
            
            # List of type names to try (from WSDL and error messages)
            type_candidates = [
                # TaskDto2 with 2012/08 namespace (from WSDL examples)
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2",
                # TaskDto with 2010/01/01 namespace (from error message)
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto/2010/01/01}TaskDto",
            ]
            
            for type_name in type_candidates:
                try:
                    task_dto_factory = client.get_type(type_name)
                    logger.debug(f"Found TaskDto type: {type_name}")
                    break
                except (KeyError, AttributeError, TypeError) as e:
                    logger.debug(f"Type {type_name} not found: {e}")
                    continue
            
            # Create TaskDto object
            if task_dto_factory:
                try:
                    # Create typed object using zeep factory
                    task_dto = task_dto_factory(**task_dict)
                    logger.debug("Created TaskDto using zeep factory")
                except Exception as e:
                    logger.warning(f"Failed to create TaskDto with factory ({e}), using dict")
                    task_dto = task_dict
            else:
                # Fallback: use dict and let zeep serialize
                logger.debug("TaskDto factory not found, using dict")
                task_dto = task_dict

            # Build request - pass dtos as array
            # Create operation signature: Create(dtos: TaskDto2[], options?: WorkOptionsDto)
            request_kwargs = {"dtos": [task_dto]}
            if options_dict:
                request_kwargs["options"] = options_dict

            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Create",
                port_name=TASK_SERVICE_PORT,
                **request_kwargs,
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

            # Try to get TaskDto/TaskDto2 type
            task_dto_factory = None
            type_candidates = [
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto2/2012/08}TaskDto2",
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/TaskDto/2010/01/01}TaskDto",
            ]
            for type_name in type_candidates:
                try:
                    task_dto_factory = client.get_type(type_name)
                    break
                except Exception:
                    continue

            if task_dto_factory:
                try:
                    task_dto_obj = task_dto_factory(**task_dict)
                except Exception:
                    task_dto_obj = task_dict
            else:
                task_dto_obj = task_dict

            request_params = {"dtos": [task_dto_obj]}
            if options_dict:
                request_params["options"] = options_dict

            result = await make_soap_request(
                client,
                TASK_SERVICE_NAME,
                "Update",
                port_name=TASK_SERVICE_PORT,
                **request_params,
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
