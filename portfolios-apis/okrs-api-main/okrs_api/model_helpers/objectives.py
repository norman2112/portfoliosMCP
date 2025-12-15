"""Model helpers for Objectives."""
from http import HTTPStatus
from datetime import datetime, timezone

from open_alchemy import models
from sqlalchemy import or_, and_

from okrs_api.hasura.actions.service_wranglers import service_wrangler_factory
from okrs_api.model_helpers.common import commit_db_session
from okrs_api.model_helpers.key_results import list_objective_key_results
from okrs_api.utils import apply_inject
from okrs_api.model_helpers.ca_configs import add_tenant_fields, adapt_error_for_hasura
from okrs_api.api.controller.helpers import is_pvadmin_connected_okrs


MODIFIABLE_DB_FIELDS = [
    "name",
    "description",
    "work_item_container_id",
    "level_depth",
    "ca_config_id",
    "app_owned_by",
    "starts_at",
    "ends_at",
    "parent_objective_id",
    "owned_by",
    "last_updated_by",
    "app_last_updated_by",
]


def decrement_objective_level_depths(
    db_session, tenant_id_str, tenant_group_id_str, deleted_level_depth
):
    """Decrement the level depths for objectives."""
    try:
        objectives = (
            db_session.query(models.Objective)
            .filter(
                or_(
                    models.Objective.tenant_group_id_str == tenant_group_id_str,
                    and_(
                        models.Objective.tenant_id_str == tenant_id_str,
                        models.Objective.tenant_id_str != "",
                    ),
                )
            )
            .filter(models.Objective.level_depth > deleted_level_depth)
            .filter(models.Objective.deleted_at_epoch == 0)
            .all()
        )

        for objective in objectives:
            db_session.query(models.Objective).filter_by(id=objective.id).update(
                {"level_depth": models.Objective.level_depth - 1},
                synchronize_session="fetch",
            )
            commit_db_session(db_session)
    except Exception as e:
        db_session.rollback()
        raise e


def increment_objective_level_depths(
    db_session, tenant_id_str, tenant_group_id_str, inserted_level_depth
):
    """Increment the level depths for objectives."""
    try:
        objectives = (
            db_session.query(models.Objective)
            .filter(
                or_(
                    models.Objective.tenant_group_id_str == tenant_group_id_str,
                    and_(
                        models.Objective.tenant_id_str == tenant_id_str,
                        models.Objective.tenant_id_str != "",
                    ),
                )
            )
            .filter(models.Objective.level_depth >= inserted_level_depth)
            .filter(models.Objective.deleted_at_epoch == 0)
            .all()
        )

        for objective in objectives:
            db_session.query(models.Objective).filter_by(id=objective.id).update(
                {"level_depth": models.Objective.level_depth + 1},
                synchronize_session="fetch",
            )
            commit_db_session(db_session)
    except Exception as e:
        db_session.rollback()
        raise e


async def list_container_objectives(input_prepper):
    """List all objectives for a container."""

    async def fetch_key_results(obj):
        return await list_objective_key_results(db_session, input_prepper, obj["id"])

    async def fetch_work_item_container(obj):
        return await get_wic_for_objective(input_prepper, obj)

    container_id = input_prepper.input_parser.container_id
    filter_by_objective_ids = input_prepper.input_parser.objective_ids
    with input_prepper.db_session() as db_session:
        response_objectives = await get_all_objectives_for_container(
            db_session,
            input_prepper,
            container_id,
            filter_by_objective_ids=filter_by_objective_ids,
        )

        response_objectives = await apply_inject(
            response_objectives, "key_results", fetch_key_results
        )

        response_objectives = await apply_inject(
            response_objectives, "container", fetch_work_item_container
        )

    return response_objectives


async def get_all_objectives_for_container(
    db_session,
    input_prepper,
    container_id,
    include_related=True,
    filter_by_objective_ids=None,
):
    """
    Retrieve all objectives visible for a container.

    A container is a strategy or board in which the OKR is hosted.
    The function retrieves all the objectives accessible in this container.
    This includes -
    1. objectives created within the container
    2. parent objectives of all objectives from step 1 if include_related == True
    3. child objectives of all objectives from step 1 if include_related == True
    """

    tenant_id_str = input_prepper.org_id
    tenant_group_id_str = input_prepper.tenant_group_id
    app_name = input_prepper.app_name

    # Get all objectives in the current container
    if filter_by_objective_ids and isinstance(filter_by_objective_ids, list):
        objectives = (
            db_session.query(models.Objective)
            .filter(
                or_(
                    models.Objective.tenant_group_id_str == tenant_group_id_str,
                    and_(
                        models.Objective.tenant_id_str == tenant_id_str,
                        models.Objective.tenant_id_str != "",
                    ),
                )
            )
            .filter(models.Objective.deleted_at_epoch == 0)
            .filter(
                models.Objective.id.in_([int(oid) for oid in filter_by_objective_ids])
            )
            .join(models.WorkItemContainer)
            .filter(models.WorkItemContainer.external_id == container_id)
            .filter(models.WorkItemContainer.app_name == app_name)
            .all()
        )
    else:
        objectives = (
            db_session.query(models.Objective)
            .filter(
                or_(
                    models.Objective.tenant_group_id_str == tenant_group_id_str,
                    and_(
                        models.Objective.tenant_id_str == tenant_id_str,
                        models.Objective.tenant_id_str != "",
                    ),
                )
            )
            .filter(models.Objective.deleted_at_epoch == 0)
            .join(models.WorkItemContainer)
            .filter(models.WorkItemContainer.external_id == container_id)
            .filter(models.WorkItemContainer.app_name == app_name)
            .all()
        )

    if len(objectives) == 0:
        return []

    objective_ids = [o.id for o in objectives]
    parent_objective_ids = [
        o.parent_objective_id
        for o in objectives
        if o.parent_objective_id not in objective_ids
    ]

    if include_related:
        child_objectives = (
            db_session.query(models.Objective)
            .filter(models.Objective.parent_objective_id.in_(objective_ids))
            .filter(models.Objective.deleted_at_epoch == 0)
            .all()
        )
    else:
        child_objectives = []

    if include_related:
        parent_objectives = (
            db_session.query(models.Objective)
            .filter(models.Objective.id.in_(parent_objective_ids))
            .filter(models.Objective.deleted_at_epoch == 0)
            .all()
        )
    else:
        parent_objectives = []

    all_objectives = list(set(objectives + parent_objectives + child_objectives))

    return [o.to_dict() for o in all_objectives]


async def get_wic_for_objective(input_prepper, objective):
    """Get the latest work item container details for an objective."""
    input_prepper.input_parser.container_ids = [
        objective["work_item_container"]["external_id"]
    ]
    wrangler = service_wrangler_factory(
        input_prepper, override_action="list_activity_containers"
    )
    api_response_data, api_response_status = await wrangler.call_service()

    if (api_response_status == HTTPStatus.OK) and (len(api_response_data) > 0):
        return api_response_data[0]

    return {}


def create_new_objective(db_session, input_prepper, data):
    """Create a new DB entry for configuration."""

    params = {k: data[k] for k in data.keys() if k in MODIFIABLE_DB_FIELDS}
    add_tenant_fields(params, input_prepper)
    config = models.Objective(**params)
    db_session.add(config)
    commit_db_session(db_session)
    return config


def fetch_objective(db_session, input_prepper):
    """Retrieve Objective from DB by ID."""

    data = db_session.query(models.Objective).get(input_prepper.input_parser.id)

    return data


def validate_app_owned_by(input_data, input_prepper):
    """Validate app_owned_by for objectives and KR actions."""
    if is_pvadmin_connected_okrs(input_prepper):
        if "app_owned_by" in input_data and input_data["app_owned_by"] is not None:
            if not ("owned_by" in input_data and input_data["owned_by"] is not None):
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="owned_by field is missing or Invalid value for owned_by",
                            error_code="OWNED_BY_REQUIRED_OR_INVALID_VALUE",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
        if "app_owned_by" in input_data and input_data["app_owned_by"] is None:
            if not ("owned_by" in input_data and input_data["owned_by"] is None):
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="owned_by field is missing or Invalid value for owned_by",
                            error_code="OWNED_BY_REQUIRED_OR_INVALID_VALUE",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
    return None


def validate_and_format_dates(input_data, error_code):
    """Validate and format start and end dates for objectives."""
    try:
        input_data["starts_at"] = datetime.fromisoformat(
            input_data.starts_at
        ).astimezone(timezone.utc)
        input_data["ends_at"] = datetime.fromisoformat(input_data.ends_at).astimezone(
            timezone.utc
        )
    except BaseException as e:
        return [
            dict(
                message=f"Invalid date format : {e}",
                error_code=error_code,
            )
        ]
    if input_data["starts_at"] > input_data["ends_at"]:
        return [
            dict(
                message="starts_at is greater than ends_at",
                error_code=error_code,
            )
        ]
    return None
