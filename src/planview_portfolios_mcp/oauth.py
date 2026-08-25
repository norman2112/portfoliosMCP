"""OAuth token management for Planview Portfolios API."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from .config import get_httpx_verify_setting, settings
from .exceptions import PlanviewAuthError

logger = logging.getLogger(__name__)

TOKEN_PATH = "/public-api/v1/oauth/token"
PING_PATH = "/public-api/v1/oauth/ping"
_DEFAULT_API_URL = "https://api.planview.com"
_BODY_PREVIEW_LIMIT = 600

# Planview Swagger lists Consumes: multipart/form-data only.
# urlencoded form sometimes binds as a fallback. JSON does not bind on this
# endpoint and returns a misleading "fields missing" body — never try it for
# token issuance (it poisoned earlier diagnostics).
_TOKEN_ENCODINGS: tuple[str, ...] = ("multipart", "form")

_MISSING_FIELD_RE = re.compile(
    r"(is required|was not present|are required|must be (provided|supplied)|"
    r"missing|the .+ field|required property|could not be bound)",
    re.IGNORECASE,
)
_CREDENTIAL_RE = re.compile(
    r"(invalid_client|invalid_grant|unauthorized|invalid.?credential|"
    r"authentication failed|access.?denied|client authentication)",
    re.IGNORECASE,
)


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


@dataclass
class TokenFetchResult:
    """Outcome of one or more token-endpoint attempts."""

    token: OAuthToken | None = None
    attempts: list[dict[str, Any]] = field(default_factory=list)
    diagnosis: dict[str, Any] = field(default_factory=dict)
    token_url: str = ""


def _looks_like_jwt(value: str) -> bool:
    if not value or not value.startswith("eyJ"):
        return False
    return value.count(".") == 2


def fingerprint(value: str | None, *, reveal: int = 4) -> dict[str, Any]:
    """Describe a config value without exposing the full secret.

    Enough for a human to catch stale/wrong-but-present values (length + ends
    + short hash) without dumping credentials into chat logs.
    """
    if value is None or value == "":
        return {"set": False, "length": 0}
    n = len(value)
    if n <= reveal * 2:
        visible = {"prefix": "…", "suffix": "…"}
    else:
        visible = {"prefix": value[:reveal], "suffix": value[-reveal:]}
    return {
        "set": True,
        "length": n,
        **visible,
        "sha256_8": hashlib.sha256(value.encode("utf-8")).hexdigest()[:8],
    }


def _preview_body(response: httpx.Response) -> str:
    text = (response.text or "").strip()
    if len(text) > _BODY_PREVIEW_LIMIT:
        return text[:_BODY_PREVIEW_LIMIT] + "…"
    return text


_ACCESS_TOKEN_JSON_RE = re.compile(
    r'("access_token"\s*:\s*")([^"]+)(")',
    re.IGNORECASE,
)


def redact_access_token_in_body(body: str | None) -> str:
    """Strip bearer tokens from response previews so diagnostics stay shareable."""
    if not body:
        return "(empty body)"
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, TypeError):
        return _ACCESS_TOKEN_JSON_RE.sub(r'\1[redacted]\3', body)
    if isinstance(data, dict) and "access_token" in data:
        redacted = dict(data)
        token = redacted.get("access_token")
        redacted["access_token"] = fingerprint(str(token), reveal=2) if token else None
        return json.dumps(redacted, separators=(",", ":"))
    return body


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


def _response_headers_of_interest(response: httpx.Response) -> dict[str, str]:
    wanted = (
        "content-type",
        "www-authenticate",
        "x-request-id",
        "x-correlation-id",
        "request-id",
        "traceparent",
    )
    out: dict[str, str] = {}
    for key in wanted:
        val = response.headers.get(key)
        if val:
            out[key] = val
    return out


def classify_token_response(status_code: int, body: str) -> str:
    """Classify how far the token endpoint got with this attempt.

    Distinguishes credential evaluation from bodies that never bound the
    grant fields — those two failures need completely different next steps.
    """
    if status_code == 200:
        return "success"
    if status_code == 404:
        return "bad_url"
    if status_code == 415:
        return "unsupported_media"
    text = body or ""
    if status_code in (401, 403):
        return "credentials_rejected"
    if status_code == 400:
        if _CREDENTIAL_RE.search(text):
            return "credentials_rejected"
        if _MISSING_FIELD_RE.search(text) or re.search(r"invalid_request", text, re.IGNORECASE):
            # OAuth invalid_request / model-binding misses: fields never evaluated.
            return "request_not_bound"
        # Ambiguous 400: treat as bound enough to be actionable (often bad secret).
        return "credentials_rejected"
    if status_code >= 500:
        return "server_error"
    return "token_http_error"


def _should_try_next_encoding(classification: str, encoding: str, remaining: bool) -> bool:
    """Only fall through when the current encoding did not bind the grant."""
    if not remaining:
        return False
    if encoding != "multipart":
        return False
    return classification in ("request_not_bound", "unsupported_media")


def diagnose_token_attempts(attempts: list[dict[str, Any]], *, token_url: str) -> dict[str, Any]:
    """Pick a verdict from the full attempt log — never 'last error wins'."""
    if not attempts:
        return {
            "verdict": "no_attempts",
            "summary": "No token requests were made.",
            "next_step": "Fix configuration, then retry test_connection.",
            "primary_attempt": None,
        }

    success = next((a for a in attempts if a.get("classification") == "success"), None)
    if success:
        return {
            "verdict": "ok",
            "summary": f"Token issued via {success['encoding']} encoding.",
            "next_step": None,
            "primary_attempt": success["encoding"],
        }

    by_class: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        by_class.setdefault(attempt.get("classification") or "unknown", []).append(attempt)

    rejected = by_class.get("credentials_rejected") or []
    unbound = by_class.get("request_not_bound") or []
    bad_url = by_class.get("bad_url") or []
    unsupported = by_class.get("unsupported_media") or []
    server = by_class.get("server_error") or []

    if bad_url:
        primary = bad_url[0]
        return {
            "verdict": "bad_url",
            "summary": (
                f"Token URL returned HTTP {primary.get('status_code')} "
                f"({primary.get('encoding')}). The endpoint path is wrong or unreachable."
            ),
            "next_step": (
                "Set PLANVIEW_API_URL to https://your-instance.pvcloud.com/polaris "
                "(lowercase host, include /polaris, do not include /public-api)."
            ),
            "primary_attempt": primary["encoding"],
            "planview_said": primary.get("body_preview") or "(empty body)",
        }

    if rejected:
        primary = rejected[0]
        note = None
        if unbound:
            note = (
                "A later encoding reported missing grant fields because that body "
                "encoding was not parsed. That is not a field-casing bug — ignore it. "
                "Use the credentials_rejected attempt as the real signal."
            )
        return {
            "verdict": "credentials_rejected",
            "summary": (
                f"Planview evaluated the grant via {primary['encoding']} and rejected "
                f"the client id/secret (HTTP {primary.get('status_code')})."
            ),
            "next_step": (
                "Confirm PLANVIEW_CLIENT_ID and PLANVIEW_CLIENT_SECRET belong to this "
                f"instance ({urlparse(token_url).netloc}), were copied without extra "
                "quotes, and that the secret is the OAuth client secret (not a bearer "
                "token). The secret is shown only once at creation — rotate if unsure."
            ),
            "primary_attempt": primary["encoding"],
            "planview_said": primary.get("body_preview") or "(empty body)",
            "note": note,
        }

    if unbound or unsupported:
        primary = (unbound or unsupported)[0]
        encodings = ", ".join(a["encoding"] for a in attempts)
        return {
            "verdict": "request_not_bound",
            "summary": (
                f"The token endpoint never evaluated credentials. Attempted "
                f"encoding(s): {encodings}. Responses indicate the grant fields were "
                f"not bound (HTTP {primary.get('status_code')})."
            ),
            "next_step": (
                "This is not a wrong-password problem. Open a Planview support ticket "
                "with the diagnostic_bundle from this result (token_url, attempts, "
                "response headers/bodies). Double-check PLANVIEW_API_URL host matches "
                "the instance where the OAuth client was created."
            ),
            "primary_attempt": primary["encoding"],
            "planview_said": primary.get("body_preview") or "(empty body)",
        }

    if server:
        primary = server[0]
        return {
            "verdict": "server_error",
            "summary": f"Token endpoint returned HTTP {primary.get('status_code')}.",
            "next_step": "Retry later; if it persists, send the diagnostic_bundle to Planview.",
            "primary_attempt": primary["encoding"],
            "planview_said": primary.get("body_preview") or "(empty body)",
        }

    primary = attempts[0]
    return {
        "verdict": "token_http_error",
        "summary": (
            f"Token request failed (HTTP {primary.get('status_code')}) via "
            f"{primary.get('encoding')}."
        ),
        "next_step": "Inspect attempts[].body_preview and open a support ticket if unclear.",
        "primary_attempt": primary["encoding"],
        "planview_said": primary.get("body_preview") or "(empty body)",
    }


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

    client_fp = fingerprint(client_id, reveal=4)
    secret_fp = fingerprint(client_secret, reveal=2)
    tenant_fp = fingerprint(tenant_id, reveal=4)

    if not client_id:
        add(
            "client_id",
            False,
            "PLANVIEW_CLIENT_ID is empty.",
            "Copy the Client ID from Administration → Users → OAuth2 credentials.",
        )
    else:
        add(
            "client_id",
            True,
            (
                f"PLANVIEW_CLIENT_ID is set (len={client_fp['length']}, "
                f"prefix={client_fp['prefix']!r}, suffix={client_fp['suffix']!r}, "
                f"sha256_8={client_fp['sha256_8']})."
            ),
        )

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
        add(
            "client_secret",
            True,
            (
                f"PLANVIEW_CLIENT_SECRET is set (len={secret_fp['length']}, "
                f"prefix={secret_fp['prefix']!r}, suffix={secret_fp['suffix']!r}, "
                f"sha256_8={secret_fp['sha256_8']}). Compare sha256_8 against a known-good "
                "secret to catch stale values without pasting the secret."
            ),
        )

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
        add(
            "tenant_id",
            True,
            (
                f"PLANVIEW_TENANT_ID is set (len={tenant_fp['length']}, "
                f"prefix={tenant_fp['prefix']!r}, suffix={tenant_fp['suffix']!r}, "
                f"sha256_8={tenant_fp['sha256_8']})."
            ),
        )

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
        "fingerprints": {
            "api_url": api_url,
            "host": host,
            "client_id": client_fp,
            "client_secret": secret_fp,
            "tenant_id": tenant_fp,
        },
    }


def _encoding_request_kwargs(encoding: str, client_id: str, client_secret: str) -> dict[str, Any]:
    if encoding == "multipart":
        return {
            "files": {
                "grant_type": (None, "client_credentials"),
                "client_id": (None, client_id),
                "client_secret": (None, client_secret),
            }
        }
    if encoding == "form":
        return {
            "data": {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
        }
    raise ValueError(f"Unsupported token encoding: {encoding}")


def _content_type_for_encoding(encoding: str) -> str:
    if encoding == "multipart":
        return "multipart/form-data"
    if encoding == "form":
        return "application/x-www-form-urlencoded"
    return encoding


def _token_from_payload(data: dict[str, Any], *, encoding: str, endpoint: str, body: str) -> OAuthToken:
    access_token = data.get("access_token")
    if not access_token:
        raise PlanviewAuthError(
            "Token response missing access_token.",
            code="token_parse",
            hint="The token endpoint responded 200 but did not include access_token.",
            endpoint=endpoint,
            details={"response_preview": body},
        )
    expires_in = _parse_expires_in(data)
    token_type = str(data.get("token_type") or "bearer")
    return OAuthToken(
        access_token=access_token,
        expires_at=datetime.now() + timedelta(seconds=expires_in),
        token_type=token_type,
        expires_in=expires_in,
        encoding=encoding,
    )


async def fetch_oauth_token_with_diagnosis() -> TokenFetchResult:
    """POST /oauth/token, recording every attempt and a cross-attempt diagnosis.

    Encoding policy: try multipart (documented). Only fall through to urlencoded
    form when multipart did not bind. Never try JSON.
    """
    config = inspect_oauth_config()
    token_url = config["token_url"]
    result = TokenFetchResult(token_url=token_url)

    if not config["ok"]:
        err = config["error"] or {}
        result.diagnosis = {
            "verdict": "config",
            "summary": err.get("message") or "OAuth configuration is invalid.",
            "next_step": err.get("hint"),
            "primary_attempt": None,
        }
        return result

    client_id = settings.planview_client_id
    client_secret = settings.planview_client_secret
    encodings = list(_TOKEN_ENCODINGS)

    try:
        async with httpx.AsyncClient(
            timeout=settings.api_timeout,
            verify=get_httpx_verify_setting(),
        ) as client:
            for index, encoding in enumerate(encodings):
                remaining = index < len(encodings) - 1
                kwargs = _encoding_request_kwargs(encoding, client_id, client_secret)
                response = await client.post(token_url, **kwargs)
                raw_body = _preview_body(response)
                classification = classify_token_response(response.status_code, raw_body)
                body = redact_access_token_in_body(raw_body)

                attempt: dict[str, Any] = {
                    "encoding": encoding,
                    "content_type_sent": _content_type_for_encoding(encoding),
                    "status_code": response.status_code,
                    "classification": classification,
                    "body_preview": body or "(empty body)",
                    "response_headers": _response_headers_of_interest(response),
                    "credentials_evaluated": classification
                    in ("success", "credentials_rejected"),
                }
                result.attempts.append(attempt)

                if response.status_code == 200:
                    try:
                        data = response.json()
                    except json.JSONDecodeError as e:
                        attempt["classification"] = "token_parse"
                        result.diagnosis = {
                            "verdict": "token_parse",
                            "summary": f"HTTP 200 but body was not JSON: {e}",
                            "next_step": (
                                "Token URL may be returning an HTML login page. "
                                "Verify PLANVIEW_API_URL."
                            ),
                            "primary_attempt": encoding,
                            "planview_said": body,
                        }
                        return result
                    try:
                        token = _token_from_payload(
                            data, encoding=encoding, endpoint=token_url, body=body
                        )
                    except PlanviewAuthError as e:
                        attempt["classification"] = "token_parse"
                        result.diagnosis = {
                            "verdict": "token_parse",
                            "summary": str(e),
                            "next_step": e.hint,
                            "primary_attempt": encoding,
                            "planview_said": body,
                        }
                        return result
                    attempt["access_token"] = fingerprint(token.access_token, reveal=2)
                    result.token = token
                    result.diagnosis = diagnose_token_attempts(result.attempts, token_url=token_url)
                    logger.info(
                        "Obtained OAuth token via %s encoding (expires in %ss)",
                        encoding,
                        token.expires_in,
                    )
                    return result

                if _should_try_next_encoding(classification, encoding, remaining):
                    logger.info(
                        "OAuth token %s encoding classified as %s (HTTP %s); trying next encoding",
                        encoding,
                        classification,
                        response.status_code,
                    )
                    continue
                break

    except httpx.TimeoutException as e:
        result.diagnosis = {
            "verdict": "token_timeout",
            "summary": f"Timeout obtaining OAuth token from {token_url}: {e}",
            "next_step": "Check VPN/proxy and that PLANVIEW_API_URL is reachable.",
            "primary_attempt": None,
        }
        return result
    except httpx.RequestError as e:
        result.diagnosis = {
            "verdict": "token_network",
            "summary": f"Network error obtaining OAuth token from {token_url}: {e}",
            "next_step": "Check PLANVIEW_API_URL, TLS (PLANVIEW_CA_BUNDLE), and network access.",
            "primary_attempt": None,
        }
        return result

    result.diagnosis = diagnose_token_attempts(result.attempts, token_url=token_url)
    return result


def _auth_error_from_fetch(fetch: TokenFetchResult) -> PlanviewAuthError:
    diagnosis = fetch.diagnosis or {}
    verdict = diagnosis.get("verdict") or "token_http_error"
    primary = None
    if diagnosis.get("primary_attempt"):
        primary = next(
            (a for a in fetch.attempts if a.get("encoding") == diagnosis["primary_attempt"]),
            None,
        )
    status = primary.get("status_code") if primary else None
    code_map = {
        "credentials_rejected": "invalid_credentials",
        "request_not_bound": "request_not_bound",
        "bad_url": "bad_token_url",
        "unsupported_media": "request_not_bound",
        "server_error": "token_http_error",
        "token_timeout": "token_timeout",
        "token_network": "token_network",
        "token_parse": "token_parse",
        "config": "config",
    }
    message = diagnosis.get("summary") or "OAuth token request failed."
    if diagnosis.get("planview_said"):
        message = f"{message} Planview said: {diagnosis['planview_said']}"
    return PlanviewAuthError(
        message,
        code=code_map.get(verdict, "token_http_error"),
        hint=diagnosis.get("next_step"),
        status_code=status,
        endpoint=fetch.token_url,
        details={
            "verdict": verdict,
            "attempts": fetch.attempts,
            "diagnosis": diagnosis,
        },
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
        fetch = await fetch_oauth_token_with_diagnosis()
        if fetch.token is not None:
            return fetch.token
        raise _auth_error_from_fetch(fetch)

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

    body = _preview_body(response)
    headers_out = _response_headers_of_interest(response)

    if response.status_code == 200:
        content_type = response.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {"message": body}
        else:
            payload = {"message": body} if body else {"status": "success"}
        return {
            "ok": True,
            "status_code": 200,
            "data": payload,
            "body_preview": body or "(empty body)",
            "response_headers": headers_out,
        }

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
            details={
                "response_preview": body,
                "response_headers": headers_out,
                "tenant_id_set": bool(settings.planview_tenant_id),
                "tenant_id": fingerprint(settings.planview_tenant_id, reveal=4),
            },
        )
    raise PlanviewAuthError(
        f"Secured ping failed (HTTP {response.status_code}). Planview said: {body or '(empty body)'}",
        code="ping_http_error",
        hint="Token was issued, but ping did not return 200. Check API URL and tenant ID.",
        status_code=response.status_code,
        endpoint=ping_url,
        details={"response_preview": body, "response_headers": headers_out},
    )
