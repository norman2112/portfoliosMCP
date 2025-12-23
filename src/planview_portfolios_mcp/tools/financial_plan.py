"""Financial plan management tools for Planview Portfolios SOAP API."""

import asyncio
import json
import logging
from time import time
from typing import Any

from fastmcp import Context

from ..exceptions import PlanviewConnectionError, PlanviewNotFoundError, PlanviewValidationError
from ..soap_client import get_soap_client_for_service, _handle_soap_result
from ..utils.soap_helpers import filter_and_sort_fields

logger = logging.getLogger(__name__)

# Service name and port for FinancialPlanService
# The WSDL defines service "FinancialPlanService" with interface "IFinancialPlanService2"
FINANCIAL_PLAN_SERVICE_NAME = "FinancialPlanService"
FINANCIAL_PLAN_SERVICE_PORT = "BasicHttpBinding_IFinancialPlanService2"


def _validate_financial_plan_fields(plan_data: dict[str, Any]) -> None:
    """Validate required financial plan fields.

    Args:
        plan_data: Financial plan data dictionary

    Raises:
        PlanviewValidationError: If required fields missing or invalid

    Notes:
        Required fields: Either Key OR (EntityKey + VersionKey)
        Also requires Lines array with at least one line
    """
    if not isinstance(plan_data, dict):
        raise PlanviewValidationError(
            f"plan_data must be a dictionary. Got: {type(plan_data).__name__}"
        )

    has_key = any(k.lower() == "key" for k in plan_data)
    has_entity_key = any(k.lower() == "entitykey" for k in plan_data)
    has_version_key = any(k.lower() == "versionkey" for k in plan_data)

    # Must have Key OR (EntityKey + VersionKey)
    if not has_key and not (has_entity_key and has_version_key):
        available_keys = list(plan_data.keys())
        raise PlanviewValidationError(
            f"Either Key OR both EntityKey and VersionKey fields are required. "
            f"Available keys: {available_keys}"
        )

    # Must have Lines
    lines = plan_data.get("Lines") or plan_data.get("lines")
    if not lines:
        raise PlanviewValidationError(
            f"Lines field is required with at least one line. "
            f"Available keys: {list(plan_data.keys())}"
        )


def _validate_financial_plan_line(line_data: dict[str, Any]) -> None:
    """Validate required financial plan line fields.

    Args:
        line_data: Financial plan line data dictionary

    Raises:
        PlanviewValidationError: If required fields missing
    """
    if not isinstance(line_data, dict):
        raise PlanviewValidationError("Each line must be a dictionary")

    has_account_key = any(k.lower() == "accountkey" for k in line_data)
    has_unit = any(k.lower() == "unit" for k in line_data)
    has_entries = any(k.lower() == "entries" for k in line_data)

    if not has_account_key:
        raise PlanviewValidationError("AccountKey field is required for each line")
    if not has_unit:
        raise PlanviewValidationError("Unit field is required for each line")
    if not has_entries:
        raise PlanviewValidationError("Entries field is required for each line")

    # Validate entries
    entries = line_data.get("Entries") or line_data.get("entries")
    if not entries or not isinstance(entries, list) or len(entries) == 0:
        raise PlanviewValidationError(
            "Entries must be a non-empty list with at least one entry"
        )

    # Validate each entry
    for entry in entries:
        if not isinstance(entry, dict):
            raise PlanviewValidationError("Each entry must be a dictionary")
        has_period_key = any(k.lower() == "periodkey" for k in entry)
        has_value = any(k.lower() == "value" for k in entry)
        if not has_period_key:
            raise PlanviewValidationError("PeriodKey field is required for each entry")
        if not has_value:
            raise PlanviewValidationError("Value field is required for each entry")


async def upsert_financial_plan(
    ctx: Context,
    plan_data: dict[str, Any],
) -> dict[str, Any]:
    """Upsert (create or update) a financial plan using SOAP FinancialPlanService.

    Creates or updates a financial plan in Planview Portfolios using the SOAP API.
    This is a single-line update tool optimized for simple use cases.

    Args:
        ctx: FastMCP context
        plan_data: Financial plan data dictionary. Required fields:
            - Key: Financial plan key URI (e.g., "ekey://12/MyPlan") OR
            - EntityKey: Entity key URI (e.g., "key://2/$Plan/17286") AND
            - VersionKey: Version key URI (e.g., "key://14/57")
            - Lines: List of FinancialPlanLineDto dictionaries
        Each FinancialPlanLineDto requires:
            - AccountKey: Account key URI (e.g., "key://2/$Account/13607")
            - Unit: Unit type ("Currency", "Units", "Unit Cost", "Unit Price", "FTE", "Hours")
            - Entries: List of EntryDto dictionaries
            - CurrencyKey: Currency key URI (defaults to "key://1/USD" if not provided)
            - Attributes: Optional list of LineAttributeDto dictionaries
        Each EntryDto requires:
            - PeriodKey: Period key URI (e.g., "key://16/197")
            - Value: Numeric value

    Returns:
        Dict with:
        - success: True if operation succeeded
        - data: Financial plan DTO (may have empty Lines array - this is normal SOAP API behavior)
        - warnings: List of non-fatal warnings (e.g., "InvalidStructureCode", "InvalidDefaultValues")
        
        Note: The SOAP API may return empty Lines array in the response even though data was persisted.
        This is expected behavior - use read_financial_plan() to verify the data was saved.

    Raises:
        PlanviewValidationError: If plan data is invalid
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors

    Examples:
        Minimal (single line, single period):
            {
                "EntityKey": "key://2/$Plan/17286",
                "VersionKey": "key://14/57",
                "Lines": [{
                    "AccountKey": "key://2/$Account/13607",
                    "Unit": "Currency",
                    "CurrencyKey": "key://1/USD",
                    "Entries": [{
                        "PeriodKey": "key://16/197",
                        "Value": 10000
                    }]
                }]
            }

        Using existing plan Key:
            {
                "Key": "ekey://12/MyPlan",
                "Lines": [{
                    "AccountKey": "key://2/$Account/13607",
                    "Unit": "Currency",
                    "Entries": [{
                        "PeriodKey": "key://16/197",
                        "Value": 10000
                    }]
                }]
            }

    Notes:
        - Field names must use PascalCase (e.g., AccountKey, not account_key)
        - Only changed or added lines must be sent
        - AccountKey and PeriodKey must match Planview configuration
        - Unit types: "Currency", "Units", "Unit Cost", "Unit Price", "FTE", "Hours"
        - For new projects, the financial plan may not exist yet - upsert will create it
        
    Common Errors and Solutions:
        - "No editable lines were provided": The account/period keys don't match the model.
          Solution: Use discover_financial_plan_info() or read_financial_plan() to find valid keys.
        - "Account not found in model": The specified account doesn't exist for this version.
          Solution: Use discover_financial_plan_info() with a reference project to discover valid accounts.
        - "Unable to find the requested Financial Plan": Plan doesn't exist (common for new projects).
          Solution: Use upsert_financial_plan() directly - it creates the plan if needed.
    
    Known SOAP API Behaviors:
        - Response may show empty Lines array: The SOAP API doesn't always echo back the full payload.
          This is normal - the data IS persisted. Use read_financial_plan() to verify.
        - Warnings are non-fatal: Warnings like "InvalidStructureCode" or "InvalidDefaultValues" 
          indicate configuration issues but don't prevent successful creation. Check the warnings 
          array in the response for details.
    """
    start_time = time()
    logger.info("Upserting financial plan", extra={"tool_name": "upsert_financial_plan"})

    try:
        # Validate required fields
        _validate_financial_plan_fields(plan_data)

        # Normalize field names to PascalCase and prepare the payload
        plan_payload: dict[str, Any] = {}
        
        # Handle Key, EntityKey, VersionKey
        for key in ["Key", "EntityKey", "VersionKey"]:
            if key in plan_data:
                plan_payload[key] = plan_data[key]
            elif key.lower() in plan_data:
                plan_payload[key] = plan_data[key.lower()]

        # Handle optional Note field
        if "Note" in plan_data:
            plan_payload["Note"] = plan_data["Note"]
        elif "note" in plan_data:
            plan_payload["Note"] = plan_data["note"]

        # Process Lines
        lines = plan_data.get("Lines") or plan_data.get("lines", [])
        if not isinstance(lines, list):
            raise PlanviewValidationError("Lines must be a list")

        processed_lines = []
        for line in lines:
            _validate_financial_plan_line(line)
            
            # Normalize line to PascalCase
            line_payload: dict[str, Any] = {}
            
            # Required fields
            for field in ["AccountKey", "Unit"]:
                if field in line:
                    line_payload[field] = line[field]
                elif field.lower() in line:
                    line_payload[field] = line[field.lower()]

            # Optional CurrencyKey (default to USD if not provided)
            if "CurrencyKey" in line:
                line_payload["CurrencyKey"] = line["CurrencyKey"]
            elif "currencykey" in line:
                line_payload["CurrencyKey"] = line["currencykey"]
            else:
                line_payload["CurrencyKey"] = "key://1/USD"  # Default to USD

            # Process Entries
            entries = line.get("Entries") or line.get("entries", [])
            processed_entries = []
            for entry in entries:
                entry_payload: dict[str, Any] = {}
                if "PeriodKey" in entry:
                    entry_payload["PeriodKey"] = entry["PeriodKey"]
                elif "periodkey" in entry:
                    entry_payload["PeriodKey"] = entry["periodkey"]
                
                if "Value" in entry:
                    entry_payload["Value"] = entry["Value"]
                elif "value" in entry:
                    entry_payload["Value"] = entry["value"]
                
                processed_entries.append(entry_payload)
            line_payload["Entries"] = processed_entries

            # Optional Attributes
            if "Attributes" in line or "attributes" in line:
                attributes = line.get("Attributes") or line.get("attributes", [])
                if attributes:
                    processed_attributes = []
                    for attr in attributes:
                        attr_payload: dict[str, Any] = {}
                        if "AltStructureKey" in attr:
                            attr_payload["AltStructureKey"] = attr["AltStructureKey"]
                        elif "altstructurekey" in attr:
                            attr_payload["AltStructureKey"] = attr["altstructurekey"]
                        processed_attributes.append(attr_payload)
                    line_payload["Attributes"] = processed_attributes

            # Optional Note for line
            if "Note" in line:
                line_payload["Note"] = line["Note"]
            elif "note" in line:
                line_payload["Note"] = line["note"]

            processed_lines.append(line_payload)

        plan_payload["Lines"] = processed_lines

        logger.info(f"Processed financial plan payload with {len(processed_lines)} line(s)")

        # Make SOAP request using FinancialPlanService
        financial_plan_service_path = "/planview/services/FinancialPlanService.svc"
        async with get_soap_client_for_service(financial_plan_service_path) as client:
            # Get the service
            try:
                service = client.bind(FINANCIAL_PLAN_SERVICE_NAME, port_name=FINANCIAL_PLAN_SERVICE_PORT)
            except (AttributeError, ValueError, KeyError, TypeError) as e:
                logger.debug(f"Binding with service name failed: {e}, trying client.service")
                service = client.service

            # Get the Upsert operation
            upsert_op = getattr(service, "Upsert")

            # Get DTO factories for nested objects and ArrayOf wrappers
            try:
                financial_plan_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanDto/2013/03}FinancialPlanDto"
                )
                financial_plan_line_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03}FinancialPlanLineDto"
                )
                entry_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01}EntryDto"
                )
                # ArrayOf wrapper types are required for proper serialization
                array_of_entry_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01}ArrayOfEntryDto"
                )
                array_of_financial_plan_line_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03}ArrayOfFinancialPlanLineDto"
                )
                array_of_financial_plan_dto_factory = client.get_type(
                    "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanDto/2013/03}ArrayOfFinancialPlanDto"
                )
            except Exception as e:
                raise PlanviewConnectionError(f"DTO type not found in WSDL: {e}") from e

            # Build nested DTO objects with ArrayOf wrappers:
            # EntryDto -> ArrayOfEntryDto -> FinancialPlanLineDto -> ArrayOfFinancialPlanLineDto -> FinancialPlanDto -> ArrayOfFinancialPlanDto
            logger.info("Creating nested DTO objects with ArrayOf wrappers...")
            
            # Create EntryDto objects for each line, wrapped in ArrayOfEntryDto
            line_dto_objects = []
            for line_data in processed_lines:
                # Make a copy so we don't modify the original
                line_dict = dict(line_data)
                entries = line_dict.pop("Entries", [])
                
                # Create EntryDto objects
                entry_objects = []
                for entry in entries:
                    entry_obj = entry_dto_factory(**entry)
                    entry_objects.append(entry_obj)
                
                # Wrap EntryDto objects in ArrayOfEntryDto
                array_of_entries = array_of_entry_dto_factory(entry_objects)
                
                # Create FinancialPlanLineDto with ArrayOfEntryDto
                line_dict["Entries"] = array_of_entries
                line_dto_obj = financial_plan_line_dto_factory(**line_dict)
                line_dto_objects.append(line_dto_obj)
            
            # Wrap FinancialPlanLineDto objects in ArrayOfFinancialPlanLineDto
            array_of_lines = array_of_financial_plan_line_dto_factory(line_dto_objects)
            
            # Create FinancialPlanDto with ArrayOfFinancialPlanLineDto
            plan_data_for_dto = {k: v for k, v in plan_payload.items() if k != "Lines"}
            plan_data_for_dto["Lines"] = array_of_lines
            
            logger.info(f"About to create FinancialPlanDto with keys: {list(plan_data_for_dto.keys())}")
            logger.info(f"  EntityKey: {plan_data_for_dto.get('EntityKey')}")
            logger.info(f"  VersionKey: {plan_data_for_dto.get('VersionKey')}")
            logger.info(f"  Lines count: {len(line_dto_objects)}")
            
            try:
                plan_dto_obj = financial_plan_dto_factory(**plan_data_for_dto)
                logger.info(f"Created FinancialPlanDto object: {type(plan_dto_obj)}")
                # Try to inspect the object
                if hasattr(plan_dto_obj, 'EntityKey'):
                    logger.info(f"  FinancialPlanDto.EntityKey: {plan_dto_obj.EntityKey}")
                if hasattr(plan_dto_obj, 'Lines'):
                    lines_attr = getattr(plan_dto_obj, 'Lines', None)
                    logger.info(f"  FinancialPlanDto.Lines type: {type(lines_attr)}, value: {lines_attr}")
                    if lines_attr:
                        logger.info(f"  FinancialPlanDto.Lines length: {len(lines_attr)}")
            except Exception as e:
                logger.error(f"Failed to create FinancialPlanDto object: {e}", exc_info=True)
                raise
            
            # Call SOAP Upsert operation
            # CRITICAL: Must wrap FinancialPlanDto in ArrayOfFinancialPlanDto and pass directly to dtos
            # Passing [plan_dto_obj] results in empty serialization
            logger.info("Calling Upsert with ArrayOfFinancialPlanDto...")
            try:
                # Wrap the plan DTO in ArrayOfFinancialPlanDto
                plan_array = array_of_financial_plan_dto_factory([plan_dto_obj])
                # Pass the ArrayOf wrapper directly to dtos (not a list containing it)
                result = await asyncio.to_thread(upsert_op, dtos=plan_array)
                logger.info("✅ Financial plan upsert succeeded!")
            except Exception as e:
                logger.error(f"Financial plan upsert failed: {e}", exc_info=True)
                raise

            # Handle the result
            try:
                processed_result = _handle_soap_result(result)
            except Exception as e:
                # Log the raw result for debugging
                logger.error(f"SOAP result handling failed. Raw result type: {type(result)}")
                if hasattr(result, '__dict__'):
                    logger.error(f"Raw result dict: {result.__dict__}")
                raise

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully upserted financial plan",
                extra={"tool_name": "upsert_financial_plan", "duration_ms": duration_ms},
            )

            return processed_result

    except PlanviewValidationError as e:
        # Enhance error messages with actionable guidance
        error_str = str(e)
        
        # Check for "No editable lines" error - common when accounts/periods don't match model
        if "No editable lines were provided" in error_str or "No editable lines" in error_str:
            entity_key = plan_data.get("EntityKey") or plan_data.get("entitykey") or "unknown"
            version_key = plan_data.get("VersionKey") or plan_data.get("versionkey") or "unknown"
            
            guidance = (
                f"\n\nGuidance: The financial plan was rejected because the provided account/period keys "
                f"don't match the editable accounts and periods available in the model for this version. "
                f"This typically happens when:\n"
                f"1. The account keys don't exist in the financial model for version {version_key}\n"
                f"2. The period keys don't exist in the model\n"
                f"3. The version {version_key} is not editable\n\n"
                f"To resolve this:\n"
                f"1. Use 'discover_financial_plan_info' to discover valid account and period keys from "
                f"an existing project with a working financial plan (e.g., structure code 3818)\n"
                f"2. Use 'read_financial_plan' to read the financial plan for a similar project and "
                f"extract the AccountKey and PeriodKey values from existing lines\n"
                f"3. Use 'get_account_key()' and 'get_period_key()' from financial_plan_config for "
                f"instance-specific defaults\n"
                f"4. Try using version 'key://14/1' (Actual/Forecast) which is typically editable"
            )
            
            raise PlanviewValidationError(error_str + guidance) from e
        
        # Check for "Account not found" error
        if "Account not found" in error_str:
            guidance = (
                f"\n\nGuidance: The specified account key doesn't exist in the financial model. "
                f"Use 'discover_financial_plan_info' or 'read_financial_plan' to discover valid account keys."
            )
            raise PlanviewValidationError(error_str + guidance) from e
        
        # Re-raise other validation errors as-is
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"Failed to upsert financial plan: {str(e)}",
            extra={
                "tool_name": "upsert_financial_plan",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise


async def discover_financial_plan_info(
    ctx: Context,
    entity_key: str,
    version_key: str = "key://14/1",
    reference_entity_key: str | None = None,
    skip_target_read: bool = False,
) -> dict[str, Any] | None:
    """Discover financial plan information with smart fallback.
    
    Attempts to read the financial plan for the target project. If that fails
    (e.g., project is too new), falls back to reading a reference project's
    financial plan to discover available accounts and periods.
    
    Optimized to check config data first (instant), and skip slow target reads
    for new projects when skip_target_read=True.
    
    Args:
        ctx: FastMCP context
        entity_key: Target project entity key (e.g., "key://2/$Plan/17291")
        version_key: Financial plan version key (default: "key://14/1" for Actual/Forecast)
        reference_entity_key: Optional reference project entity key for fallback.
            Defaults to None - if not provided and target read fails, returns config data.
        skip_target_read: If True, skip reading target project's plan (much faster for new projects).
            Defaults to False for backward compatibility.
        
    Returns:
        Dict with financial plan data including accounts and periods, or None if unavailable.
        May return config-based data structure for fast path.
        
    Example:
        # Fast path for new projects - skip target read, use config or reference
        plan_info = await discover_financial_plan_info(
            ctx,
            entity_key="key://2/$Plan/17291",
            reference_entity_key="key://2/$Plan/3818",
            skip_target_read=True  # Skip slow read for new project
        )
        
        # Standard path - try target first, then reference
        plan_info = await discover_financial_plan_info(
            ctx,
            entity_key="key://2/$Plan/17291",
            reference_entity_key="key://2/$Plan/3818"
        )
        
        if plan_info:
            # Extract accounts and periods
            lines = plan_info.get("data", {}).get("Lines", {}).get("FinancialPlanLineDto", [])
    """
    # Fast path: If we're skipping target read, go straight to reference or config
    if skip_target_read:
        logger.info(f"Skipping target project read for {entity_key} (optimization)")
        
        # Try reference project first (if provided)
        if reference_entity_key:
            try:
                logger.info(f"Reading reference project {reference_entity_key} for account discovery")
                result = await read_financial_plan(ctx, reference_entity_key, version_key)
                logger.info("Successfully read reference project financial plan")
                return result
            except Exception as ref_error:
                logger.debug(f"Could not read reference project {reference_entity_key}: {ref_error}")
        
        # Fallback to config data (instant, no API call)
        try:
            from ..financial_plan_config import list_available_accounts, list_available_periods
            
            accounts = list_available_accounts()
            periods = list_available_periods()
            
            if accounts or periods:
                logger.info("Returning config-based financial plan info (fast path)")
                # Return a structure similar to read_financial_plan for compatibility
                return {
                    "success": True,
                    "data": {
                        "EntityKey": entity_key,
                        "VersionKey": version_key,
                        "Accounts": accounts,  # Config accounts
                        "Periods": periods,    # Config periods
                        "Source": "config",    # Indicate this is from config, not API read
                    },
                    "warnings": [],
                }
        except Exception as config_error:
            logger.debug(f"Could not get config data: {config_error}")
        
        logger.info(
            f"Could not discover financial plan info for {entity_key}. "
            f"Use known account/period keys or configure defaults."
        )
        return None
    
    # Standard path: Try reading the target project first
    try:
        result = await read_financial_plan(ctx, entity_key, version_key)
        logger.info(f"Successfully read financial plan for {entity_key}")
        return result
    except Exception as e:
        logger.debug(f"Could not read financial plan for {entity_key}: {e}")
        
        # If target project has no plan yet, try reference project
        if reference_entity_key:
            try:
                logger.info(
                    f"Falling back to reference project {reference_entity_key} "
                    f"for account discovery"
                )
                result = await read_financial_plan(ctx, reference_entity_key, version_key)
                logger.info(f"Successfully read reference project financial plan")
                return result
            except Exception as ref_error:
                logger.debug(
                    f"Could not read reference project {reference_entity_key}: {ref_error}"
                )
        
        # Final fallback: Return config data (instant, no API call)
        try:
            from ..financial_plan_config import list_available_accounts, list_available_periods
            
            accounts = list_available_accounts()
            periods = list_available_periods()
            
            if accounts or periods:
                logger.info("Returning config-based financial plan info (fallback)")
                return {
                    "success": True,
                    "data": {
                        "EntityKey": entity_key,
                        "VersionKey": version_key,
                        "Accounts": accounts,
                        "Periods": periods,
                        "Source": "config",
                    },
                    "warnings": [],
                }
        except Exception as config_error:
            logger.debug(f"Could not get config data: {config_error}")
        
        logger.info(
            f"Could not discover financial plan info for {entity_key}. "
            f"Use known account/period keys or configure defaults."
        )
        return None


async def read_financial_plan(
    ctx: Context,
    entity_key: str,
    version_key: str,
) -> dict[str, Any]:
    """Read a financial plan for a project using SOAP FinancialPlanService.

    This tool reads the financial plan structure including all account lines,
    entries, and periods. Use this to discover available accounts before
    adding new lines with upsert_financial_plan.

    Args:
        ctx: FastMCP context
        entity_key: Project entity key (e.g., "key://2/$Plan/17288")
        version_key: Financial plan version key (e.g., "key://14/1" for Actual/Forecast)

    Returns:
        Dict with financial plan data including:
        - EntityKey: Project entity key
        - VersionKey: Version key
        - Lines: Array of FinancialPlanLineDto objects with account details
        - ModelDescription: Financial model name
        - VersionDescription: Version name

    Raises:
        PlanviewValidationError: If entity_key or version_key is invalid
        PlanviewNotFoundError: If financial plan is not found
        PlanviewAuthError: If authentication fails
        PlanviewError: For other errors

    Example:
        # Read financial plan for project 17288, Actual/Forecast version
        result = await read_financial_plan(
            ctx,
            entity_key="key://2/$Plan/17288",
            version_key="key://14/1"
        )
        
        # Extract available accounts
        lines = result.get("data", {}).get("Lines", {}).get("FinancialPlanLineDto", [])
        accounts = {}
        for line in lines:
            account_key = line.get("AccountKey")
            if account_key:
                accounts[account_key] = {
                    "description": line.get("AccountDescription"),
                    "parent": line.get("AccountParentDescription"),
                    "unit": line.get("Unit"),
                }
    """
    start_time = time()
    logger.info(
        "Reading financial plan",
        extra={
            "tool_name": "read_financial_plan",
            "entity_key": entity_key,
            "version_key": version_key,
        },
    )

    try:
        # Validate inputs with better error context
        if not entity_key or not isinstance(entity_key, str):
            raise PlanviewValidationError(
                f"entity_key is required and must be a string. "
                f"Got: {type(entity_key).__name__} = {entity_key}"
            )
        if not version_key or not isinstance(version_key, str):
            raise PlanviewValidationError(
                f"version_key is required and must be a string. "
                f"Got: {type(version_key).__name__} = {version_key}"
            )

        financial_plan_service_path = "/planview/services/FinancialPlanService.svc"

        async with get_soap_client_for_service(financial_plan_service_path) as client:
            # Get the service
            try:
                service = client.bind(
                    FINANCIAL_PLAN_SERVICE_NAME,
                    port_name=FINANCIAL_PLAN_SERVICE_PORT,
                )
            except (AttributeError, ValueError, KeyError, TypeError):
                service = client.service

            # Get the Read operation
            read_op = getattr(service, "Read")

            # Get DTO factories
            financial_plan_dto_factory = client.get_type(
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanDto/2013/03}FinancialPlanDto"
            )
            array_of_financial_plan_dto_factory = client.get_type(
                "{http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanDto/2013/03}ArrayOfFinancialPlanDto"
            )

            # Create the DTO object with EntityKey and VersionKey
            read_dto_obj = financial_plan_dto_factory(
                EntityKey=entity_key, VersionKey=version_key
            )

            logger.info(
                f"Calling Read operation for EntityKey={entity_key}, VersionKey={version_key}"
            )

            # Wrap in ArrayOfFinancialPlanDto and call Read
            plan_array = array_of_financial_plan_dto_factory([read_dto_obj])
            result = await asyncio.to_thread(read_op, dtos=plan_array)

            logger.info("✅ Financial plan read succeeded!")

            # Handle the result
            processed_result = _handle_soap_result(result)

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully read financial plan",
                extra={
                    "tool_name": "read_financial_plan",
                    "entity_key": entity_key,
                    "version_key": version_key,
                    "duration_ms": duration_ms,
                },
            )

            return processed_result

    except (PlanviewValidationError, PlanviewNotFoundError) as e:
        # Enhance error messages with actionable guidance for common cases
        error_msg = str(e)
        duration_ms = int((time() - start_time) * 1000)
        
        if "Unable to find the requested Financial Plan" in error_msg or "not found" in error_msg.lower():
            # Extract structure code from entity_key if possible
            structure_code = "unknown"
            if "/$Plan/" in entity_key:
                try:
                    structure_code = entity_key.split("/$Plan/")[1].split(":")[0]
                except Exception:
                    pass
            
            guidance = (
                f"\n\nGuidance: The financial plan doesn't exist yet for project {structure_code}. "
                f"This is normal for newly created projects.\n\n"
                f"Options to proceed:\n"
                f"1. Use 'discover_financial_plan_info()' with a reference project "
                f"(e.g., structure code 3818) to discover valid account and period keys, "
                f"then use those keys in 'upsert_financial_plan()'\n"
                f"2. Use 'upsert_financial_plan()' directly - it will create the financial plan "
                f"if it doesn't exist (provided you use valid account/period keys from the model)\n"
                f"3. Wait a moment after project creation - some systems need time to initialize "
                f"the financial plan infrastructure"
            )
            
            raise PlanviewNotFoundError(error_msg + guidance) from e
        
        # Re-raise other validation/not-found errors with original message
        logger.error(
            f"Failed to read financial plan: {error_msg}",
            extra={
                "tool_name": "read_financial_plan",
                "entity_key": entity_key,
                "version_key": version_key,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise
        
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        
        # Add context to error message
        error_context = (
            f"Failed to read financial plan for EntityKey={entity_key}, "
            f"VersionKey={version_key}. "
        )
        
        error_msg = str(e)
        if "structure code" in error_msg.lower():
            error_context += (
                "The EntityKey appears invalid. Verify the structure code is correct. "
                f"Expected format: key://2/$Plan/<structure_code>"
            )
        
        logger.error(
            error_context + f" Error: {error_msg}",
            extra={
                "tool_name": "read_financial_plan",
                "entity_key": entity_key,
                "version_key": version_key,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise

