"""OAuth secured ping tool."""

import logging
from time import time
from typing import Any

from fastmcp import Context

from ..client import get_client, make_request

logger = logging.getLogger(__name__)


async def oauth_ping(ctx: Context) -> Any:
    """Call secured ping to verify credentials."""
    start_time = time()
    logger.info("Calling OAuth ping", extra={"tool_name": "oauth_ping"})

    try:
        async with get_client() as client:
            response = await make_request(
                client, "GET", "/public-api/v1/oauth/ping"
            )
            data = response.json()

            duration_ms = int((time() - start_time) * 1000)
            logger.info(
                "OAuth ping success",
                extra={"tool_name": "oauth_ping", "duration_ms": duration_ms},
            )
            return data
    except Exception as e:
        duration_ms = int((time() - start_time) * 1000)
        logger.error(
            f"OAuth ping failed: {str(e)}",
            extra={
                "tool_name": "oauth_ping",
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise

