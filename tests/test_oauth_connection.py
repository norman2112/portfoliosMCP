import json
from datetime import datetime, timedelta

import httpx
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from planview_portfolios_mcp.config import normalize_planview_api_url
from planview_portfolios_mcp.exceptions import PlanviewAuthError
from planview_portfolios_mcp.oauth import (
    classify_token_response,
    diagnose_token_attempts,
    fingerprint,
    inspect_oauth_config,
    ping_with_access_token,
)


def test_normalize_lowercases_host_and_strips_slash():
    assert (
        normalize_planview_api_url(" HTTPS://SCDEMO508.pvcloud.com/polaris/ ")
        == "https://scdemo508.pvcloud.com/polaris"
    )


def test_fingerprint_hides_full_secret_but_shows_shape():
    fp = fingerprint("super-secret-value-here", reveal=2)
    assert fp["set"] is True
    assert fp["length"] == len("super-secret-value-here")
    assert fp["prefix"] == "su"
    assert fp["suffix"] == "re"
    assert len(fp["sha256_8"]) == 8
    assert "super-secret" not in json.dumps(fp)


def test_inspect_includes_fingerprints_for_present_values():
    result = inspect_oauth_config(
        api_url="https://scdemo508.pvcloud.com/polaris",
        client_id="client-abc-12345",
        client_secret="sekrit-value-xyz",
        tenant_id="tenant-9999",
    )
    assert result["ok"] is True
    assert result["fingerprints"]["client_id"]["suffix"] == "2345"
    assert result["fingerprints"]["tenant_id"]["prefix"] == "tena"
    secret_check = next(c for c in result["checks"] if c["name"] == "client_secret")
    assert "sha256_8=" in secret_check["detail"]


def test_inspect_detects_jwt_pasted_as_client_secret():
    result = inspect_oauth_config(
        api_url="https://scdemo508.pvcloud.com/polaris",
        client_id="abc",
        client_secret="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.xxx",
        tenant_id="tenant-1",
    )
    assert result["ok"] is False
    secret_check = next(c for c in result["checks"] if c["name"] == "client_secret")
    assert secret_check["ok"] is False
    assert "JWT" in secret_check["detail"]
    assert "bearer" in (result["error"]["hint"] or "").lower()


def test_inspect_flags_missing_polaris_path():
    result = inspect_oauth_config(
        api_url="https://scdemo508.pvcloud.com",
        client_id="abc",
        client_secret="secret",
        tenant_id="tenant-1",
    )
    assert result["ok"] is False
    url_check = next(c for c in result["checks"] if c["name"] == "api_url")
    assert url_check["ok"] is False
    assert "/polaris" in (result["error"]["hint"] or "")


def test_inspect_missing_tenant_is_warning_not_blocking():
    result = inspect_oauth_config(
        api_url="https://scdemo508.pvcloud.com/polaris",
        client_id="abc",
        client_secret="secret",
        tenant_id="",
    )
    assert result["ok"] is True
    tenant_check = next(c for c in result["checks"] if c["name"] == "tenant_id")
    assert tenant_check["ok"] is False


def test_classify_missing_fields_is_not_credentials():
    body = "The client_id field is required. The grant_type field is required."
    assert classify_token_response(400, body) == "request_not_bound"


def test_classify_401_is_credentials_rejected():
    assert classify_token_response(401, '{"error":"invalid_client"}') == "credentials_rejected"


def test_diagnose_prefers_credentials_over_later_unbound():
    """Regression: last-error-wins reported JSON 'fields missing' and misled users."""
    attempts = [
        {
            "encoding": "multipart",
            "status_code": 401,
            "classification": "credentials_rejected",
            "body_preview": '{"error":"invalid_client"}',
        },
        {
            "encoding": "form",
            "status_code": 400,
            "classification": "request_not_bound",
            "body_preview": "The client_id field is required",
        },
    ]
    diagnosis = diagnose_token_attempts(
        attempts, token_url="https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token"
    )
    assert diagnosis["verdict"] == "credentials_rejected"
    assert diagnosis["primary_attempt"] == "multipart"
    assert "field-casing" in (diagnosis.get("note") or "")
    assert "invalid_client" in diagnosis["planview_said"]


def test_diagnose_all_unbound_means_support_ticket_not_password():
    attempts = [
        {
            "encoding": "multipart",
            "status_code": 400,
            "classification": "request_not_bound",
            "body_preview": "The grant_type field is required",
        },
    ]
    diagnosis = diagnose_token_attempts(
        attempts, token_url="https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token"
    )
    assert diagnosis["verdict"] == "request_not_bound"
    assert "support ticket" in diagnosis["next_step"].lower()
    assert "not a wrong-password" in diagnosis["next_step"].lower()


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict | str | None = None, headers: dict | None = None):
        self.status_code = status_code
        self.headers = headers or {"content-type": "application/json"}
        if isinstance(payload, str):
            self.text = payload
            self._payload = None
        else:
            self._payload = payload or {}
            self.text = json.dumps(self._payload)
        self.request = httpx.Request(
            "POST", "https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token"
        )

    def json(self):
        if self._payload is None:
            raise json.JSONDecodeError("no json", self.text, 0)
        return self._payload


class _DummyClient:
    def __init__(self, post_handler):
        self._post = post_handler

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        return self._post(url, **kwargs)

    async def get(self, url, headers=None):
        raise AssertionError("unexpected get")


@pytest.mark.asyncio
async def test_token_falls_back_from_multipart_to_form_when_unbound(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_id", "cid")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_secret", "csecret")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "tenant-1")

    calls: list[str] = []

    def handler(url, **kwargs):
        if "files" in kwargs:
            calls.append("multipart")
            return _DummyResponse(400, "The client_id field is required")
        if "data" in kwargs:
            calls.append("form")
            return _DummyResponse(
                200,
                {"access_token": "tok-form", "token_type": "bearer", "expires_in": 3600},
            )
        raise AssertionError(f"unexpected kwargs: {kwargs}")

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: _DummyClient(handler))

    await oauth_mod.clear_oauth_token()
    token = await oauth_mod.get_oauth_token_record(force_refresh=True)
    assert token.access_token == "tok-form"
    assert token.encoding == "form"
    assert calls == ["multipart", "form"]


@pytest.mark.asyncio
async def test_token_does_not_fall_through_after_credentials_rejected(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_id", "cid")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_secret", "bad")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "tenant-1")

    calls: list[str] = []

    def handler(url, **kwargs):
        if "files" in kwargs:
            calls.append("multipart")
            return _DummyResponse(401, {"error": "invalid_client"})
        calls.append("other")
        return _DummyResponse(400, "The client_id field is required")

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: _DummyClient(handler))

    await oauth_mod.clear_oauth_token()
    with pytest.raises(PlanviewAuthError) as exc:
        await oauth_mod.get_oauth_token_record(force_refresh=True)
    assert calls == ["multipart"]
    assert exc.value.code == "invalid_credentials"
    assert exc.value.details["diagnosis"]["verdict"] == "credentials_rejected"
    assert len(exc.value.details["attempts"]) == 1


@pytest.mark.asyncio
async def test_token_never_tries_json_encoding(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_id", "cid")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_secret", "csecret")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "tenant-1")

    encodings: list[str] = []

    def handler(url, **kwargs):
        if "files" in kwargs:
            encodings.append("multipart")
            return _DummyResponse(400, "The client_id field is required")
        if "data" in kwargs:
            encodings.append("form")
            return _DummyResponse(400, "The client_id field is required")
        if "json" in kwargs:
            encodings.append("json")
            return _DummyResponse(400, "nope")
        raise AssertionError(kwargs)

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: _DummyClient(handler))

    fetch = await oauth_mod.fetch_oauth_token_with_diagnosis()
    assert encodings == ["multipart", "form"]
    assert "json" not in encodings
    assert fetch.diagnosis["verdict"] == "request_not_bound"


@pytest.mark.asyncio
async def test_ping_401_points_at_tenant(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "")

    class PingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, headers=None):
            return _DummyResponse(401, {"message": "Unauthorized"})

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: PingClient())

    with pytest.raises(PlanviewAuthError) as exc:
        await ping_with_access_token("fresh-token")
    assert exc.value.code == "ping_unauthorized"
    assert "TENANT" in (exc.value.hint or "")


@pytest.mark.asyncio
async def test_connection_surfaces_all_attempts_and_prefers_credential_signal(monkeypatch):
    from planview_portfolios_mcp.tools import ping as ping_mod
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(
        ping_mod,
        "inspect_oauth_config",
        lambda: {
            "ok": True,
            "checks": [{"name": "api_url", "ok": True, "detail": "ok"}],
            "error": None,
            "token_url": "https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token",
            "ping_url": "https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/ping",
            "host": "scdemo508.pvcloud.com",
            "fingerprints": {"client_id": fingerprint("cid"), "tenant_id": fingerprint("t1")},
        },
    )

    async def fake_clear():
        return None

    async def fake_fetch():
        return oauth_mod.TokenFetchResult(
            token=None,
            token_url="https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token",
            attempts=[
                {
                    "encoding": "multipart",
                    "content_type_sent": "multipart/form-data",
                    "status_code": 401,
                    "classification": "credentials_rejected",
                    "body_preview": '{"error":"invalid_client"}',
                    "response_headers": {},
                    "credentials_evaluated": True,
                },
                {
                    "encoding": "form",
                    "content_type_sent": "application/x-www-form-urlencoded",
                    "status_code": 400,
                    "classification": "request_not_bound",
                    "body_preview": "The client_id, grant_type, and client_secret fields are required",
                    "response_headers": {},
                    "credentials_evaluated": False,
                },
            ],
            diagnosis=diagnose_token_attempts(
                [
                    {
                        "encoding": "multipart",
                        "status_code": 401,
                        "classification": "credentials_rejected",
                        "body_preview": '{"error":"invalid_client"}',
                    },
                    {
                        "encoding": "form",
                        "status_code": 400,
                        "classification": "request_not_bound",
                        "body_preview": "The client_id, grant_type, and client_secret fields are required",
                    },
                ],
                token_url="https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token",
            ),
        )

    monkeypatch.setattr(ping_mod, "clear_oauth_token", fake_clear)
    monkeypatch.setattr(ping_mod, "fetch_oauth_token_with_diagnosis", fake_fetch)

    result = await ping_mod.test_connection()
    assert result["ok"] is False
    assert len(result["token_attempts"]) == 2
    assert result["diagnosis"]["verdict"] == "credentials_rejected"
    assert result["diagnosis"]["primary_attempt"] == "multipart"
    assert "field-casing" in (result["diagnosis"].get("note") or "")
    assert "invalid_client" in result["diagnosis"]["planview_said"]
    assert "are required" not in result["diagnosis"]["summary"]
    assert result["diagnostic_bundle"]["token_attempts"]
    assert result["error"]["hint"]


@pytest.mark.asyncio
async def test_connection_returns_authenticated_as_on_success(monkeypatch):
    from planview_portfolios_mcp.tools import ping as ping_mod
    from planview_portfolios_mcp.oauth import OAuthToken, TokenFetchResult

    monkeypatch.setattr(
        ping_mod,
        "inspect_oauth_config",
        lambda: {
            "ok": True,
            "checks": [{"name": "api_url", "ok": True, "detail": "ok"}],
            "error": None,
            "token_url": "https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token",
            "ping_url": "https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/ping",
            "host": "scdemo508.pvcloud.com",
            "fingerprints": {
                "client_id": fingerprint("cid-123456"),
                "tenant_id": fingerprint("tenant-abcdef"),
            },
        },
    )
    monkeypatch.setattr(ping_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(ping_mod.settings, "planview_client_id", "cid-123456")
    monkeypatch.setattr(ping_mod.settings, "planview_tenant_id", "tenant-abcdef")

    async def fake_clear():
        return None

    async def fake_fetch():
        return TokenFetchResult(
            token=OAuthToken(
                access_token="abc",
                expires_at=datetime.now() + timedelta(hours=1),
                expires_in=3600,
                encoding="multipart",
            ),
            attempts=[
                {
                    "encoding": "multipart",
                    "status_code": 200,
                    "classification": "success",
                    "body_preview": "(token redacted)",
                    "credentials_evaluated": True,
                    "content_type_sent": "multipart/form-data",
                    "response_headers": {},
                    "access_token": fingerprint("abc", reveal=2),
                }
            ],
            diagnosis={"verdict": "ok", "summary": "ok", "primary_attempt": "multipart"},
            token_url="https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token",
        )

    async def fake_ping(access_token: str):
        assert access_token == "abc"
        return {"ok": True, "status_code": 200, "data": {"message": "pong"}, "body_preview": "pong"}

    monkeypatch.setattr(ping_mod, "clear_oauth_token", fake_clear)
    monkeypatch.setattr(ping_mod, "fetch_oauth_token_with_diagnosis", fake_fetch)
    monkeypatch.setattr(ping_mod, "ping_with_access_token", fake_ping)

    result = await ping_mod.test_connection()
    assert result["ok"] is True
    assert result["connected"] is True
    assert result["authenticated_as"]["host"] == "scdemo508.pvcloud.com"
    assert result["authenticated_as"]["encoding"] == "multipart"
    assert result["authenticated_as"]["client_id"]["sha256_8"]
    assert result["authenticated_as"]["tenant_id"]["suffix"] == "cdef"
    assert result["authenticated_as"]["access_token"]["set"] is True
    assert "abc" not in json.dumps(result["authenticated_as"]["access_token"])
    assert result["diagnosis"]["verdict"] == "ok"


@pytest.mark.asyncio
async def test_successful_token_body_masks_access_token(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_id", "cid")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_secret", "csecret")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "tenant-1")

    secret_token = "eyJhbGciOiJIUzI1NiJ9.payload.signature-secret"

    def handler(url, **kwargs):
        return _DummyResponse(
            200,
            {
                "access_token": secret_token,
                "token_type": "bearer",
                "expires_in": 3600,
            },
        )

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: _DummyClient(handler))

    fetch = await oauth_mod.fetch_oauth_token_with_diagnosis()
    assert fetch.token is not None
    assert fetch.token.access_token == secret_token
    preview = fetch.attempts[0]["body_preview"]
    assert secret_token not in preview
    assert "access_token" in preview
    assert fetch.attempts[0]["access_token"]["sha256_8"]
    assert secret_token not in json.dumps(fetch.attempts[0]["access_token"])
