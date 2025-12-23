"""Util classes and functions for custom attributes configs."""
import json
import uuid

from open_alchemy import models

from okrs_api.model_helpers.common import commit_db_session

DEFAULT_FIELDS_NUM = 2
MAX_ACTIVE_CA_FIELD = 12

# Config Types
CA_TYPE_TEXT = "text"
CA_TYPE_DATE = "date"
CA_TYPE_NUMERIC = "numeric"
CA_TYPE_SINGLE_SELECT = "singleselect"
CA_TYPE_MULTI_SELECT = "multiselect"
ALL_CA_TYPES = (
    CA_TYPE_TEXT,
    CA_TYPE_DATE,
    CA_TYPE_NUMERIC,
    CA_TYPE_SINGLE_SELECT,
    CA_TYPE_MULTI_SELECT,
)

MODIFIABLE_DB_FIELDS = [
    "label",
    "tooltip",
    "value",
    "ca_config_type",
    "is_default",
    "is_archived",
    "is_mandatory_objective",
    "is_mandatory_keyresult",
    "is_objective",
    "is_keyresult",
]


def get_new_uuid():
    """Generate and create a new uuid."""

    return str(uuid.uuid4())


def adapt_error_for_hasura(error_obj, code):
    """Convert error from API to Hasura specific format."""

    return (
        dict(
            message=json.dumps(error_obj), extensions=dict(code=code, details=error_obj)
        ),
        code,
    )


def fetch_all_configurations(db_session, input_prepper):
    """Retrieve all custom attribute configs from DB."""

    if (input_prepper.input_parser.is_active is True) or (
        (not input_prepper.input_parser.is_active)
        and (input_prepper.input_parser.is_archived is False)
    ):
        return (
            db_session.query(models.CustomAttributesConfig)
            .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
            .filter_by(is_deleted=False)
            .filter_by(is_archived=False)
            .all()
        )

    if (input_prepper.input_parser.is_archived is True) or (
        (not input_prepper.input_parser.is_archived)
        and (input_prepper.input_parser.is_active is False)
    ):
        return (
            db_session.query(models.CustomAttributesConfig)
            .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
            .filter_by(is_deleted=False)
            .filter_by(is_archived=True)
            .all()
        )
    return (
        db_session.query(models.CustomAttributesConfig)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(is_deleted=False)
        .all()
    )


def fetch_all_active_configurations(db_session, input_prepper):
    """Retrieve all active configs."""

    return (
        db_session.query(models.CustomAttributesConfig)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(is_deleted=False)
        .filter_by(is_archived=False)
        .all()
    )


def fetch_configuration(db_session, input_prepper):
    """Retrieve a custom attribute config from DB by ID."""

    data = db_session.query(models.CustomAttributesConfig).get(
        input_prepper.input_parser.id
    )

    if data.tenant_group_id_str != input_prepper.tenant_group_id:
        return None

    return data


def fetch_configuration_by_id(db_session, input_prepper, config_id):
    """Retrieve a custom attribute config from DB by ID."""

    data = db_session.query(models.CustomAttributesConfig).get(config_id)

    if data and (data.tenant_group_id_str != input_prepper.tenant_group_id):
        return None

    return data


def remove_default_configurations(db_session, input_prepper):
    """Remove the default configurations from DB."""

    default_fields = (
        db_session.query(models.CustomAttributesConfig)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(is_default=True)
        .filter_by(is_deleted=False)
        .all()
    )
    for field in default_fields:
        field.soft_delete()
        field.is_deleted = True

    db_session.add_all(default_fields)
    commit_db_session(db_session)


def create_default_configurations(db_session, input_prepper):
    """Create the default configurations in DB."""

    type_of_okrs = models.CustomAttributesConfig(
        label="Type of OKR",
        ca_config_type=CA_TYPE_SINGLE_SELECT,
        is_default=True,
        is_objective=False,
        is_keyresult=False,
        value=[
            dict(id=get_new_uuid(), value="Committed OKRs"),
            dict(id=get_new_uuid(), value="Aspirational OKRs"),
        ],
        tooltip="Defines the goal nature of your OKR",
        tenant_id_str=input_prepper.org_id,
        tenant_group_id_str=input_prepper.tenant_group_id,
        app_created_by=input_prepper.user_id,
        created_by=input_prepper.planview_user_id,
        app_last_updated_by=input_prepper.user_id,
        last_updated_by=input_prepper.planview_user_id,
        deleted_at_epoch=0,
    )

    status = models.CustomAttributesConfig(
        label="Status",
        ca_config_type=CA_TYPE_SINGLE_SELECT,
        is_default=True,
        is_objective=False,
        is_keyresult=False,
        value=[
            dict(id=get_new_uuid(), value="Work Period"),
            dict(id=get_new_uuid(), value="Measurement Period"),
            dict(id=get_new_uuid(), value="Abandoned"),
            dict(id=get_new_uuid(), value="Paused"),
            dict(id=get_new_uuid(), value="Draft"),
        ],
        tooltip="Tracks the progress of your OKR",
        tenant_id_str=input_prepper.org_id,
        tenant_group_id_str=input_prepper.tenant_group_id,
        app_created_by=input_prepper.user_id,
        created_by=input_prepper.planview_user_id,
        app_last_updated_by=input_prepper.user_id,
        last_updated_by=input_prepper.planview_user_id,
        deleted_at_epoch=0,
    )

    db_session.add_all([type_of_okrs, status])
    commit_db_session(db_session)


def ca_configs_response_adapter(ca_configs):
    """Adapt the DB values into api response format."""
    all_configs = [ca_config_response_adapter(x) for x in ca_configs]
    all_configs = sorted(all_configs, key=lambda k: k["created_at"])
    all_configs = sorted(all_configs, key=lambda k: k["is_default"], reverse=True)
    return all_configs


def ca_config_response_adapter(ca_config):
    """Adapt the DB values into api response format."""
    response = ca_config.to_dict()
    non_required_fields = [
        "deleted_at_epoch",
        "pv_created_by",
        "pv_tenant_id",
        "pv_last_updated_by",
    ]
    for k in non_required_fields:
        if k in response:
            del response[k]

    if "value" in response:
        if isinstance(response["value"], str):
            response["value"] = json.loads(response["value"])
    return response


def add_tenant_fields(params, input_prepper):
    """Add tenant and user id fields."""

    params.update(
        dict(
            tenant_id_str=input_prepper.org_id,
            tenant_group_id_str=input_prepper.tenant_group_id,
            app_created_by=input_prepper.user_id,
            created_by=input_prepper.planview_user_id,
            app_last_updated_by=input_prepper.user_id,
            last_updated_by=input_prepper.planview_user_id,
            deleted_at_epoch=0,
        )
    )

    return params


def validate_configuration(configs):
    """Validate config and return errors (if any)."""

    req_fields = ["label", "ca_config_type"]
    errors = []

    for field in req_fields:
        if configs.get(field, None) is None:
            errors.append(
                dict(
                    message=f"Field {field} is mandatory but missing",
                    error_code="MISSING_MANDATORY_FIELD",
                    error_details=f"{field}",
                )
            )

    ca_type = configs.get("ca_config_type", "")
    if ca_type not in ALL_CA_TYPES:
        errors.append(
            dict(
                message=f"Field type {ca_type} not allowed",
                error_code="INVALID_FIELD_TYPE",
            )
        )

    update_errors = validate_update_configuration(configs)

    return errors + update_errors


def validate_update_configuration(configs):
    """Validate the configs specifically applicable to update operation."""

    errors = []
    ca_type = configs.get("ca_config_type", "")
    if ca_type in (CA_TYPE_SINGLE_SELECT, CA_TYPE_MULTI_SELECT):
        ca_options = configs.get("value", [])
        if isinstance(ca_options, str):
            ca_options = json.loads(ca_options)

        if not isinstance(ca_options, list):
            errors.append(
                dict(message="Invalid format for options", error_code="INVALID_FORMAT")
            )
        elif (not ca_options) or (len(ca_options) == 0):
            errors.append(
                dict(
                    message="Dropdown or multi select options cannot be empty",
                    error_code="EMPTY_OPTIONS_LIST",
                )
            )
        else:
            unique_options = {x["value"] for x in ca_options}
            if len(unique_options) != len(ca_options):
                errors.append(
                    dict(
                        message="Only unique values are accepted",
                        error_code="DUPLICATE_OPTIONS",
                    )
                )
    else:
        ca_value = configs.get("value", None)
        if ca_value is not None:
            errors.append(
                dict(
                    message="Only singleselect and multiselect can have value",
                    error_code="INVALID_VALUE_FOR_FIELD",
                )
            )

    # if (
    #     (not configs.get("is_archived"))
    #     and (not configs.get("is_objective"))
    #     and (not configs.get("is_keyresult"))
    # ):
    #     errors.append(
    #         dict(
    #             message="Unarchived field cannot be turned off for both objective and key result",
    #             error_code="CANNOT_TURN_OFF_FOR_BOTH",
    #         )
    #     )

    return errors


def add_ca_option_ids(configs):
    """Add unique ID to single select or multi select options."""

    ca_type = configs.get("ca_config_type", "")
    if ca_type in (CA_TYPE_SINGLE_SELECT, CA_TYPE_MULTI_SELECT):
        ca_options = configs.get("value", [])
        if isinstance(ca_options, str):
            ca_options = json.loads(ca_options)
        for option in ca_options:
            if not option.get("id", None):
                option["id"] = get_new_uuid()
        configs["value"] = ca_options
    return configs


def create_new_configuration(db_session, input_prepper, configs):
    """Create a new DB entry for configuration."""
    params = {k: configs[k] for k in configs.keys() if k in MODIFIABLE_DB_FIELDS}
    params["is_default"] = False  # By default it is False for API sources
    add_tenant_fields(params, input_prepper)
    config = models.CustomAttributesConfig(**params)
    db_session.add(config)
    commit_db_session(db_session)
    return config


def update_configuration(db_session, current_config):
    """Update an existing configuration."""

    db_session.add(current_config)
    commit_db_session(db_session)
