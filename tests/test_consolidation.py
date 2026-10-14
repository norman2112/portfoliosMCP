import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from planview_portfolios_mcp.exceptions import PlanviewValidationError
from planview_portfolios_mcp.utils.key_uri import mint_task_ekey, plan_entity_key
from planview_portfolios_mcp.tool_registry import TOOL_NAMES
from planview_portfolios_mcp import tools as tools_pkg

manage_project_mod = importlib.import_module("planview_portfolios_mcp.tools.manage_project")
inspect_work_mod = importlib.import_module("planview_portfolios_mcp.tools.inspect_work")
manage_tasks_mod = importlib.import_module("planview_portfolios_mcp.tools.manage_tasks")
manage_fp_mod = importlib.import_module("planview_portfolios_mcp.tools.manage_financial_plan")


def test_registry_is_five_job_tools():
    assert TOOL_NAMES == [
        "test_connection",
        "manage_project",
        "inspect_work",
        "manage_tasks",
        "manage_financial_plan",
    ]
    assert all(hasattr(tools_pkg, name) for name in TOOL_NAMES)


def test_plan_entity_key_mints_and_passthrough():
    assert plan_entity_key("17286") == "key://2/$Plan/17286"
    assert plan_entity_key("key://2/$Plan/17286") == "key://2/$Plan/17286"
    assert mint_task_ekey().startswith("ekey://2/mcp/")


@pytest.mark.asyncio
async def test_manage_project_rejects_unknown_action():
    with pytest.raises(PlanviewValidationError, match="action must be one of"):
        await manage_project_mod.manage_project(action="list")


@pytest.mark.asyncio
async def test_manage_project_create_requires_data():
    with pytest.raises(PlanviewValidationError, match="requires data"):
        await manage_project_mod.manage_project(action="create")


@pytest.mark.asyncio
async def test_manage_project_create_requires_parent_from_ui():
    with pytest.raises(PlanviewValidationError, match="Planview UI"):
        await manage_project_mod.manage_project(
            action="create",
            data={"description": "Test 1001"},
        )


@pytest.mark.asyncio
async def test_manage_project_get_dispatches(monkeypatch):
    async def fake_get(project_id, attributes=None):
        return {"id": project_id, "attributes": attributes}

    monkeypatch.setattr(manage_project_mod, "get_project", fake_get)
    result = await manage_project_mod.manage_project(action="get", project_id="3818")
    assert result["id"] == "3818"


@pytest.mark.asyncio
async def test_inspect_work_list_builds_filter_from_project_id(monkeypatch):
    captured = {}

    async def fake_list(filter, attributes=None, fields=None):
        captured["filter"] = filter
        return {"data": []}

    monkeypatch.setattr(inspect_work_mod, "list_work", fake_list)
    await inspect_work_mod.inspect_work(action="list", project_id="3818")
    assert captured["filter"] == "project.Id .eq 3818"


@pytest.mark.asyncio
async def test_inspect_work_defaults_to_wbs(monkeypatch):
    async def fake_wbs(project_id, include_milestones=True, max_depth=None):
        return {"project_id": project_id}

    monkeypatch.setattr(inspect_work_mod, "get_project_wbs", fake_wbs)
    result = await inspect_work_mod.inspect_work(project_id="3818")
    assert result["project_id"] == "3818"


@pytest.mark.asyncio
async def test_manage_tasks_create_fills_father_and_ekey(monkeypatch):
    captured = {}

    async def fake_batch(tasks, options=None):
        captured["tasks"] = tasks
        return {
            "success": True,
            "created": [{"description": "T", "key": tasks[0]["Key"], "status": "success"}],
            "summary": {"total": 1, "succeeded": 1, "failed": 0},
            "warnings": [],
        }

    monkeypatch.setattr(manage_tasks_mod, "batch_create_tasks", fake_batch)
    result = await manage_tasks_mod.manage_tasks(
        action="create",
        project_id="17286",
        tasks=[{"Description": "Kickoff"}],
    )
    task = captured["tasks"][0]
    assert task["FatherKey"] == "key://2/$Plan/17286"
    assert str(task["Key"]).startswith("ekey://2/")
    assert result["action"] == "create"
    assert result.get("partial") is not True


@pytest.mark.asyncio
async def test_manage_financial_plan_read_mints_entity_key(monkeypatch):
    captured = {}

    async def fake_read(entity_key, version_key, include_entries=False, summary=False, fields=None):
        captured["entity_key"] = entity_key
        captured["version_key"] = version_key
        return {"success": True, "data": {}}

    monkeypatch.setattr(manage_fp_mod, "read_financial_plan", fake_read)
    result = await manage_fp_mod.manage_financial_plan(action="read", project_id="17286")
    assert captured["entity_key"] == "key://2/$Plan/17286"
    assert captured["version_key"] == "key://14/1"
    assert result["echo_incomplete_is_normal"] is True
