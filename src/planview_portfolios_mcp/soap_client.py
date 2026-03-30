"""SOAP client for Planview Portfolios SOAP web services."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from zeep import Client, Settings
from zeep.exceptions import Fault, TransportError
from zeep.transports import Transport

from .config import settings
from .exceptions import (
    PlanviewAuthError,
    PlanviewConnectionError,
    PlanviewError,
    PlanviewNotFoundError,
    PlanviewServerError,
    PlanviewTimeoutError,
    PlanviewValidationError,
)

from .oauth import get_oauth_token

logger = logging.getLogger(__name__)


class PlanviewSOAPClient:
    """Manages SOAP client lifecycle with connection pooling and OAuth authentication."""

    def __init__(self):
        self._client: Client | None = None
        self._wsdl_url: str | None = None

    def _get_wsdl_url(self) -> str:
        """Get WSDL URL for TaskService."""
        if self._wsdl_url is None:
            # Remove /polaris from base URL if present (SOAP services are at /planview, not /polaris)
            base_url = settings.planview_api_url.rstrip("/")
            if base_url.endswith("/polaris"):
                base_url = base_url[:-7]  # Remove "/polaris"
            service_path = settings.soap_service_path.lstrip("/")
            self._wsdl_url = f"{base_url}/{service_path}?wsdl"
        return self._wsdl_url

    async def _get_client(self) -> Client:
        """Get or create SOAP client with OAuth authentication."""
        if self._client is None:
            # Get OAuth token
            if not settings.planview_client_id or not settings.planview_client_secret:
                raise PlanviewAuthError(
                    "OAuth credentials are required (PLANVIEW_CLIENT_ID/PLANVIEW_CLIENT_SECRET)."
                )

            token = await get_oauth_token()
            auth_header = f"Bearer {token}"

            # Create requests.Session with auth headers
            # zeep's Transport uses requests by default
            session = requests.Session()
            session.headers.update(
                {
                    "Authorization": auth_header,
                    "X-Tenant-Id": settings.planview_tenant_id,
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": "",
                }
            )

            # Use MCP timeout if set, else soap_timeout (fail-fast on slow SOAP)
            soap_timeout_sec = getattr(settings, "mcp_soap_timeout_seconds", None) or settings.soap_timeout
            transport = Transport(session=session, timeout=soap_timeout_sec)

            # Create zeep client settings
            zeep_settings = Settings(
                strict=False,  # Allow extra fields
                xml_huge_tree=True,  # Handle large XML responses
            )
            
            # Only enable zeep debug logging if log level is DEBUG
            import logging
            if settings.log_level == "DEBUG":
                zeep_logger = logging.getLogger('zeep.wsdl')
                zeep_logger.setLevel(logging.DEBUG)
                zeep_transport_logger = logging.getLogger('zeep.transports')
                zeep_transport_logger.setLevel(logging.DEBUG)

            wsdl_url = self._get_wsdl_url()
            logger.debug(f"Creating SOAP client for WSDL: {wsdl_url}")

            # Create client (synchronous operation)
            self._client = Client(
                wsdl=wsdl_url,
                transport=transport,
                settings=zeep_settings,
            )

        else:
            # Refresh token if needed (tokens expire in 60 minutes)
            # Update headers on existing client's transport session
            token = await get_oauth_token()
            auth_header = f"Bearer {token}"
            if (
                hasattr(self._client, "transport")
                and hasattr(self._client.transport, "session")
            ):
                session = self._client.transport.session
                if isinstance(session, requests.Session):
                    session.headers.update(
                        {
                            "Authorization": auth_header,
                            "X-Tenant-Id": settings.planview_tenant_id,
                        }
                    )

        return self._client

    async def close(self):
        """Close SOAP client (call on server shutdown)."""
        if self._client and hasattr(self._client, "transport"):
            transport = self._client.transport
            if hasattr(transport, "session"):
                session = transport.session
                if isinstance(session, requests.Session):
                    session.close()
            self._client = None


# Global SOAP client instance
_soap_client = PlanviewSOAPClient()


@asynccontextmanager
async def get_soap_client() -> AsyncContextManager[Client]:
    """Get shared SOAP client with OAuth authentication.

    Yields:
        zeep Client instance configured for TaskService3

    Raises:
        PlanviewAuthError: If OAuth credentials are missing or invalid
        PlanviewConnectionError: If WSDL cannot be loaded
    """
    try:
        client = await _soap_client._get_client()
    except PlanviewAuthError:
        raise
    except TransportError as e:
        if "401" in str(e) or "403" in str(e):
            raise PlanviewAuthError(f"SOAP authentication failed: {str(e)}") from e
        elif "404" in str(e):
            raise PlanviewNotFoundError(f"SOAP service not found: {str(e)}") from e
        else:
            raise PlanviewConnectionError(f"SOAP transport error: {str(e)}") from e
    except Exception as e:
        raise PlanviewConnectionError(f"Failed to create SOAP client: {str(e)}") from e

    try:
        yield client
    except TransportError as e:
        if "401" in str(e) or "403" in str(e):
            raise PlanviewAuthError(f"SOAP authentication failed: {str(e)}") from e
        elif "404" in str(e):
            raise PlanviewNotFoundError(f"SOAP service not found: {str(e)}") from e
        else:
            raise PlanviewConnectionError(f"SOAP transport error: {str(e)}") from e


async def close_soap_client():
    """Close shared SOAP client (call on shutdown)."""
    await _soap_client.close()
    _close_cached_service_clients()


# Cache for per-service SOAP clients (avoid re-fetching WSDL every call)
_service_client_cache: dict[str, Client] = {}
_service_client_lock = asyncio.Lock()


def _close_cached_service_clients() -> None:
    """Close all cached per-service clients (call on shutdown)."""
    global _service_client_cache
    for path, client in list(_service_client_cache.items()):
        try:
            if hasattr(client, "transport") and hasattr(client.transport, "session"):
                session = client.transport.session
                if isinstance(session, requests.Session):
                    session.close()
        except Exception:
            pass
    _service_client_cache.clear()


@asynccontextmanager
async def get_soap_client_for_service(service_path: str) -> AsyncContextManager[Client]:
    """Get SOAP client for a specific service path (cached per path).
    
    First call for a given path fetches WSDL and creates the client; subsequent
    calls reuse the cached client so discover + upsert don't each pay ~15s.
    
    Args:
        service_path: Service path (e.g., "/planview/services/FinancialPlanService.svc")
        
    Yields:
        zeep Client instance for the specified service
    """
    path_key = (service_path or "").strip().rstrip("/") or "/"
    async with _service_client_lock:
        client = _service_client_cache.get(path_key)
        if client is not None:
            # Refresh auth header on cached client
            try:
                token = await get_oauth_token()
                auth_header = f"Bearer {token}"
                if (
                    hasattr(client, "transport")
                    and hasattr(client.transport, "session")
                    and isinstance(client.transport.session, requests.Session)
                ):
                    client.transport.session.headers.update(
                        {"Authorization": auth_header, "X-Tenant-Id": settings.planview_tenant_id}
                    )
            except Exception:
                pass
            yield client
            return

    # Cache miss: create and cache
    if not settings.planview_client_id or not settings.planview_client_secret:
        raise PlanviewAuthError(
            "OAuth credentials are required (PLANVIEW_CLIENT_ID/PLANVIEW_CLIENT_SECRET)."
        )
    token = await get_oauth_token()
    auth_header = f"Bearer {token}"
    base_url = settings.planview_api_url.rstrip("/")
    if base_url.endswith("/polaris"):
        base_url = base_url[:-7]
    service_path_clean = (service_path or "").strip().lstrip("/")
    wsdl_url = f"{base_url}/{service_path_clean}?wsdl"
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": auth_header,
            "X-Tenant-Id": settings.planview_tenant_id,
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "",
        }
    )
    soap_timeout_sec = getattr(settings, "mcp_soap_timeout_seconds", None) or settings.soap_timeout
    transport = Transport(session=session, timeout=soap_timeout_sec)
    zeep_settings = Settings(strict=False, xml_huge_tree=True)
    logger.debug(f"Creating SOAP client for WSDL: {wsdl_url}")
    try:
        new_client = Client(wsdl=wsdl_url, transport=transport, settings=zeep_settings)
    except TransportError as e:
        if "401" in str(e) or "403" in str(e):
            raise PlanviewAuthError(f"SOAP authentication failed: {str(e)}") from e
        if "404" in str(e):
            raise PlanviewNotFoundError(f"SOAP service not found: {str(e)}") from e
        raise PlanviewConnectionError(f"SOAP transport error: {str(e)}") from e
    except Exception as e:
        raise PlanviewConnectionError(f"Failed to create SOAP client: {str(e)}") from e
    async with _service_client_lock:
        _service_client_cache[path_key] = new_client
    try:
        yield new_client
    except Exception:
        # On error, don't evict cache - next call can retry with same client
        raise


def _convert_zeep_object_to_dict(obj: Any) -> dict[str, Any]:
    """Recursively convert zeep object to dict, handling nested structures."""
    if obj is None:
        return {}
    
    result_dict = {}
    
    # Handle dict-like objects
    if hasattr(obj, "__dict__"):
        obj_dict = obj.__dict__
        if "__values__" in obj_dict:
            # zeep objects store values in __values__
            obj_dict = obj_dict["__values__"]
        
        for key, value in obj_dict.items():
            if key.startswith("_"):
                continue
            result_dict[key] = _convert_zeep_value_to_python(value)
    
    # Also try dir() approach for zeep objects
    if not result_dict:
        for attr in dir(obj):
            if attr.startswith("_") or callable(getattr(obj, attr)):
                continue
            try:
                value = getattr(obj, attr, None)
                if value is not None:
                    result_dict[attr] = _convert_zeep_value_to_python(value)
            except Exception:
                pass
    
    return result_dict


def _convert_zeep_value_to_python(value: Any) -> Any:
    """Convert zeep value to native Python type, handling nested structures."""
    if value is None:
        return None
    
    # Handle zeep objects
    if hasattr(value, "__dict__") or (hasattr(value, "__class__") and "zeep" in str(type(value))):
        return _convert_zeep_object_to_dict(value)
    
    # Handle lists/arrays
    if isinstance(value, (list, tuple)):
        return [_convert_zeep_value_to_python(item) for item in value]
    
    # Handle dicts
    if isinstance(value, dict):
        return {k: _convert_zeep_value_to_python(v) for k, v in value.items()}
    
    # Return primitive values as-is
    return value


def _parse_opensuite_result(result: Any) -> dict[str, Any]:
    """Parse OpenSuiteResult from SOAP response to dict format.

    Args:
        result: OpenSuiteResult object from zeep

    Returns:
        Dict with successes, failures, warnings, and general_error_message
    """
    parsed = {
        "successes": [],
        "failures": [],
        "warnings": [],
        "general_error_message": getattr(result, "GeneralErrorMessage", None),
    }

    # Parse successes
    # Successes can be a dict with "OpenSuiteStatus" key or a direct list/iterable
    if hasattr(result, "Successes") and result.Successes:
        successes_to_process = []
        
        # Handle nested structure: Successes may contain OpenSuiteStatus
        if hasattr(result.Successes, "OpenSuiteStatus"):
            successes_to_process = result.Successes.OpenSuiteStatus
            if not isinstance(successes_to_process, list):
                successes_to_process = [successes_to_process]
        elif hasattr(result.Successes, "__iter__") and not isinstance(result.Successes, (str, bytes)):
            # Direct iterable
            successes_to_process = list(result.Successes)
        else:
            successes_to_process = [result.Successes]
        
        for success in successes_to_process:
            success_dict = {
                "source_index": getattr(success, "SourceIndex", None),
                "code": getattr(success, "Code", None),
                "error_message": getattr(success, "ErrorMessage", None),
            }
            # Extract DTO from success (contains full DTO on read operations)
            if hasattr(success, "Dto"):
                dto = success.Dto
                # Convert DTO to dict recursively
                dto_dict = _convert_zeep_object_to_dict(dto)
                success_dict["dto"] = dto_dict
            parsed["successes"].append(success_dict)

    # Parse failures
    # Failures can be a dict with "OpenSuiteStatus" key or a direct list/iterable
    if hasattr(result, "Failures") and result.Failures:
        failures_to_process = []
        
        # Handle nested structure: Failures may contain OpenSuiteStatus
        if hasattr(result.Failures, "OpenSuiteStatus"):
            failures_to_process = result.Failures.OpenSuiteStatus
            if not isinstance(failures_to_process, list):
                failures_to_process = [failures_to_process]
        elif hasattr(result.Failures, "__iter__") and not isinstance(result.Failures, (str, bytes)):
            # Direct iterable
            failures_to_process = list(result.Failures)
        else:
            failures_to_process = [result.Failures]
        
        for failure in failures_to_process:
            failure_dict = {
                "source_index": getattr(failure, "SourceIndex", None),
                "code": getattr(failure, "Code", None),
                "error_message": getattr(failure, "ErrorMessage", None),
            }
            # Extract DTO from failure (contains full DTO on failure)
            if hasattr(failure, "Dto"):
                dto = failure.Dto
                dto_dict = _convert_zeep_object_to_dict(dto)
                failure_dict["dto"] = dto_dict
            parsed["failures"].append(failure_dict)

    # Parse warnings
    if hasattr(result, "Warnings") and result.Warnings:
        for warning in result.Warnings:
            warning_dict = {
                "source_index": getattr(warning, "SourceIndex", None),
                "code": getattr(warning, "Code", None),
                "error_message": getattr(warning, "ErrorMessage", None),
            }
            if hasattr(warning, "Dto"):
                dto = warning.Dto
                dto_dict = _convert_zeep_object_to_dict(dto)
                warning_dict["dto"] = dto_dict
            parsed["warnings"].append(warning_dict)

    return parsed


def _handle_soap_result(result: Any) -> dict[str, Any]:
    """Handle SOAP operation result and convert to consistent format.

    Args:
        result: OpenSuiteResult from SOAP operation

    Returns:
        Dict with operation results

    Raises:
        PlanviewValidationError: If operation has failures
        PlanviewError: For other errors
    """
    parsed = _parse_opensuite_result(result)

    # Check for general error
    if parsed["general_error_message"]:
        raise PlanviewServerError(
            f"SOAP operation failed: {parsed['general_error_message']}"
        )

    # Check for failures
    if parsed["failures"]:
        error_messages = []
        for failure in parsed["failures"]:
            msg = failure.get("error_message") or "Unknown error"
            if failure.get("dto"):
                # Include DTO info in error
                dto = failure["dto"]
                key = dto.get("Key") or dto.get("EntityKey", "unknown")
                description = dto.get("Description") or dto.get("EntityDescription", "")
                if description:
                    msg = f"{msg} (EntityKey: {key}, Description: {description})"
                else:
                    msg = f"{msg} (EntityKey: {key})"
            error_messages.append(msg)

        raise PlanviewValidationError(
            f"SOAP operation failed: {'; '.join(error_messages)}"
        )

    # Return successes
    if parsed["successes"]:
        # For single operations, return the first success
        success = parsed["successes"][0]
        return {
            "success": True,
            "data": success.get("dto", {}),
            "warnings": parsed["warnings"],
        }

    # No successes, failures, or errors - return empty result
    return {"success": True, "data": {}, "warnings": parsed["warnings"]}


def create_retry_decorator():
    """Create retry decorator for SOAP operations."""
    return retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (
                TransportError,
                PlanviewServerError,
                PlanviewConnectionError,
            )
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


@create_retry_decorator()
async def make_soap_request(
    client: Client,
    service_name: str,
    operation_name: str,
    port_name: str | None = None,
    *args,
    **kwargs,
) -> dict[str, Any]:
    """Make SOAP request with automatic retry and error handling.

    Args:
        client: zeep Client instance
        service_name: Name of the service (e.g., "ITaskService3")
        operation_name: Name of the operation (e.g., "Create", "Read")
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        Parsed result dict

    Raises:
        PlanviewAuthError: Authentication failure
        PlanviewNotFoundError: Resource not found
        PlanviewValidationError: Invalid request
        PlanviewServerError: Server error
        PlanviewTimeoutError: Request timeout
        PlanviewConnectionError: Network connection failure
    """
    try:
        # Get the service binding
        # zeep's bind() method signature: bind(service_name, port_name=None)
        # For TaskService, try binding with service name first
        try:
            if port_name:
                service = client.bind(service_name, port_name=port_name)
            else:
                service = client.bind(service_name)
        except (AttributeError, ValueError, KeyError, TypeError) as bind_error:
            # If explicit binding fails, try using client.service (default service)
            logger.debug(
                f"Binding with {service_name} port {port_name} failed: {bind_error}, trying client.service"
            )
            if hasattr(client, 'service'):
                service = client.service
            else:
                # Last resort: try to get service from WSDL
                raise PlanviewConnectionError(
                    f"Could not bind to service {service_name}. Available services: {list(client.wsdl.services.keys()) if hasattr(client, 'wsdl') else 'unknown'}"
                ) from bind_error
        
        # Get the operation
        operation = getattr(service, operation_name)

        # Remove binding-only kwargs so they aren’t passed to the operation
        kwargs.pop("port_name", None)
        
        # Log operation signature for debugging
        if hasattr(operation, '_signature'):
            logger.debug(f"Operation signature: {operation._signature}")

        # Call the operation
        # zeep operations are synchronous, so we run them in a thread pool to avoid blocking
        logger.debug(
            f"Calling SOAP operation {service_name}.{operation_name} with args={args}, kwargs={kwargs}"
        )
        try:
            result = await asyncio.to_thread(operation, *args, **kwargs)
        except TypeError as e:
            # If we get a TypeError, it might be a signature mismatch
            # Log the operation signature for debugging
            if hasattr(operation, '_signature'):
                logger.error(f"Operation signature: {operation._signature}")
            raise

        # Handle the result
        return _handle_soap_result(result)

    except Fault as e:
        # SOAP fault - check error code
        fault_code = getattr(e, "code", None) or str(e)
        fault_message = getattr(e, "message", None) or str(e)

        logger.error(f"SOAP fault: {fault_code} - {fault_message}")

        if "401" in fault_code or "Unauthorized" in fault_message:
            raise PlanviewAuthError(f"SOAP authentication failed: {fault_message}") from e
        elif "404" in fault_code or "Not Found" in fault_message:
            raise PlanviewNotFoundError(f"SOAP resource not found: {fault_message}") from e
        elif "400" in fault_code or "Bad Request" in fault_message:
            raise PlanviewValidationError(f"SOAP invalid request: {fault_message}") from e
        else:
            raise PlanviewServerError(f"SOAP fault ({fault_code}): {fault_message}") from e

    except TransportError as e:
        # Transport/network error
        error_msg = str(e)
        logger.error(f"SOAP transport error: {error_msg}")

        if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            raise PlanviewTimeoutError(
                f"SOAP request timed out after {settings.soap_timeout}s: {error_msg}"
            ) from e
        elif "401" in error_msg or "403" in error_msg:
            raise PlanviewAuthError(f"SOAP authentication failed: {error_msg}") from e
        elif "404" in error_msg:
            raise PlanviewNotFoundError(f"SOAP service not found: {error_msg}") from e
        else:
            raise PlanviewConnectionError(f"SOAP transport error: {error_msg}") from e

    except Exception as e:
        logger.error(f"Unexpected SOAP error: {str(e)}", exc_info=True)
        raise PlanviewError(f"Unexpected SOAP error: {str(e)}") from e
