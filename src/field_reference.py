"""
Curated Portfolios project field reference for MCP tool descriptions.

Source: GET /public-api/v1/projects/attributes/available on a Planview instance
Total: 779 attributes (427 writable, 352 system-controlled)
This module exports only the ~120 demo-relevant writable fields, organized by category.

IMPORTANT: StructureCode fields use format "code|description" (e.g., "2170|Green").
The code is what gets sent in the PATCH; the description is human-readable.

Create Parent is the work-hierarchy PPL-1 folder, copied from the Planview UI.
This catalog cannot enumerate $Plan parents. Strategy hierarchy ($Strategy) is out of scope.

Catalog StructureCode defaults were removed: demo-tenant codes (region/RAG/status)
caused InvalidDefaultValues on create when agents sent them. Omit StructureCode
attributes on create unless the code is verified for the target tenant.
"""

from __future__ import annotations


# Categories map field_id -> (human_title, type, example_or_None, ppl_only)
# example_or_None is intentionally unused for StructureCodes (tenant-specific).
# ppl_only = True means the field is only available at Primary Planning Level (projects), not sub-tasks
FIELD_CATEGORIES: dict[str, dict[str, tuple[str, str, object | None, bool]] | dict[str, str]] = {
    "core_identity": {
        "_description": "Basic project identity fields",
        "Description": ("Work Name", "Text", None, False),  # max 50 chars
        "ShortName": ("Work ID #", "Text", None, True),  # max 12 chars
        "Parent": ("Parent (work hierarchy PPL-1; copy structure code from Planview UI)", "StructureCode", None, False),
        "Status": ("Work Status", "StructureCode", None, False),
    },
    "dates": {
        "_description": "Schedule and actual date fields. DateTime format: ISO 8601",
        "ScheduleStart": ("Schedule Start", "DateTime", None, False),
        "ScheduleFinish": ("Schedule Finish", "DateTime", None, False),
        "ActualStart": ("Actual Start", "DateTime", None, False),
        "ActualFinish": ("Actual Finish", "DateTime", None, False),
        "RequestedStart": ("Requested Start", "DateTime", None, True),
        "RequestedFinish": ("Requested Finish", "DateTime", None, True),
    },
    "progress": {
        "_description": "Progress tracking fields",
        "PERCENT_COMPLETE": ("Percent Complete", "Integer", None, False),  # 0-100
        "POINTS_EARNED": ("Story Points Earned", "Real", None, False),
        "POINTS_PLANNED": ("Story Points Planned", "Real", None, False),
        "EnterStatus": ("Enter Status Flag", "Boolean", None, False),
        "ProgressAsPlanned": ("Progress As Planned", "Boolean", None, False),
    },
    "status_assessments": {
        "_description": "RAG status assessments. Values: Green, Yellow, Red (use structureCode|label format)",
        "Wbs709": ("Overall Status Assessment", "StructureCode", None, True),
        "Wbs722": ("Schedule Status Assessment", "StructureCode", None, True),
        "Wbs721": ("Cost Status Assessment", "StructureCode", None, True),
        "Wbs723": ("Resourcing Status Assessment", "StructureCode", None, True),
        "Wbs724": ("Quality Status Assessment", "StructureCode", None, True),
        "Wbs725": ("Benefit Status Assessment", "StructureCode", None, True),
        "Wbs726": ("Scope Status Assessment", "StructureCode", None, True),
        "Wbs9": ("Manager Assessment", "StructureCode", None, True),
    },
    "investment_scoring": {
        "_description": "Investment approval and scoring fields (PPL only)",
        "ProductInvestmentApproval": (
            "Investment Approval",
            "StructureCode",
            None,
            True,
        ),
        "Wbs27": ("Investment Status", "StructureCode", None, True),
        "Wbs59": ("Investment Category", "StructureCode", None, True),
        "score1": ("Investment Priority Score", "Real", None, True),
        "score2": ("Investment Risk Score", "Real", None, True),
        "score3": ("Preliminary Score", "Real", None, True),
    },
    "strategic_classification": {
        "_description": (
            "Strategic alignment fields on a project. $Strategy is a writable "
            "attribute only if you already have codes — this MCP cannot browse "
            "the strategy hierarchy (out of scope; use Anvi Prod)."
        ),
        "$Strategy": ("Strategic Hierarchy (out of scope to enumerate; Anvi Prod)", "MultiStructureCode", None, True),
        "Wbs7": ("Strategic Alignment", "StructureCode", None, True),
        "Str35": ("RGT Type (Run/Grow/Transform)", "StructureCode", None, False),
        "Str34": ("Theme", "StructureCode", None, False),
        "Wbs713": ("Line of Business", "StructureCode", None, True),
        "Wbs37": ("Region (optional; unset is fine for demos)", "StructureCode", None, True),
        "Wbs58": ("Service Line", "StructureCode", None, True),
        "ExecType": ("Execution Type", "StructureCode", None, False),
        "Wbs22": ("Work Type", "StructureCode", None, False),
        "Wbs29": ("Execution Stage", "StructureCode", None, False),
    },
    "wsjf_safe": {
        "_description": "WSJF/SAFe prioritization fields. Fields marked NO_EDIT are read-only in UI but technically writable via API",
        "Wbs30": ("User Business Value", "StructureCode", None, False),  # editFeature=$None
        "Wbs31": ("Time Criticality", "StructureCode", None, False),  # editFeature=$None
        "Wbs32": ("RR | OE Value", "StructureCode", None, False),  # editFeature=$None
        "Wbs33": ("Job Size", "StructureCode", None, False),  # editFeature=$None
        "Wbs82": (
            "Time Criticality (Dynamic Planning)",
            "StructureCode",
            None,
            True,
        ),
        "wsjfcodf": ("WSJF Cost of Delay", "Real", None, True),  # editFeature=$None
        "wsjff": ("WSJF Score", "Real", None, True),  # editFeature=$None
    },
    "risk": {
        "_description": "Risk and complexity assessments",
        "Wbs708": ("Work Risk", "StructureCode", None, False),
        "Wbs711": ("Work Complexity", "StructureCode", None, True),
        "Wbs69": ("Technical Risk", "StructureCode", None, False),
        "Wbs77": ("Business Risk", "StructureCode", None, True),
    },
    "business_case_text": {
        "_description": "Long text fields for business case documentation",
        "PE01": ("Description (Long)", "LongText", None, False),
        "PE02": ("Business Opportunity", "LongText", None, False),
        "rpm_benef_anticipate": ("Benefits Anticipated", "LongText", None, False),
        "rpm_risk_not_proceed": ("Risk of not Proceeding", "LongText", None, False),
        "rpm_scop_deliv_depen": ("Scope, Deliverables and Dependencies", "LongText", None, False),
        "rpm_align_with_strat": ("Alignment with Strategic Plan", "LongText", None, False),
        "rpm_key_actual": ("Key Accomplishments This Period", "LongText", None, False),
        "rpm_key_planned": ("Planned Activities Next Period", "LongText", None, False),
        "work_results_hypo": ("Results Hypothesis", "LongText", None, False),
    },
    "lifecycle_roles": {
        "_description": "Lifecycle role assignments (user references)",
        "LC_ROLE2268": ("Project Manager", "LcRole", None, False),
        "LC_ROLE2269": ("Project Sponsor", "LcRole", None, False),
        "LC_ROLE2270": ("Outcome Manager", "LcRole", None, False),
        "LC_ROLE2271": ("Gate Keeper", "LcRole", None, False),
        "LC_ROLE2272": ("PMO", "LcRole", None, False),
        "LC_ROLE2273": ("Program Manager", "LcRole", None, False),
        "LC_ROLE5713": ("Initiative Owner", "LcRole", None, False),
    },
    "financial_metrics": {
        "_description": "Writable financial metric fields (PPL only). Note: computed financial plan rollups (1001-1206) are READ-ONLY",
        "actual_dollars_saved": ("Actual Dollars Saved", "Currency", None, True),
        "proj_dollars_saved": ("Projected Dollars Saved", "Currency", None, True),
        "actual_revenue_saved": ("Actual Revenue Saved", "Currency", None, True),
        "proj_revenue_saved": ("Projected Revenue Saved", "Currency", None, True),
        "actual_headcount_sav": ("Actual Headcount Saved", "Real", None, True),
        "proj_headcount_saved": ("Projected Headcount Saved", "Real", None, True),
    },
    "agileplace_integration": {
        "_description": "AgilePlace (LeanKit) integration sync fields",
        "LK_CARD_SIZE": ("AgilePlace Card Size", "Integer", None, False),
        "LK_CARD_TYPE": ("Card Type", "Text", None, False),
        "LK_PRIORITY": ("Priority", "Text", None, False),
        "LK_LANE_CLASS": ("Card Lane Status", "Text", None, False),
        "LK_TOP_LANE": ("Top Lane", "Text", None, False),
        "LK_CRDS_TOTAL": ("AgilePlace Cards (Total)", "Integer", None, False),
        "LK_CRDS_COMPLETE": ("Complete Cards", "Integer", None, False),
        "LK_CRDS_IN_PROGRESS": ("In Progress Child Cards", "Integer", None, False),
        "LK_CRDS_NOT_STARTED": ("Not Started Child Cards", "Integer", None, False),
        "LK_CRDS_PCT_CMPLT": ("AgilePlace Percent Complete", "Integer", None, False),
        "LKBoard": ("Kanban Board", "StructureCode", None, False),
        "lk_sync_work": ("Sync with AgilePlace", "Boolean", None, False),
    },
    "swot": {
        "_description": "SWOT analysis text fields",
        "workstrengths": ("Projected Strengths", "LongText", None, False),
        "workweaknesses": ("Projected Weaknesses", "LongText", None, False),
        "workopps": ("Projected Opportunities", "LongText", None, False),
        "workthreats": ("Projected Threats", "LongText", None, False),
    },
}


def get_all_writable_field_ids() -> set[str]:
    """Return set of all curated writable field IDs."""

    ids: set[str] = set()
    for cat_fields in FIELD_CATEGORIES.values():
        for key in cat_fields:
            if not key.startswith("_"):
                ids.add(key)
    return ids


def get_field_info(field_id: str) -> dict[str, object] | None:
    """Look up a field by ID. Returns dict with title, type, example, ppl_only, category."""

    for cat_name, cat_fields in FIELD_CATEGORIES.items():
        if field_id in cat_fields and not field_id.startswith("_"):
            # type: ignore[assignment]
            title, ftype, example, ppl_only = cat_fields[field_id]
            return {
                "id": field_id,
                "title": title,
                "type": ftype,
                "example": example,
                "ppl_only": ppl_only,
                "category": cat_name,
            }
    return None


def get_fields_by_category(category: str) -> dict[str, tuple[str, str, object | None, bool]]:
    """Get all fields in a category. Returns {field_id: (title, type, example, ppl_only)}."""

    cat = FIELD_CATEGORIES.get(category, {})  # type: ignore[assignment]
    if not isinstance(cat, dict):
        return {}

    out: dict[str, tuple[str, str, object | None, bool]] = {}
    for k, v in cat.items():
        if k.startswith("_"):
            continue
        # type: ignore[assignment]
        out[k] = v
    return out


def build_tool_description_appendix() -> str:
    """
    Build a compact field reference string suitable for embedding in MCP tool descriptions.
    This gets appended to update_project and create_project tool descriptions so the AI
    caller knows exactly which fields to use without calling get_project_attributes.
    """

    lines: list[str] = ["\n\nCURATED FIELD REFERENCE (writable fields organized by category):"]
    lines.append(
        'Work-hierarchy Parent (create): copy structureCode from the Planview UI (PPL-1). '
        "This MCP cannot list $Plan parents. Strategy hierarchy ($Strategy) is out of scope."
    )
    lines.append(
        'StructureCode format: send {"structureCode": "CODE", "description": "LABEL"} or just {"structureCode": "CODE"}'
    )
    lines.append(
        "Do not invent StructureCode values on create — omit them or verify against the tenant."
    )
    lines.append("")

    for cat_name, cat_fields in FIELD_CATEGORIES.items():
        # type: ignore[index]
        desc = cat_fields.get("_description", "")  # type: ignore[attr-defined]
        lines.append(f"[{cat_name}] {desc}")

        field_items = [(fid, info) for fid, info in cat_fields.items() if not fid.startswith("_")]
        for field_id, (title, ftype, _example, ppl_only) in sorted(field_items, key=lambda x: x[0]):
            parts = [f"  {field_id}: {title} ({ftype})"]
            if ppl_only:
                parts.append("PPL-only")
            lines.append(" | ".join(parts))
        lines.append("")

    return "\n".join(lines)

