"""Util classes and functions for custom attributes values."""
import datetime
import json
from json import JSONDecodeError

from open_alchemy import models
from sqlalchemy import or_, and_
from okrs_api.model_helpers.common import commit_db_session
from okrs_api.model_helpers.ca_configs import (
    fetch_configuration_by_id,
    add_tenant_fields,
    CA_TYPE_DATE,
    CA_TYPE_SINGLE_SELECT,
    CA_TYPE_NUMERIC,
    CA_TYPE_TEXT,
)

# pylint: disable=all

MAX_TEXT_LENGTH = 1000


def fetch_custom_attributes(db_session, input_prepper, remove_inactives=True):
    """Fetch all values for an object."""

    object_id = input_prepper.input_parser.object_id
    object_type = input_prepper.input_parser.object_type
    tenant_group_id = input_prepper.tenant_group_id

    ca_values = (
        db_session.query(models.CustomAttributesValue)
        .filter_by(tenant_group_id_str=tenant_group_id)
        .filter_by(object_id=object_id)
        .filter_by(object_type=object_type)
        .filter_by(deleted_at_epoch=0)
        .all()
    )
    ca_selected_values = []

    for ca_value in ca_values:
        config = fetch_configuration_by_id(
            db_session, input_prepper, ca_value.ca_config_id
        )
        if remove_inactives and (config.is_deleted or config.is_archived):
            continue
        if ca_value.object_type == "objective":
            if not config.is_objective:
                continue
        else:
            if not config.is_keyresult:
                continue

        ca_selected_values.append(ca_value)

    return ca_selected_values


def ca_values_response_adapter(ca_values_with_configs):
    """Adapt a JSON response for a list of CA values."""

    return [ca_value_response_adapter(each) for each in ca_values_with_configs]


def ca_value_response_adapter(ca_value):
    """Return a JSON compatible view of CA value."""

    response = ca_value.to_dict()
    non_required_fields = [
        "deleted_at_epoch",
        "pv_created_by",
        "pv_tenant_id",
        "updated_at",
        "created_at",
        "pv_last_updated_by",
    ]
    for k in non_required_fields:
        if k in response:
            del response[k]

    if "value" in response:

        if isinstance(response["value"], str):
            try:
                if isinstance(json.loads(response["value"]), bool):
                    response["value"] = str(response["value"])
                else:
                    response["value"] = json.loads(response["value"])
                    if isinstance(response["value"], int) or isinstance(
                        response["value"], float
                    ):
                        response["value"] = str(response["value"])
            except JSONDecodeError:
                print("WARNING: could not parse value - returning as is")

    # response["configuration"] = ca_config_response_adapter(config)
    return response


def get_wic_role(db_session, input_prepper, wic_id):
    """Given a WIC id get a non-none role."""

    role = (
        db_session.query(models.WorkItemContainerRole)
        .filter_by(work_item_container_id=wic_id)
        .filter(
            or_(
                models.WorkItemContainerRole.created_by
                == input_prepper.planview_user_id,
                and_(
                    models.WorkItemContainerRole.app_created_by
                    == input_prepper.user_id,
                    models.WorkItemContainerRole.app_created_by != "",
                ),
            )
        )
        .filter(models.WorkItemContainerRole.okr_role != "none")
        .first()
    )

    return role


def get_objective_role(db_session, input_prepper, object_id):
    """Get the role for an objective."""
    role = "none"

    objective = (
        db_session.query(models.Objective)
        .filter_by(id=object_id)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(deleted_at_epoch=0)
        .first()
    )

    if not objective:
        return role
    role = (
        db_session.query(models.WorkItemContainerRole)
        .filter_by(work_item_container_id=objective.work_item_container_id)
        .filter(
            or_(
                models.WorkItemContainerRole.created_by
                == input_prepper.planview_user_id,
                and_(
                    models.WorkItemContainerRole.app_created_by
                    == input_prepper.user_id,
                    models.WorkItemContainerRole.app_created_by != "",
                ),
            )
        )
        .filter(models.WorkItemContainerRole.okr_role != "none")
        .first()
    )

    if not role:
        role = "none"

    return role


def get_key_result_role(db_session, input_prepper, object_id):
    """Get the role for a key result."""
    role = "none"

    kr = (
        db_session.query(models.KeyResult)
        .filter_by(id=object_id)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(deleted_at_epoch=0)
        .first()
    )

    if not kr:
        return role

    role = (
        db_session.query(models.WorkItemContainerRole)
        .filter_by(work_item_container_id=kr.objective.work_item_container_id)
        .filter(
            or_(
                models.WorkItemContainerRole.created_by
                == input_prepper.planview_user_id,
                and_(
                    models.WorkItemContainerRole.app_created_by
                    == input_prepper.user_id,
                    models.WorkItemContainerRole.app_created_by != "",
                ),
            )
        )
        .filter(models.WorkItemContainerRole.okr_role != "none")
        .first()
    )

    if not role:
        role = "none"

    return role


def get_okr_role_for_object(db_session, input_prepper):
    """Get the role for an objective or key result."""
    object_id = input_prepper.input_parser.object_id
    object_type = input_prepper.input_parser.object_type
    role = "none"

    if object_type == "objective":
        role = get_objective_role(db_session, input_prepper, object_id)
    elif object_type == "keyresult":
        role = get_key_result_role(db_session, input_prepper, object_id)

    return role


def create_new_ca_value(db_session, input_prepper, data_dict, values_data):
    """Create a new DB entry for configuration."""
    processed_data_list = []
    for each in data_dict:
        params = {"ca_config_id": each, "value": data_dict[each]}
        params.update(values_data)
        add_tenant_fields(params, input_prepper)
        record = models.CustomAttributesValue(**params)
        processed_data_list.append(record)
    db_session.add_all(processed_data_list)
    commit_db_session(db_session)


def update_ca_values(db_session, input_prepper, data_dict, values_data):
    """Retrieve a custom attribute config from DB by ID."""
    tenant_group_id = input_prepper.tenant_group_id
    ca_values = (
        db_session.query(models.CustomAttributesValue)
        .filter_by(tenant_group_id_str=tenant_group_id)
        .filter_by(object_id=values_data["object_id"])
        .filter_by(object_type=values_data["object_type"])
        .filter_by(deleted_at_epoch=0)
        .all()
    )
    for each in ca_values:
        if str(each.ca_config_id) in data_dict:
            if each.value != data_dict[str(each.ca_config_id)]:
                each.value = data_dict[str(each.ca_config_id)]
                each.last_updated_by = input_prepper.planview_user_id
                each.app_last_updated_by = input_prepper.user_id
            del data_dict[str(each.ca_config_id)]
    db_session.add_all(ca_values)
    commit_db_session(db_session)
    create_new_ca_value(db_session, input_prepper, data_dict, values_data)


def validate_and_fix_ca_values(
    db_session, input_prepper, ca_values
):  # noqa: C901, R0912
    """Validate if we have the correct data for CA values."""

    errors = []
    for key in ca_values:
        if ca_values[key] is None:
            continue
        config = fetch_configuration_by_id(db_session, input_prepper, key)
        if not config:
            errors.append(
                dict(
                    message=f"Could not find a matching config with ID {key}",
                    error_code="INVALID_CONFIG_ID",
                )
            )
            return errors

        val = ca_values[key]
        if config.ca_config_type == CA_TYPE_TEXT:
            if len(val) > MAX_TEXT_LENGTH or len(val) <= 0:
                errors.append(
                    dict(
                        message=f"Max length for text {val} should be {MAX_TEXT_LENGTH} or \
                        Min length should be more than zero",
                        error_code="INVALID_VALUE_FOR_TEXT_FIELD",
                    )
                )
        elif config.ca_config_type == CA_TYPE_NUMERIC:
            try:
                val = float(val)
            except BaseException:
                errors.append(
                    dict(
                        message=f"Not a number for numeric field {val}",
                        error_code="INVALID_VALUE_FOR_NUMERIC_FIELD",
                    )
                )
        elif config.ca_config_type == CA_TYPE_DATE:
            try:
                _ = datetime.datetime.strptime(val, "%Y-%m-%d")
            except BaseException as ex:
                errors.append(
                    dict(
                        message=f"{val} does not seem to be a valid date in the format: {ex}",
                        error_code="INVALID_VALUE_FOR_DATE_FIELD",
                    )
                )
        elif config.ca_config_type == CA_TYPE_SINGLE_SELECT:
            if not (isinstance(val, str) and len(val) > 0):
                errors.append(
                    dict(
                        message="Not a valid format for single select",
                        error_code="INVALID_VALUE_FOR_SINGLESELECT_FIELD",
                    )
                )
        else:  # multi select
            if not (isinstance(val, list) and len(val) > 0):
                errors.append(
                    dict(
                        message="Not a valid format for multiselect",
                        error_code="INVALID_VALUE_FOR_MULTISELECT_FIELD",
                    )
                )

    return errors
