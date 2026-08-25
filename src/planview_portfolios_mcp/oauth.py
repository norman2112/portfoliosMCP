"""OAuth token management for Planview Portfolios API."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from .config import get_httpx_verify_setting, settings
from .exceptions import PlanviewAuthError, PlanviewError

logger = logging.getLogger(__name__)

TOKEN_PATH = "/public-api/v1/oauth/token"
PING_PATH = "/public-api/v1/oauth/ping"
_DEFAULT_API_URL = "https://api.planview.com"
_BODY_PREVIEW_LIMIT = 400


@dataclass
class OAuthToken:
    """OAuth token with expiration tracking."""

    access_token: str
    expires_at: datetime
    token_type: str = "bearer"
    expires_in: int = 3600
    encoding: str = "multipart"

    def is_expired(self, buffer_seconds: int | None = None) -> bool:
        """Check if token is expired (with buffer for clock skew)."""
        if buffer_seconds is None:
            buffer_seconds = min(60, max(5, self.expires_in // 10))
        return datetime.now() >= (self.expires_at - timedelta(seconds=buffer_seconds))


def _looks_like_jwt(value: str) -> bool:
    if not value or not value.startswith("eyJ"):
        return False
    return value.count(".") == 2


def _preview_body(response: httpx.Response) -> str:
    text = (response.text or "").strip()
    if len(text) > _BODY_PREVIEW_LIMIT:
        return text[:_BODY_PREVIEW_LIMIT] + "…"
    return text


def _parse_expires_in(data: dict[str, Any]) -> int:
    raw = data.get("expires_in", 3600)
    try:
        expires_in = int(raw)
    except (TypeError, ValueError):
        return 3600
    # Swagger examples use 0; a zero/negative TTL would mark every token expired.
    if expires_in <= 0:
        return 3600
    return expires_in


def inspect_oauth_config(
    api_url: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Validate OAuth config without contacting Planview. Never returns secrets."""
    api_url = api_url if api_url is not None else settings.planview_api_url
    client_id = client_id if client_id is not None else settings.planview_client_id
    client_secret = client_secret if client_secret is not None else settings.planview_client_secret
    tenant_id = tenant_id if tenant_id is not None else settings.planview_tenant_id

    checks: list[dict[str, Any]] = []
    hints: list[str] = []
    blocking_ok = True

    def add(name: str, passed: bool, detail: str, hint: str | None = None, *, blocking: bool = True) -> None:
        nonlocal blocking_ok
        checks.append({"name": name, "ok": passed, "detail": detail})
        if not passed:
            if blocking:
                blocking_ok = False
            if hint:
                hints.append(hint)

    parsed = urlparse(api_url or "")
    host = parsed.netloc or ""
    path = (parsed.path or "").rstrip("/")

    if not api_url or api_url.rstrip("/") == _DEFAULT_API_URL:
        add(
            "api_url",
            False,
            f"PLANVIEW_API_URL is missing or still the default ({_DEFAULT_API_URL}).",
            "Set PLANVIEW_API_URL to https://your-instance.pvcloud.com/polaris (lowercase).",
        )
    elif not parsed.scheme or not host:
        add(
            "api_url",
            False,
            f"PLANVIEW_API_URL is not a valid URL: {api_url!r}.",
            "Use https://your-instance.pvcloud.com/polaris — include the scheme.",
        )
    else:
        notes: list[str] = [f"Using {parsed.scheme}://{host}{path or ''}"]
        if path != "/polaris":
            notes.append("Path does not end in /polaris.")
            hints.append(
                "PLANVIEW_API_URL must include /polaris "
                "(example: https://scdemo508.pvcloud.com/polaris), not the host alone "
                "and not a /public-api path."
            )
            blocking_ok = False
        if "/public-api" in path:
            notes.append("URL already contains /public-api; token requests will double the path.")
            hints.append("Remove /public-api/v1 from PLANVIEW_API_URL; the server appends it.")
            blocking_ok = False
        add("api_url", path == "/polaris" and "/public-api" not in path, " ".join(notes), None)

    if not client_id:
        add(
            "client_id",
            False,
            "PLANVIEW_CLIENT_ID is empty.",
            "Copy the Client ID from Administration → Users → OAuth2 credentials.",
        )
    else:
        add("client_id", True, f"PLANVIEW_CLIENT_ID is set ({len(client_id)} chars).")

    if not client_secret:
        add(
            "client_secret",
            False,
            "PLANVIEW_CLIENT_SECRET is empty.",
            "Use the client secret shown once at OAuth credential creation — "
            "not a bearer access token.",
        )
    elif _looks_like_jwt(client_secret):
        add(
            "client_secret",
            False,
            "PLANVIEW_CLIENT_SECRET looks like a JWT access token, not an OAuth client secret.",
            "This server uses OAuth client_credentials. Put the OAuth client secret in "
            "PLANVIEW_CLIENT_SECRET. Do not paste a freshly issued bearer token.",
        )
    else:
        add("client_secret", True, f"PLANVIEW_CLIENT_SECRET is set ({len(client_secret)} chars).")

    if not tenant_id:
        add(
            "tenant_id",
            False,
            "PLANVIEW_TENANT_ID is empty. Token issuance may still succeed; secured ping often returns 401.",
            "Ask a Planview admin for the global tenant ID. A valid token with a missing "
            "X-Tenant-Id is the most common 'fresh token still fails' failure.",
            blocking=False,
        )
    else:
        add("tenant_id", True, f"PLANVIEW_TENANT_ID is set ({len(tenant_id)} chars).")

    error = None
    if not blocking_ok:
        error = {
            "code": "config",
            "message": "OAuth configuration is incomplete or malformed.",
            "hint": " ".join(hints) if hints else None,
        }

    return {
        "ok": blocking_ok,
        "checks": checks,
        "error": error,
        "token_url": f"{api_url.rstrip('/')}{TOKEN_PATH}" if api_url else TOKEN_PATH,
        "ping_url": f"{api_url.rstrip('/')}{PING_PATH}" if api_url else PING_PATH,
        "host": host,
    }


def _auth_error_from_response(
    response: httpx.Response,
    *,
    encodings_tried: list[str],
    endpoint: str,
) -> PlanviewAuthError:
    body = _preview_body(response)
    status = response.status_code
    if status in (401, 403):
        hint = (
            "Client ID or client secret was rejected. Confirm both values were copied "
            "without extra quotes, and that they belong to this instance "
            f"({urlparse(endpoint).netloc}). The secret is shown only once at creation."
        )
        code = "invalid_credentials"
    elif status == 404:
        hint = (
            "Token URL was not found. PLANVIEW_API_URL should be "
            "https://your-instance.pvcloud.com/polaris (lowercase, with /polaris)."
        )
        code = "bad_token_url"
    elif status == 400:
        hint = (
            "Token request was rejected (HTTP 400). Common causes: wrong grant encoding, "
            "PLANVIEW_CLIENT_SECRET is a bearer token instead of the OAuth client secret, "
            "or the API URL host is uppercase."
        )
        code = "token_bad_request"
    else:
        hint = "Token endpoint returned an unexpected status."
        code = "token_http_error"

    return PlanviewAuthError(
        f"OAuth token request failed (HTTP {status}) via {', '.join(encodings_tried)}. "
        f"Planview said: {body or '(empty body)'}",
        code=code,
        hint=hint,
        status_code=status,
        endpoint=endpoint,
        details={"encodings_tried": encodings_tried, "response_preview": body},
    )


class OAuthTokenManager:
    """Manages OAuth token lifecycle with caching and automatic refresh."""

    def __init__(self) -> None:
        self._token: Optional[OAuthToken] = None
        self._lock = asyncio.Lock()

    async def get_token(self, force_refresh: bool = False) -> str:
        token = await self.get_token_record(force_refresh=force_refresh)
        return token.access_token

    async def get_token_record(self, force_refresh: bool = False) -> OAuthToken:
        async with self._lock:
            if not force_refresh and self._token and not self._token.is_expired():
                return self._token
            token = await self._fetch_token()
            self._token = token
            return token

    async def _fetch_token(self) -> OAuthToken:
        config = inspect_oauth_config()
        if not config["ok"]:
            err = config["error"] or {}
            raise PlanviewAuthError(
                err.get("message") or "OAuth configuration is invalid.",
                code=err.get("code") or "config",
                hint=err.get("hint"),
                details={"checks": config["checks"]},
            )

        token_url = config["token_url"]
        client_id = settings.planview_client_id
        client_secret = settings.planview_client_secret

        attempts: list[tuple[str, dict[str, Any]]] = [
            (
                "multipart",
                {"files": {
                    "grant_type": (None, "client_credentials"),
                    "client_id": (None, client_id),
                    "client_secret": (None, client_secret),
                }},
            ),
            (
                "form",
                {"data": {
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                }},
            ),
            (
                "json",
                {"json": {
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                }},
            ),
        ]

        tried: list[str] = []
        last_response: httpx.Response | None = None

        try:
            async with httpx.AsyncClient(
                timeout=settings.api_timeout,
                verify=get_httpx_verify_setting(),
            ) as client:
                for encoding, kwargs in attempts:
                    tried.append(encoding)
                    response = await client.post(token_url, **kwargs)
                    last_response = response
                    if response.status_code == 200:
                        return self._token_from_response(response, encoding=encoding)
                    # 400/415: try the next encoding. 401: credentials are wrong regardless of encoding.
                    if response.status_code in (400, 415) and encoding != attempts[-1][0]:
                        logger.info(
                            "OAuth token %s encoding returned HTTP %s; trying next encoding",
                            encoding,
                            response.status_code,
                        )
                        continue
                    raise _auth_error_from_response(
                        response, encodings_tried=tried, endpoint=token_url
                    )

        except PlanviewAuthError:
            raise
        except httpx.TimeoutException as e:
            raise PlanviewAuthError(
                f"Timeout obtaining OAuth token from {token_url}: {e}",
                code="token_timeout",
                hint="Check VPN/proxy and that PLANVIEW_API_URL is reachable.",
                endpoint=token_url,
            ) from e
        except httpx.RequestError as e:
            raise PlanviewAuthError(
                f"Network error obtaining OAuth token from {token_url}: {e}",
                code="token_network",
                hint="Check PLANVIEW_API_URL, TLS (PLANVIEW_CA_BUNDLE), and network access.",
                endpoint=token_url,
            ) from e
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            body = _preview_body(last_response) if last_response is not None else ""
            raise PlanviewAuthError(
                f"OAuth token response was not valid JSON: {e}. Body: {body}",
                code="token_parse",
                hint="The token URL may be wrong (HTML login page) or the instance returned an error page.",
                endpoint=token_url,
                details={"response_preview": body},
            ) from e

        raise PlanviewAuthError(
            "OAuth token request failed after all encodings.",
            code="token_http_error",
            endpoint=token_url,
            details={"encodings_tried": tried},
        )

    def _token_from_response(self, response: httpx.Response, *, encoding: str) -> OAuthToken:
        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            raise PlanviewAuthError(
                "Token response missing access_token.",
                code="token_parse",
                hint="The token endpoint responded 200 but did not include access_token.",
                endpoint=str(response.request.url),
                details={"response_preview": _preview_body(response)},
            )
        expires_in = _parse_expires_in(data)
        token_type = str(data.get("token_type") or "bearer")
        logger.info(
            "Obtained OAuth token via %s encoding (expires in %ss)",
            encoding,
            expires_in,
        )
        return OAuthToken(
            access_token=access_token,
            expires_at=datetime.now() + timedelta(seconds=expires_in),
            token_type=token_type,
            expires_in=expires_in,
            encoding=encoding,
        )

    async def clear_token(self) -> None:
        async with self._lock:
            self._token = None


_token_manager = OAuthTokenManager()


async def get_oauth_token(force_refresh: bool = False) -> str:
    """Get a valid OAuth token."""
    return await _token_manager.get_token(force_refresh=force_refresh)


async def get_oauth_token_record(force_refresh: bool = False) -> OAuthToken:
    """Get the cached/fetched token record (includes expiry metadata)."""
    return await _token_manager.get_token_record(force_refresh=force_refresh)


async def clear_oauth_token() -> None:
    """Clear the cached OAuth token."""
    await _token_manager.clear_token()


async def ping_with_access_token(access_token: str) -> dict[str, Any]:
    """Call secured ping with an explicit token (does not use the pooled REST client)."""
    ping_url = f"{settings.planview_api_url.rstrip('/')}{PING_PATH}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Tenant-Id": settings.planview_tenant_id,
        "Accept": "application/json, text/plain",
    }
    async with httpx.AsyncClient(
        timeout=settings.api_timeout,
        verify=get_httpx_verify_setting(),
    ) as client:
        response = await client.get(ping_url, headers=headers)

    if response.status_code == 200:
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {"message": response.text.strip()}
        else:
            text = response.text.strip()
            payload = {"message": text} if text else {"status": "success"}
        return {"ok": True, "status_code": 200, "data": payload}

    body = _preview_body(response)
    if response.status_code in (401, 403):
        hint = (
            "A freshly issued token was rejected on secured ping. "
            "This is usually PLANVIEW_TENANT_ID (wrong or missing), not the client secret. "
            "Confirm the tenant ID for this instance and that PLANVIEW_API_URL host matches "
            "the instance where the OAuth client was created."
        )
        raise PlanviewAuthError(
            f"Secured ping rejected the token (HTTP {response.status_code}). "
            f"Planview said: {body or '(empty body)'}",
            code="ping_unauthorized",
            hint=hint,
            status_code=response.status_code,
            endpoint=ping_url,
            details={"response_preview": body, "tenant_id_set": bool(settings.planview_tenant_id)},
        )
    raise PlanviewAuthError(
        f"Secured ping failed (HTTP {response.status_code}). Planview said: {body or '(empty body)'}",
        code="ping_http_error",
        hint="Token was issued, but ping did not return 200. Check API URL and tenant ID.",
        status_code=response.status_code,
        endpoint=ping_url,
        details={"response_preview": body},
    )
