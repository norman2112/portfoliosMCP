"""Unit tests for financial-plan upsert normalization and discover key lists."""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

fp = importlib.import_module("planview_portfolios_mcp.tools.financial_plan")
manage_fp = importlib.import_module("planview_portfolios_mcp.tools.manage_financial_plan")
manage_project = importlib.import_module("planview_portfolios_mcp.tools.manage_project")
from planview_portfolios_mcp.exceptions import PlanviewValidationError


def test_normalize_upsert_accepts_soap_line_envelope():
    nested = {
        "EntityKey": "key://2/$Plan/1",
        "VersionKey": "key://14/1",
        "Lines": {
            "FinancialPlanLineDto": [
                {
                    "AccountKey": "key://2/$Account/A",
                    "Unit": "Currency",
                    "Entries": {
                        "EntryDto": [{"PeriodKey": "key://16/1", "Value": 10}]
                    },
                }
            ]
        },
    }
    flat = fp._normalize_upsert_plan_data(nested)
    assert isinstance(flat["Lines"], list)
    assert flat["Lines"][0]["AccountKey"] == "key://2/$Account/A"
    assert isinstance(flat["Lines"][0]["Entries"], list)
    assert flat["Lines"][0]["Entries"][0]["PeriodKey"] == "key://16/1"


def test_normalize_upsert_unwraps_read_response_wrapper():
    wrapped = {
        "success": True,
        "action": "read",
        "data": {
            "EntityKey": "key://2/$Plan/1",
            "VersionKey": "key://14/1",
            "Lines": [
                {
                    "AccountKey": "key://2/$Account/A",
                    "Unit": "Currency",
                    "Entries": [{"PeriodKey": "key://16/1", "Value": 5}],
                }
            ],
        },
    }
    flat = fp._normalize_upsert_plan_data(wrapped)
    assert flat["EntityKey"] == "key://2/$Plan/1"
    assert flat["Lines"][0]["Entries"][0]["Value"] == 5


def test_normalize_upsert_rejects_missing_entries_clearly():
    with pytest.raises(PlanviewValidationError, match="include_entries"):
        fp._normalize_upsert_plan_data(
            {
                "EntityKey": "key://2/$Plan/1",
                "VersionKey": "key://14/1",
                "Lines": [{"AccountKey": "key://2/$Account/A", "Unit": "Currency"}],
            }
        )


def test_extract_account_and_period_keys_from_lines_and_periods():
    data = {
        "Lines": {
            "FinancialPlanLineDto": [
                {
                    "AccountKey": "key://2/$Account/A",
                    "AccountDescription": "Benefits",
                    "Entries": [{"PeriodKey": "key://16/9", "Value": 1}],
                }
            ]
        },
        "Periods": [
            {"PeriodKey": "key://16/10", "Description": "Sep 2025"},
            {"PeriodKey": "key://16/183", "Description": "Aug 2026"},
        ],
    }
    accounts, periods = fp._extract_labeled_accounts_and_periods(data)
    assert accounts == [{"key": "key://2/$Account/A", "description": "Benefits"}]
    # Numeric sort: 9 before 10 before 183
    assert [p["key"] for p in periods] == [
        "key://16/9",
        "key://16/10",
        "key://16/183",
    ]
    assert periods[2]["description"] == "Aug 2026"
    bare_a, bare_p = fp._extract_account_and_period_keys(data)
    assert bare_a == ["key://2/$Account/A"]
    assert bare_p == ["key://16/9", "key://16/10", "key://16/183"]


def test_annotate_discovery_sets_source_and_keys():
    result = {
        "success": True,
        "data": {
            "Lines": {
                "FinancialPlanLineDto": [
                    {
                        "AccountKey": "key://2/$Account/A",
                        "AccountDescription": "Labor",
                        "Entries": [{"PeriodKey": "key://16/1", "Value": 1}],
                    }
                ]
            },
            "Periods": [{"PeriodKey": "key://16/1", "Description": "Jan 2025"}],
        },
    }
    out = fp._annotate_discovery_result(
        result,
        source="reference",
        target_entity_key="key://2/$Plan/TARGET",
        version_key="key://14/1",
        reference_entity_key="key://2/$Plan/REF",
    )
    assert out["source"] == "reference"
    assert out["data"]["Source"] == "reference"
    assert out["data"]["EntityKey"] == "key://2/$Plan/TARGET"
    assert out["data"]["account_keys"] == ["key://2/$Account/A"]
    assert out["data"]["period_keys"] == ["key://16/1"]
    assert out["data"]["periods"] == [
        {"key": "key://16/1", "description": "Jan 2025"}
    ]
    assert out["data"]["accounts"][0]["description"] == "Labor"
    assert "fiscal" in (out["data"].get("period_keys_note") or "").lower()
    assert "reference" in (out.get("hint") or "").lower()


def test_config_periods_become_labeled():
    data = {
        "Accounts": {"benefits": {"key": "key://2/$Account/1", "description": "Benefits"}},
        "Periods": {"dec_2025": "key://16/170"},
    }
    accounts, periods = fp._extract_labeled_accounts_and_periods(data)
    assert accounts == [{"key": "key://2/$Account/1", "description": "Benefits"}]
    assert periods == [{"key": "key://16/170", "description": "dec_2025"}]


@pytest.mark.asyncio
async def test_manage_financial_plan_discover_surfaces_keys(monkeypatch):
    async def fake_discover(**kwargs):
        return {
            "success": True,
            "source": "reference",
            "data": {
                "EntityKey": "key://2/$Plan/T",
                "VersionKey": "key://14/1",
                "Source": "reference",
                "account_keys": ["key://2/$Account/A"],
                "period_keys": ["key://16/1"],
            },
        }

    monkeypatch.setattr(manage_fp, "discover_financial_plan_info", fake_discover)
    result = await manage_fp.manage_financial_plan(
        action="discover",
        project_id="1",
        reference_project_id="2",
    )
    assert result["upsert_ready"] is True
    assert result["data"]["period_keys"] == ["key://16/1"]


@pytest.mark.asyncio
async def test_manage_project_create_promotes_warnings(monkeypatch):
    async def fake_create(data, attributes=None, create_default_tasks=False):
        return {
            "data": [{"structureCode": "999", "description": data["description"]}],
            "meta": {
                "warnings": [
                    {"codeDesc": "InvalidDefaultValues", "message": "Wbs37 default invalid"}
                ]
            },
        }

    monkeypatch.setattr(manage_project, "create_project", fake_create)
    result = await manage_project.manage_project(
        action="create",
        data={"description": "Test", "parent": {"structureCode": "14170"}},
    )
    assert result["has_warnings"] is True
    assert result["create_ok"] is True
    assert result["demo_safe"] is True
    assert result["warnings"][0]["codeDesc"] == "InvalidDefaultValues"
    assert "succeeded" in result["warning_hint"].lower()
    assert "not required" in result["warning_hint"].lower() or "optional" in result["warning_hint"].lower()
