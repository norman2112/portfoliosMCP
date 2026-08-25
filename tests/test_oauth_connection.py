import json

import httpx
import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from planview_portfolios_mcp.config import normalize_planview_api_url
from planview_portfolios_mcp.exceptions import PlanviewAuthError
from planview_portfolios_mcp.oauth import inspect_oauth_config, ping_with_access_token


def test_normalize_lowercases_host_and_strips_slash():
    assert (
        normalize_planview_api_url(" HTTPS://SCDEMO508.pvcloud.com/polaris/ ")
        == "https://scdemo508.pvcloud.com/polaris"
    )


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


@pytest.mark.asyncio
async def test_token_falls_back_from_multipart_to_form(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_id", "cid")
    monkeypatch.setattr(oauth_mod.settings, "planview_client_secret", "csecret")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "tenant-1")

    calls: list[str] = []

    class DummyResponse:
        def __init__(self, status_code: int, payload: dict | None = None):
            self.status_code = status_code
            self._payload = payload or {}
            self.text = json.dumps(self._payload)
            self.request = httpx.Request("POST", "https://scdemo508.pvcloud.com/polaris/public-api/v1/oauth/token")

        def json(self):
            return self._payload

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, **kwargs):
            if "files" in kwargs:
                calls.append("multipart")
                return DummyResponse(400, {"error": "invalid_request"})
            if "data" in kwargs:
                calls.append("form")
                return DummyResponse(
                    200,
                    {"access_token": "tok-form", "token_type": "bearer", "expires_in": 3600},
                )
            calls.append("json")
            return DummyResponse(400, {"error": "nope"})

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: DummyClient())

    await oauth_mod.clear_oauth_token()
    token = await oauth_mod.get_oauth_token_record(force_refresh=True)
    assert token.access_token == "tok-form"
    assert token.encoding == "form"
    assert calls == ["multipart", "form"]


@pytest.mark.asyncio
async def test_ping_401_points_at_tenant(monkeypatch):
    from planview_portfolios_mcp import oauth as oauth_mod

    monkeypatch.setattr(oauth_mod.settings, "planview_api_url", "https://scdemo508.pvcloud.com/polaris")
    monkeypatch.setattr(oauth_mod.settings, "planview_tenant_id", "")

    class DummyResponse:
        status_code = 401
        text = '{"message":"Unauthorized"}'
        headers = {"content-type": "application/json"}

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url, headers=None):
            return DummyResponse()

    monkeypatch.setattr(oauth_mod.httpx, "AsyncClient", lambda **kwargs: DummyClient())

    with pytest.raises(PlanviewAuthError) as exc:
        await ping_with_access_token("fresh-token")
    assert exc.value.code == "ping_unauthorized"
    assert "TENANT" in (exc.value.hint or "")


@pytest.mark.asyncio
async def test_connection_returns_structured_success(monkeypatch):
    from planview_portfolios_mcp.tools import ping as ping_mod
    from planview_portfolios_mcp.oauth import OAuthToken
    from datetime import datetime, timedelta

    monkeypatch.setattr(
        ping_mod,
        "inspect_oauth_config",
        lambda: {
            "ok": True,
            "checks": [{"name": "api_url", "ok": True, "detail": "ok"}],
            "error": None,
            "token_url": "https://example/public-api/v1/oauth/token",
            "ping_url": "https://example/public-api/v1/oauth/ping",
            "host": "example",
        },
    )

    async def fake_token(force_refresh: bool = False):
        return OAuthToken(
            access_token="abc",
            expires_at=datetime.now() + timedelta(hours=1),
            expires_in=3600,
            encoding="multipart",
        )

    async def fake_ping(access_token: str):
        assert access_token == "abc"
        return {"ok": True, "status_code": 200, "data": {"message": "pong"}}

    monkeypatch.setattr(ping_mod, "get_oauth_token_record", fake_token)
    monkeypatch.setattr(ping_mod, "ping_with_access_token", fake_ping)

    result = await ping_mod.test_connection()
    assert result["ok"] is True
    assert result["connected"] is True
    names = [c["name"] for c in result["checks"]]
    assert "token" in names
    assert "ping" in names
