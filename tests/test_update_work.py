import pytest

import sys
from pathlib import Path

# Ensure `src/` is on the import path when running tests from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.mark.asyncio
async def test_update_work_calls_patch(monkeypatch):
    from planview_portfolios_mcp.tools import work as work_mod
    from contextlib import asynccontextmanager

    calls = []

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    async def mock_make_request(client, method, url, **kwargs):
        calls.append(
            {
                "method": method,
                "url": url,
                "kwargs": kwargs,
            }
        )
        return DummyResp({"ok": True})

    class DummyClient:
        pass

    @asynccontextmanager
    async def mock_get_client():
        yield DummyClient()

    # Patch get_client and make_request used by update_work.
    monkeypatch.setattr(work_mod, "make_request", mock_make_request)
    monkeypatch.setattr(work_mod, "get_client", mock_get_client)

    result = await work_mod.update_work(
        work_id="123",
        updates={"ExecType": {"structureCode": "6354|Project"}},
        attributes=["Description"],
    )

    assert result == {"ok": True}
    assert len(calls) == 1
    assert calls[0]["method"] == "PATCH"
    assert calls[0]["url"] == "/public-api/v1/work/123"
    assert calls[0]["kwargs"]["json"] == {"ExecType": {"structureCode": "6354|Project"}}
    assert calls[0]["kwargs"]["params"]["attributes"] == "Description"


@pytest.mark.asyncio
async def test_update_work_blocks_field_identification(monkeypatch):
    from planview_portfolios_mcp.tools import work as work_mod
    from planview_portfolios_mcp.exceptions import PlanviewValidationError
    from contextlib import asynccontextmanager

    attempts = []

    class DummyResp:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

    async def mock_make_request(client, method, url, **kwargs):
        json_payload = kwargs.get("json") or {}
        attempts.append(json_payload)

        # Initial call with multi-field payload fails.
        if set(json_payload.keys()) == {"ExecType", "OtherField"}:
            raise PlanviewValidationError("Invalid request: ExecType is lifecycle-controlled")

        # Isolated calls:
        if "ExecType" in json_payload:
            raise PlanviewValidationError("Invalid request: ExecType is lifecycle-controlled")
        if "OtherField" in json_payload:
            return DummyResp({"ok": True})

        raise PlanviewValidationError("Unexpected payload")

    class DummyClient:
        pass

    @asynccontextmanager
    async def mock_get_client():
        yield DummyClient()

    monkeypatch.setattr(work_mod, "make_request", mock_make_request)
    monkeypatch.setattr(work_mod, "get_client", mock_get_client)

    with pytest.raises(PlanviewValidationError) as excinfo:
        await work_mod.update_work(
            work_id="123",
            updates={"ExecType": {"structureCode": "6354|Project"}, "OtherField": {"structureCode": "X|Y"}},
        )

    msg = str(excinfo.value)
    assert "ExecType" in msg
    # First attempt + 2 isolated attempts.
    assert len(attempts) == 3

