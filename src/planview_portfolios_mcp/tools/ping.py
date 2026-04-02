"""OAuth secured ping tool."""

import json
import logging
from time import time
from typing import Any

from ..client import get_client, make_request
from ..exceptions import PlanviewError
from ..performance import log_performance

logger = logging.getLogger(__name__)


@log_performance
async def oauth_ping() -> Any:
    """[LOCAL — auth health check for this server's connection.]

    Call secured ping to verify credentials."""
    start_time = time()
    logger.info("Calling OAuth ping", extra={"tool_name": "oauth_ping"})

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/oauth/ping"
            )
            
            # Handle different response types (text/plain or application/json)
            content_type = response.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                data = response.json()
            else:
                # Handle text/plain response (should be "pong")
                text = response.text.strip()
                data = {"message": text} if text else {"status": "success"}

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "OAuth ping success",
                extra={"tool_name": "oauth_ping", "duration_ms": duration_ms},
            )
            return data
    except (PlanviewError, json.JSONDecodeError, UnicodeDecodeError) as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "OAuth ping failed",
            extra={
                "tool_name": "oauth_ping",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.exception(
            "OAuth ping failed (unexpected error)",
            extra={
                "tool_name": "oauth_ping",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
        )
        raise

