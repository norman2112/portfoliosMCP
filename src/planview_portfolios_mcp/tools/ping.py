"""Connection diagnostic tool for Planview Portfolios OAuth."""

import logging
from time import time
from typing import Any

from ..config import settings
from ..exceptions import PlanviewAuthError, PlanviewError
from ..oauth import (
    clear_oauth_token,
    fetch_oauth_token_with_diagnosis,
    fingerprint,
    inspect_oauth_config,
    ping_with_access_token,
)
from ..performance import log_performance

logger = logging.getLogger(__name__)


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def _diagnostic_bundle(
    *,
    config: dict[str, Any],
    attempts: list[dict[str, Any]] | None = None,
    ping: dict[str, Any] | None = None,
    diagnosis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Everything Planview support needs without full secrets."""
    return {
        "host": config.get("host"),
        "token_url": config.get("token_url"),
        "ping_url": config.get("ping_url"),
        "fingerprints": config.get("fingerprints"),
        "token_attempts": attempts or [],
        "ping": ping,
        "diagnosis": diagnosis,
    }


@log_performance
async def test_connection() -> dict[str, Any]:
    """[LOCAL — diagnose this server's Planview OAuth connection.]

    Test the Portfolios OAuth connection with a fresh client_credentials token.

    Always returns a structured result (does not throw on auth failure) so the
    model and a human can act without reading source or running manual probes.

    Output shape:
    - ``checks`` — config / token / ping pass-fail summaries
    - ``steps`` — ordered stages with their full outcomes (not flattened)
    - ``token_attempts`` — every encoding tried, each with status, classification,
      body preview, and whether credentials were evaluated
    - ``diagnosis`` — verdict + next_step chosen from the *best* signal across
      attempts (never "last error wins")
    - ``diagnostic_bundle`` — ticket-ready bundle (URLs, fingerprints, attempts, headers)
    - On success, ``authenticated_as`` — host / client / tenant fingerprints and
      which encoding issued the token

    Encoding policy: multipart/form-data (documented), then urlencoded form only
    if multipart did not bind. JSON is not attempted — it never binds here and
    previously produced a false "fields missing" diagnosis.
    """
    start_time = time()
    logger.info("Testing Planview connection", extra={"tool_name": "test_connection"})

    config = inspect_oauth_config()
    checks: list[dict[str, Any]] = list(config["checks"])
    steps: list[dict[str, Any]] = [
        {
            "stage": "config",
            "ok": config["ok"],
            "checks": config["checks"],
            "fingerprints": config.get("fingerprints"),
        }
    ]

    result: dict[str, Any] = {
        "ok": False,
        "connected": False,
        "checks": checks,
        "steps": steps,
        "token_url": config["token_url"],
        "ping_url": config["ping_url"],
        "host": config["host"],
        "fingerprints": config.get("fingerprints"),
    }

    if not config["ok"]:
        diagnosis = {
            "verdict": "config",
            "summary": (config.get("error") or {}).get("message")
            or "OAuth configuration is incomplete or malformed.",
            "next_step": (config.get("error") or {}).get("hint"),
            "primary_attempt": None,
        }
        result["diagnosis"] = diagnosis
        result["error"] = config["error"]
        result["diagnostic_bundle"] = _diagnostic_bundle(config=config, diagnosis=diagnosis)
        result["duration_ms"] = int((time() - start_time) * 1000)
        logger.warning(
            "Connection test failed at config",
            extra={
                "tool_name": "test_connection",
                "checks": [c["name"] for c in checks if not c["ok"]],
            },
        )
        return result

    # Fresh probe — do not trust a cached token for diagnosis.
    await clear_oauth_token()
    fetch = await fetch_oauth_token_with_diagnosis()
    attempts = fetch.attempts
    token_diagnosis = fetch.diagnosis
    result["token_attempts"] = attempts
    steps.append(
        {
            "stage": "token",
            "ok": fetch.token is not None,
            "attempts": attempts,
            "diagnosis": token_diagnosis,
        }
    )

    if fetch.token is None:
        detail = token_diagnosis.get("summary") or "Token request failed."
        if token_diagnosis.get("note"):
            detail = f"{detail} {token_diagnosis['note']}"
        checks.append(_check("token", False, detail))
        result["diagnosis"] = {
            **token_diagnosis,
            "stage": "token",
        }
        result["error"] = {
            "ok": False,
            "code": token_diagnosis.get("verdict"),
            "error": token_diagnosis.get("summary"),
            "hint": token_diagnosis.get("next_step"),
            "note": token_diagnosis.get("note"),
            "attempts": attempts,
        }
        result["diagnostic_bundle"] = _diagnostic_bundle(
            config=config, attempts=attempts, diagnosis=result["diagnosis"]
        )
        result["duration_ms"] = int((time() - start_time) * 1000)
        logger.warning(
            "Connection test failed at token",
            extra={
                "tool_name": "test_connection",
                "verdict": token_diagnosis.get("verdict"),
            },
        )
        return result

    token = fetch.token
    checks.append(
        _check(
            "token",
            True,
            (
                f"Issued a client_credentials token via {token.encoding} encoding "
                f"(expires in {token.expires_in}s). "
                f"Attempts recorded: {[a['encoding'] + '=' + str(a['status_code']) for a in attempts]}."
            ),
        )
    )

    try:
        ping = await ping_with_access_token(token.access_token)
    except PlanviewAuthError as e:
        ping_step = {
            "stage": "ping",
            "ok": False,
            "status_code": e.status_code,
            "body_preview": (e.details or {}).get("response_preview"),
            "response_headers": (e.details or {}).get("response_headers"),
            "code": e.code,
        }
        steps.append(ping_step)
        checks.append(_check("ping", False, str(e)))
        diagnosis = {
            "stage": "ping",
            "verdict": e.code,
            "summary": str(e),
            "next_step": e.hint,
            "primary_attempt": token.encoding,
            "planview_said": (e.details or {}).get("response_preview"),
        }
        # Token worked — surface that so users don't "fix" good credentials.
        diagnosis["note"] = (
            f"Token issuance succeeded via {token.encoding}. The failure is on "
            "secured ping (typically wrong/missing PLANVIEW_TENANT_ID or cross-tenant URL), "
            "not client_id/client_secret."
        )
        result["diagnosis"] = diagnosis
        result["error"] = e.to_dict()
        result["diagnostic_bundle"] = _diagnostic_bundle(
            config=config,
            attempts=attempts,
            ping=ping_step,
            diagnosis=diagnosis,
        )
        result["duration_ms"] = int((time() - start_time) * 1000)
        logger.warning(
            "Connection test failed at ping",
            extra={"tool_name": "test_connection", "error_code": e.code},
        )
        return result
    except PlanviewError as e:
        steps.append({"stage": "ping", "ok": False, "error": str(e)})
        checks.append(_check("ping", False, str(e)))
        result["error"] = e.to_dict() if hasattr(e, "to_dict") else {"ok": False, "error": str(e)}
        result["duration_ms"] = int((time() - start_time) * 1000)
        return result

    ping_data = ping.get("data")
    ping_step = {
        "stage": "ping",
        "ok": True,
        "status_code": ping.get("status_code"),
        "data": ping_data,
        "body_preview": ping.get("body_preview"),
        "response_headers": ping.get("response_headers"),
    }
    steps.append(ping_step)
    checks.append(_check("ping", True, "Secured ping accepted the token."))

    authenticated_as = {
        "host": config["host"],
        "api_url": settings.planview_api_url,
        "token_url": config["token_url"],
        "ping_url": config["ping_url"],
        "encoding": token.encoding,
        "expires_in": token.expires_in,
        "access_token": fingerprint(token.access_token, reveal=2),
        "client_id": fingerprint(settings.planview_client_id, reveal=4),
        "tenant_id": fingerprint(settings.planview_tenant_id, reveal=4),
        "ping_response": ping_data,
    }

    result["ok"] = True
    result["connected"] = True
    result["ping"] = ping_data
    result["authenticated_as"] = authenticated_as
    result["diagnosis"] = {
        "stage": "done",
        "verdict": "ok",
        "summary": (
            f"Authenticated to {config['host']} as client_id "
            f"{authenticated_as['client_id'].get('prefix')}…"
            f"{authenticated_as['client_id'].get('suffix')} "
            f"(tenant sha256_8={authenticated_as['tenant_id'].get('sha256_8')}) "
            f"via {token.encoding}."
        ),
        "next_step": None,
        "primary_attempt": token.encoding,
    }
    result["diagnostic_bundle"] = _diagnostic_bundle(
        config=config,
        attempts=attempts,
        ping=ping_step,
        diagnosis=result["diagnosis"],
    )
    result["duration_ms"] = int((time() - start_time) * 1000)
    logger.info(
        "Connection test succeeded",
        extra={"tool_name": "test_connection", "duration_ms": result["duration_ms"]},
    )
    return result


# Backward-compatible name for internal scripts; not registered as an MCP tool.
oauth_ping = test_connection
