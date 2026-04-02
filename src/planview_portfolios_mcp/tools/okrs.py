"""OKRs (Objectives and Key Results) tools for Planview Portfolios."""

import json
import logging
from contextlib import asynccontextmanager
from time import time
from typing import Any

import httpx
from ..client import make_request
from ..config import settings
from ..exceptions import PlanviewAuthError, PlanviewError, PlanviewValidationError
from ..oauth import get_okr_oauth_token
from ..performance import log_performance

logger = logging.getLogger(__name__)


def _get_okr_base_url() -> str:
    """Get the OKR API base URL.
    
    The OKRs API uses a different base URL than the Portfolios API.
    Defaults to https://api-us.okrs.planview.com/api/rest/ or uses
    planview_okr_api_url if configured.
    """
    if settings.planview_okr_api_url:
        return settings.planview_okr_api_url.rstrip("/")
    
    # Default OKR API URL (REST API)
    return "https://api-us.okrs.planview.com/api/rest"


@asynccontextmanager
async def _get_okr_client():
    """Get an HTTP client configured for OKRs API.
    
    Automatically uses OAuth token refresh if PLANVIEW_OKR_CLIENT_ID and
    PLANVIEW_OKR_CLIENT_SECRET are configured. Otherwise, falls back to
    static PLANVIEW_OKR_BEARER_TOKEN if provided.
    
    Prefers OAuth credentials over static bearer token for automatic refresh.
    """
    okr_base_url = _get_okr_base_url()
    
    # Try OAuth credentials first (automatic refresh)
    okr_token = None
    has_client_id = bool(settings.planview_okr_client_id)
    has_client_secret = bool(settings.planview_okr_client_secret)
    
    if has_client_id and has_client_secret:
        try:
            okr_token = await get_okr_oauth_token()
            logger.debug("Using OKR OAuth token (auto-refreshing)")
        except (PlanviewAuthError, PlanviewError, httpx.RequestError, httpx.TimeoutException) as e:
            logger.warning(
                "Failed to get OKR OAuth token: %s. Falling back to static bearer token.",
                e,
                exc_info=True,
            )
    
    # Fallback to static bearer token if OAuth failed or not configured
    if not okr_token:
        okr_token = settings.planview_okr_bearer_token
    
    if not okr_token:
        # Provide detailed error message about what's missing
        missing_parts = []
        if not has_client_id:
            missing_parts.append("PLANVIEW_OKR_CLIENT_ID")
        if not has_client_secret:
            missing_parts.append("PLANVIEW_OKR_CLIENT_SECRET")
        if not settings.planview_okr_bearer_token:
            missing_parts.append("PLANVIEW_OKR_BEARER_TOKEN")
        
        error_msg = (
            "OKRs API authentication required. "
            f"Missing: {', '.join(missing_parts)}. "
            "Please set PLANVIEW_OKR_CLIENT_ID and PLANVIEW_OKR_CLIENT_SECRET "
            "(recommended for auto-refresh) or PLANVIEW_OKR_BEARER_TOKEN "
            "in your Claude Desktop config JSON file under the 'env' section, "
            "or in a .env file, or as environment variables."
        )
        raise PlanviewValidationError(error_msg)
    
    auth_header = f"Bearer {okr_token}"
    
    client = httpx.AsyncClient(
        base_url=okr_base_url,
        timeout=settings.api_timeout,
        headers={
            "Authorization": auth_header,
        },
    )
    
    try:
        yield client
    finally:
        await client.aclose()


@log_performance
async def list_objectives(
    ids: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    """[LOCAL — OKR objectives list. No Beta MCP equivalent exists for OKRs.]
    
    List all objectives from the OKRs API.
    
    Args:
        ids: Optional comma-separated list of objective IDs to filter by
        limit: Number of results to return (default: 10, max: 500)
        offset: Offset for pagination (default: 0)
        
    Returns:
        Dict with objectives list and total_records count
        
    Example:
        {
            "fetch_objectives": {
                "total_records": 1100,
                "objectives": [...]
            }
        }
    """
    start_time = time()
    logger.info(
        "Listing objectives",
        extra={
            "tool_name": "list_objectives",
            "ids": ids,
            "limit": limit,
            "offset": offset,
        },
    )
    
    # Validate limit
    if limit < 1 or limit > 500:
        raise PlanviewValidationError("limit must be between 1 and 500")
    if offset < 0:
        raise PlanviewValidationError("offset must be >= 0")
    
    params: dict[str, Any] = {
        "limit": limit,
        "offset": offset,
    }
    
    if ids:
        params["ids"] = ids
    
    try:
        async with _get_okr_client() as client:
            # OKRs API endpoint is /v1/objectives (base URL already includes /api/rest)
            # This is a Hasura REST endpoint that wraps the GraphQL fetch_objectives query
            # Hasura automatically converts query parameters to GraphQL variables
            response = await make_request(
                client, "GET", "/v1/objectives", params=params
            )
            
            # Handle both JSON and text responses
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                # If response is text, try to parse as JSON
                text = response.text
                try:
                    data = response.json()
                except (json.JSONDecodeError, UnicodeDecodeError) as parse_err:
                    logger.debug(
                        "OKR list_objectives: response body is not JSON: %s: %s",
                        type(parse_err).__name__,
                        parse_err,
                    )
                    # If it's not JSON, return the text in a structured format
                    data = {"error": text}
            
            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully listed objectives",
                extra={
                    "tool_name": "list_objectives",
                    "duration_ms": duration_ms,
                    "total_records": data.get("fetch_objectives", {}).get("total_records", 0),
                },
            )
            return data
            
    except (PlanviewError, json.JSONDecodeError, httpx.HTTPError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to list objectives",
            extra={
                "tool_name": "list_objectives",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to list objectives (unexpected error)",
            extra={
                "tool_name": "list_objectives",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


@log_performance
async def get_key_results_for_objective(
    objective_id: int,
) -> dict[str, Any]:
    """[LOCAL — OKR key results for a single objective. No Beta MCP equivalent exists for OKRs.]
    
    Get all key results for a specific objective.
    
    Args:
        objective_id: The ID of the objective
        
    Returns:
        Dict with key_results array
        
    Example:
        {
            "key_results": [
                {
                    "id": 28304,
                    "name": "Increase NPS Score",
                    "objective_id": 17841,
                    ...
                }
            ]
        }
    """
    start_time = time()
    logger.info(
        "Getting key results for objective",
        extra={"tool_name": "get_key_results_for_objective", "objective_id": objective_id},
    )
    
    if not objective_id or objective_id <= 0:
        raise PlanviewValidationError("objective_id must be a positive integer")
    
    try:
        async with _get_okr_client() as client:
            # OKRs API endpoint is /v1/objectives/{id}/key-results (base URL already includes /api/rest)
            # This is a Hasura REST endpoint that wraps the GraphQL KeyResultsByObjectiveId query
            response = await make_request(
                client,
                "GET",
                f"/v1/objectives/{objective_id}/key-results",
            )
            
            # Handle both JSON and text responses
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                # If response is text, try to parse as JSON
                try:
                    data = response.json()
                except (json.JSONDecodeError, UnicodeDecodeError) as parse_err:
                    logger.debug(
                        "OKR get_key_results: response body is not JSON: %s: %s",
                        type(parse_err).__name__,
                        parse_err,
                    )
                    # If it's not JSON, return the text in a structured format
                    data = {"error": response.text}
            
            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "Successfully retrieved key results",
                extra={
                    "tool_name": "get_key_results_for_objective",
                    "objective_id": objective_id,
                    "duration_ms": duration_ms,
                    "key_results_count": len(data.get("key_results", [])),
                },
            )
            return data
            
    except (PlanviewError, json.JSONDecodeError, httpx.HTTPError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to get key results",
            extra={
                "tool_name": "get_key_results_for_objective",
                "objective_id": objective_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "Failed to get key results (unexpected error)",
            extra={
                "tool_name": "get_key_results_for_objective",
                "objective_id": objective_id,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise


@log_performance
async def list_all_objectives_with_key_results(
    limit: int = 500,
    include_key_results: bool = True,
) -> dict[str, Any]:
    """[LOCAL — OKR objectives with key results. No Beta MCP equivalent exists.]
    
    List all objectives with their key results.
    
    This is a convenience function that fetches all objectives and optionally
    includes their key results in the response.
    
    Args:
        limit: Maximum number of objectives per page (default: 500, max: 500)
        include_key_results: If True, fetch key results for each objective (default: True)
        
    Returns:
        Dict with objectives and their key results:
        {
            "total_records": 1100,
            "objectives": [
                {
                    "id": 17841,
                    "name": "Increase customer satisfaction",
                    "key_results": [...],  # Only if include_key_results=True
                    ...
                }
            ]
        }
    """
    start_time = time()
    logger.info(
        "Listing all objectives with key results",
        extra={
            "tool_name": "list_all_objectives_with_key_results",
            "limit": limit,
            "include_key_results": include_key_results,
        },
    )
    
    # Get first page of objectives
    first_page = await list_objectives(limit=limit, offset=0)
    fetch_objectives = first_page.get("fetch_objectives", {})
    total_records = fetch_objectives.get("total_records", 0)
    objectives = fetch_objectives.get("objectives", [])
    
    # Handle pagination if needed
    if total_records > limit:
        # Fetch remaining pages
        remaining_pages = []
        current_offset = limit
        while current_offset < total_records:
            page = await list_objectives(limit=limit, offset=current_offset)
            page_objectives = page.get("fetch_objectives", {}).get("objectives", [])
            if not page_objectives:
                break
            remaining_pages.extend(page_objectives)
            current_offset += limit
        
        objectives.extend(remaining_pages)
    
    # Fetch key results for each objective if requested
    if include_key_results:
        logger.info(f"Fetching key results for {len(objectives)} objectives...")
        for objective in objectives:
            objective_id = objective.get("id")
            if objective_id:
                try:
                    key_results_data = await get_key_results_for_objective(objective_id)
                    objective["key_results"] = key_results_data.get("key_results", [])
                except (PlanviewError, json.JSONDecodeError, httpx.HTTPError) as e:
                    logger.warning(
                        "Failed to fetch key results for objective %s: %s",
                        objective_id,
                        e,
                        exc_info=True,
                        extra={"objective_id": objective_id},
                    )
                    # Continue with other objectives even if one fails
                    objective["key_results"] = []
                except Exception:
                    logger.exception(
                        "Unexpected error fetching key results for objective %s",
                        objective_id,
                        extra={"objective_id": objective_id},
                    )
                    objective["key_results"] = []
    
    duration_ms = int((time() - start_time) * 1000)
    logger.info(
        "Successfully listed all objectives with key results",
        extra={
            "tool_name": "list_all_objectives_with_key_results",
            "total_records": total_records,
            "objectives_count": len(objectives),
            "duration_ms": duration_ms,
        },
    )
    
    return {
        "total_records": total_records,
        "objectives": objectives,
    }

