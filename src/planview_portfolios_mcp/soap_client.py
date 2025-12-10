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
            base_url = settings.planview_api_url.rstrip("/")
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

            # Create transport with pre-configured session
            transport = Transport(session=session, timeout=settings.soap_timeout)

            # Create zeep client settings
            zeep_settings = Settings(
                strict=False,  # Allow extra fields
                xml_huge_tree=True,  # Handle large XML responses
            )

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
        yield client
    except TransportError as e:
        if "401" in str(e) or "403" in str(e):
            raise PlanviewAuthError(f"SOAP authentication failed: {str(e)}") from e
        elif "404" in str(e):
            raise PlanviewNotFoundError(f"SOAP service not found: {str(e)}") from e
        else:
            raise PlanviewConnectionError(f"SOAP transport error: {str(e)}") from e
    except Exception as e:
        raise PlanviewConnectionError(f"Failed to create SOAP client: {str(e)}") from e


async def close_soap_client():
    """Close shared SOAP client (call on shutdown)."""
    await _soap_client.close()


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
    if hasattr(result, "Successes") and result.Successes:
        for success in result.Successes:
            success_dict = {
                "source_index": getattr(success, "SourceIndex", None),
                "code": getattr(success, "Code", None),
                "error_message": getattr(success, "ErrorMessage", None),
            }
            # Extract DTO from success (contains keys only on success)
            if hasattr(success, "Dto"):
                dto = success.Dto
                # Convert DTO to dict
                dto_dict = {}
                if dto:
                    for attr in dir(dto):
                        if not attr.startswith("_") and not callable(getattr(dto, attr)):
                            value = getattr(dto, attr, None)
                            if value is not None:
                                dto_dict[attr] = value
                success_dict["dto"] = dto_dict
            parsed["successes"].append(success_dict)

    # Parse failures
    if hasattr(result, "Failures") and result.Failures:
        for failure in result.Failures:
            failure_dict = {
                "source_index": getattr(failure, "SourceIndex", None),
                "code": getattr(failure, "Code", None),
                "error_message": getattr(failure, "ErrorMessage", None),
            }
            # Extract DTO from failure (contains full DTO on failure)
            if hasattr(failure, "Dto"):
                dto = failure.Dto
                dto_dict = {}
                if dto:
                    for attr in dir(dto):
                        if not attr.startswith("_") and not callable(getattr(dto, attr)):
                            value = getattr(dto, attr, None)
                            if value is not None:
                                dto_dict[attr] = value
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
                dto_dict = {}
                if dto:
                    for attr in dir(dto):
                        if not attr.startswith("_") and not callable(getattr(dto, attr)):
                            value = getattr(dto, attr, None)
                            if value is not None:
                                dto_dict[attr] = value
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
                key = dto.get("Key", "unknown")
                description = dto.get("Description", "")
                msg = f"{msg} (Key: {key}, Description: {description})"
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
        service = client.bind(service_name)
        # Get the operation
        operation = getattr(service, operation_name)

        # Call the operation
        # zeep operations are synchronous, so we run them in a thread pool to avoid blocking
        logger.debug(
            f"Calling SOAP operation {service_name}.{operation_name} with args={args}, kwargs={kwargs}"
        )
        result = await asyncio.to_thread(operation, *args, **kwargs)

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
