"""Connection diagnostic tool for Planview Portfolios OAuth."""

import logging
from time import time
from typing import Any

from ..exceptions import PlanviewAuthError, PlanviewError
from ..oauth import (
    get_oauth_token_record,
    inspect_oauth_config,
    ping_with_access_token,
)
from ..performance import log_performance

logger = logging.getLogger(__name__)


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


@log_performance
async def test_connection() -> dict[str, Any]:
    """[LOCAL — diagnose this server's Planview OAuth connection.]

    Test the Portfolios OAuth connection with a fresh client_credentials token.

    Runs three checks and always returns a structured result (does not throw on
    auth failure) so the model can self-correct:

    1. Config — API URL shape, client id/secret present, tenant id present.
       Detects a bearer JWT pasted into PLANVIEW_CLIENT_SECRET.
    2. Token — POST /public-api/v1/oauth/token (tries multipart, then form, then JSON).
    3. Ping — GET /public-api/v1/oauth/ping with that same token and X-Tenant-Id.

    A token that succeeds and a ping that returns 401 almost always means
    PLANVIEW_TENANT_ID is wrong or empty — not that the secret is stale.
    """
    start_time = time()
    logger.info("Testing Planview connection", extra={"tool_name": "test_connection"})

    config = inspect_oauth_config()
    checks: list[dict[str, Any]] = list(config["checks"])
    result: dict[str, Any] = {
        "ok": False,
        "connected": False,
        "checks": checks,
        "token_url": config["token_url"],
        "ping_url": config["ping_url"],
        "host": config["host"],
    }

    if not config["ok"]:
        result["error"] = config["error"]
        result["duration_ms"] = int((time() - start_time) * 1000)
        logger.warning(
            "Connection test failed at config",
            extra={"tool_name": "test_connection", "checks": [c["name"] for c in checks if not c["ok"]]},
        )
        return result

    try:
        token = await get_oauth_token_record(force_refresh=True)
    except PlanviewAuthError as e:
        checks.append(_check("token", False, str(e)))
        result["error"] = e.to_dict()
        result["duration_ms"] = int((time() - start_time) * 1000)
        logger.warning(
            "Connection test failed at token",
            extra={"tool_name": "test_connection", "error_code": e.code},
        )
        return result
    except PlanviewError as e:
        checks.append(_check("token", False, str(e)))
        result["error"] = e.to_dict() if hasattr(e, "to_dict") else {"ok": False, "error": str(e)}
        result["duration_ms"] = int((time() - start_time) * 1000)
        return result

    checks.append(
        _check(
            "token",
            True,
            f"Issued a client_credentials token via {token.encoding} encoding "
            f"(expires in {token.expires_in}s).",
        )
    )

    try:
        ping = await ping_with_access_token(token.access_token)
    except PlanviewAuthError as e:
        checks.append(_check("ping", False, str(e)))
        result["error"] = e.to_dict()
        result["duration_ms"] = int((time() - start_time) * 1000)
        logger.warning(
            "Connection test failed at ping",
            extra={"tool_name": "test_connection", "error_code": e.code},
        )
        return result
    except PlanviewError as e:
        checks.append(_check("ping", False, str(e)))
        result["error"] = e.to_dict() if hasattr(e, "to_dict") else {"ok": False, "error": str(e)}
        result["duration_ms"] = int((time() - start_time) * 1000)
        return result

    checks.append(_check("ping", True, "Secured ping accepted the token."))
    result["ok"] = True
    result["connected"] = True
    result["ping"] = ping.get("data")
    result["duration_ms"] = int((time() - start_time) * 1000)
    logger.info(
        "Connection test succeeded",
        extra={"tool_name": "test_connection", "duration_ms": result["duration_ms"]},
    )
    return result


# Backward-compatible name for internal scripts; not registered as an MCP tool.
oauth_ping = test_connection
