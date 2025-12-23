"""Model helpers for Objectives."""
from http import HTTPStatus

from open_alchemy import models
from sqlalchemy import or_
from okrs_api.model_helpers.ca_configs import add_tenant_fields
from okrs_api.hasura.actions.service_wranglers import service_wrangler_factory
from okrs_api.utils import apply_inject


KEYRESULT_DB_FIELDS = [
    "name",
    "description",
    "data_source",
    "starts_at",
    "ends_at",
    "objective_id",
    "owned_by",
    "app_owned_by",
    "starting_value",
    "target_value",
    "value_type",
    "ca_config_id",
    "last_updated_by",
    "app_last_updated_by",
]


async def list_objective_key_results(db_session, input_prepper, objective_id):
    """List all key results for an objective."""

    async def fetch_activities(kr):
        return await get_key_result_activities(db_session, input_prepper, kr["id"])

    async def fetch_progress_points(kr):
        return await get_key_result_progress_points(db_session, kr["id"])

    all_key_results = await get_key_results_for_objective(db_session, objective_id)

    if input_prepper.input_parser.include_activities:
        all_key_results = await apply_inject(
            all_key_results, "activities", fetch_activities
        )

    if input_prepper.input_parser.include_progress_points:
        all_key_results = await apply_inject(
            all_key_results, "progress_points", fetch_progress_points
        )

    return all_key_results


async def get_key_results_for_objective(db_session, objective_id):
    """Get all key results for an objective."""

    key_results = (
        db_session.query(models.KeyResult)
        .filter(models.KeyResult.objective_id == objective_id)
        .filter(models.KeyResult.deleted_at_epoch == 0)
        .all()
    )

    return [kr.to_dict() for kr in key_results]


def get_work_item_mappings(
    db_session, tenant_id_str, tenant_group_id_str, app_name, key_result_id
):
    """Get list of activities for a key result."""

    available_work_items = (
        db_session.query(models.WorkItem)
        .filter(
            or_(
                models.WorkItem.tenant_group_id_str == tenant_group_id_str,
                models.WorkItem.tenant_id_str == tenant_id_str,
            )
        )
        .filter_by(app_name=app_name)
        .join(models.KeyResultWorkItemMapping)
        .filter(models.KeyResultWorkItemMapping.key_result_id == key_result_id)
        .all()
    )

    if not available_work_items:
        return [], []

    mappings = (
        db_session.query(models.KeyResultWorkItemMapping)
        .filter(models.KeyResultWorkItemMapping.key_result_id == key_result_id)
        .filter(
            or_(
                models.KeyResultWorkItemMapping.tenant_group_id_str
                == tenant_group_id_str,
                models.KeyResultWorkItemMapping.tenant_id_str == tenant_id_str,
            )
        )
        .filter(
            models.KeyResultWorkItemMapping.work_item_id.in_(
                [wi.id for wi in available_work_items]
            )
        )
        .all()
    )

    return available_work_items, mappings


async def get_key_result_activities(db_session, input_prepper, kr_id):
    """Get all activities for a key result."""
    tenant_id_str = input_prepper.org_id
    tenant_group_id_str = input_prepper.tenant_group_id
    app_name = input_prepper.app_name

    available_work_items, mappings = get_work_item_mappings(
        db_session,
        tenant_id_str,
        tenant_group_id_str,
        app_name,
        kr_id,
    )

    if available_work_items:
        activity_ids = [wi.external_id for wi in available_work_items]
        input_prepper.input_parser.activity_ids = activity_ids
        wrangler = service_wrangler_factory(
            input_prepper, override_action="list_activities"
        )
        api_response_data, api_response_status = await wrangler.call_service()
        work_items = {
            wi.id: (
                wi.external_id,
                {
                    "id": wi.work_item_container.id,
                    "external_id": wi.work_item_container.external_id,
                    "external_title": wi.work_item_container.external_title,
                },
            )
            for wi in available_work_items
        }

        key_results_wi_mapping = {
            mapping.work_item_id: mapping.id for mapping in mappings
        }

        if api_response_status == HTTPStatus.OK:
            external_id_map = {
                response["external_id"]: response for response in api_response_data
            }
            mapped_response_data = list(
                map(
                    lambda wiid: {
                        "id": wiid,
                        "work_item_container": work_items[wiid][1],
                    }
                    | external_id_map[work_items[wiid][0]]
                    if work_items[wiid][0] in external_id_map
                    else None,
                    work_items,
                )
            )
            api_response_data = [
                data for data in mapped_response_data if data is not None
            ]

            api_response_data = [
                data
                | {
                    "key_result_work_item_mapping_id": key_results_wi_mapping.get(
                        data["id"]
                    )
                }
                for data in api_response_data
            ]
            return api_response_data
    return []


async def get_key_result_progress_points(db_session, key_result_id):
    """Get the progress points for a key result."""

    progress_points = (
        db_session.query(models.ProgressPoint)
        .filter(models.ProgressPoint.key_result_id == key_result_id)
        .filter(models.ProgressPoint.deleted_at_epoch == 0)
        .all()
    )

    return [progress.to_dict() for progress in progress_points]


def create_new_keyresult(db_session, input_prepper, data):
    """Create New Key result with Custom Attributes."""
    params = {k: data[k] for k in data.keys() if k in KEYRESULT_DB_FIELDS}
    add_tenant_fields(params, input_prepper)
    key_result = models.KeyResult(**params)
    db_session.add(key_result)
    db_session.flush()
    return key_result


def fetch_key_result(db_session, input_prepper):
    """Retrieve Key Result from DB by ID."""

    data = db_session.query(models.KeyResult).get(input_prepper.input_parser.id)

    return data


def get_by_id_and_tenant(db_session, key_result_id, tenant_group_id, org_id):
    """Retrieve Key Result from DB by id, tenant_group_id and tenant_id."""
    key_result = (
        db_session.query(models.KeyResult)
        .filter(
            or_(
                models.KeyResult.tenant_group_id_str == tenant_group_id,
                models.KeyResult.tenant_id_str == org_id,
            )
        )
        .filter_by(
            id=key_result_id,
            deleted_at_epoch=0,
        )
        .first()
    )
    return key_result


def get_key_result_targets(db_session, objective_id):
    """Retrieve Key Result Targets from DB by objective_id."""
    key_result_targets = (
        db_session.query(models.KeyResult, models.Target)
        .outerjoin(
            models.Target,
            (models.KeyResult.id == models.Target.key_result_id)
            & (models.Target.is_deleted.is_(False)),
        )
        .filter(models.KeyResult.objective_id == objective_id)
        .filter(models.KeyResult.deleted_at_epoch == 0)
        .all()
    )
    return key_result_targets


def has_date_range_shortened(previous_starts_at, previous_ends_at, starts_at, ends_at):
    """Check if an object's date range is getting shortened."""
    if previous_starts_at >= starts_at and previous_ends_at <= ends_at:
        return False
    return True


def update_keyresult_target_dates(db_session, key_result_targets, starts_at, ends_at):
    """Update key result target dates."""
    for key_result, target in key_result_targets:
        if has_date_range_shortened(
            key_result.starts_at, key_result.ends_at, starts_at, ends_at
        ):
            if (
                key_result.starts_at < starts_at and key_result.ends_at < starts_at
            ) or (key_result.starts_at > ends_at and key_result.ends_at > ends_at):
                key_result.starts_at = starts_at
                key_result.ends_at = ends_at
                if target:
                    target.starts_at = starts_at
                    target.ends_at = ends_at
            if key_result.starts_at < starts_at:
                key_result.starts_at = starts_at
                if target:
                    target.starts_at = starts_at
            if key_result.ends_at > ends_at:
                key_result.ends_at = ends_at
                if target:
                    target.ends_at = ends_at
            db_session.add(key_result)
            if target:
                db_session.add(target)


def validate_objective_and_update_kr_daterange(
    objective_id, previous_starts_at, previous_ends_at, starts_at, ends_at, db_session
):
    """Validate objective's new date range and update key result targets."""
    has_shortened = has_date_range_shortened(
        previous_starts_at, previous_ends_at, starts_at, ends_at
    )
    if not has_shortened:
        return None
    key_result_targets = get_key_result_targets(db_session, objective_id)
    if not key_result_targets:
        return None

    key_result_ids = set()
    multi_target_key_result_ids = set()
    for _, target in key_result_targets:
        if target:
            if target.key_result_id in key_result_ids:
                multi_target_key_result_ids.add(target.key_result_id)
            key_result_ids.add(target.key_result_id)

    need_update = False
    for key_result, _ in key_result_targets:
        if has_date_range_shortened(
            key_result.starts_at, key_result.ends_at, starts_at, ends_at
        ):
            need_update = True
            if key_result.id in multi_target_key_result_ids:
                return "MULTIPLE_TARGETS_FOUND"
    if not need_update:
        return None

    update_keyresult_target_dates(db_session, key_result_targets, starts_at, ends_at)
    db_session.flush()
    return None
