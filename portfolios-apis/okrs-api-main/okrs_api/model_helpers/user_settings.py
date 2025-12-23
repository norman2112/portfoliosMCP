"""User Settings Model helper here."""
import copy
import json
from http import HTTPStatus
from open_alchemy import models
from sqlalchemy import or_

from okrs_api.model_helpers.common import commit_db_session
from okrs_api.model_helpers.ca_configs import adapt_error_for_hasura


MODIFIABLE_DB_FIELDS = ["user_id", "app_user_id", "type", "value"]


def fetch_user_settings(db_session, input_prepper):
    """Retrieve all active configs."""
    input_data = input_prepper.input_parser

    user_settings = (
        db_session.query(models.UserSettings)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(is_deleted=False)
        .filter_by(user_id=input_data["user_id"])
        .filter_by(type=input_data["type"])
        .all()
    )
    if not user_settings:
        return []

    ca_config = get_ca_configs(db_session, input_prepper)
    updated_value, return_value, is_missing_value = add_missing_ca_ids_to_value(
        user_settings[0].value, ca_config
    )
    user_settings_to_return = copy.deepcopy(user_settings)
    user_settings_to_return[0].value = return_value
    if is_missing_value:
        try:
            user_settings[0].value = updated_value
            commit_db_session(db_session)
        except Exception as e:
            print(
                f"Exception while updating CA values for user settings {e} "
                f'for user_id {input_data["user_id"]}'
            )

    return user_settings_to_return


def validate_user_settings(configs):
    """Validate user settings data and return errors (if any)."""

    req_fields = ["user_id", "app_user_id", "type", "value"]
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
    value = configs.get("value")
    unique_values = {"id": [], "name": []}
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        errors.append(
            dict(
                message=f"Invalid value for value {value}",
                error_code="INVALID_VALUE",
                error_details=f"{value}",
            )
        )

    for each in value:
        column_type = each["column_type"]
        keys = unique_values.keys()
        for each_key in keys:
            if each[each_key] in unique_values[each_key] and column_type == "static":
                errors.append(
                    dict(
                        message=f"duplicate value for  {each_key}",
                        error_code="DUPLICATE_COLUMN_VALUES",
                        error_details=f"{each_key}",
                    )
                )
            else:
                unique_values[each_key].append(each[each_key])
    return errors


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
            pv_created_by=input_prepper.planview_user_id,
            pv_last_updated_by=input_prepper.planview_user_id,
            pv_tenant_id=input_prepper.tenant_group_id,
            is_deleted=False,
        )
    )


def user_settings_response_adapter(user_setting):
    """Adapt the DB values into api response format."""
    response = user_setting
    non_required_fields = [
        "is_deleted",
        "pv_created_by",
        "pv_tenant_id",
        "pv_last_updated_by",
        "created_at",
        "updated_at",
    ]
    for k in non_required_fields:
        if k in response:
            del response[k]

    if "value" in response:
        if isinstance(response["value"], str):
            response["value"] = json.loads(response["value"])
    return response


def get_user_settings_response(user_setting):
    """Adapt the DB values into api response format."""
    response = user_setting.to_dict()
    new_response = {}
    required_fileds = [
        "id",
        "user_id",
        "app_user_id",
    ]
    for k in required_fileds:
        new_response[k] = response[k]
    if "value" in response:
        value = response["value"]
        if isinstance(value, str):
            value = json.loads(response["value"])
        new_response["value"] = format_value(value)
    return [new_response]


def format_value(value):
    """Add app_onwed_by and sort remaining items with index."""
    ids = [each["id"] for each in value]
    if "app_owned_by" not in ids:
        value.sort(key=lambda x: x["index"])
        value.insert(
            3, {"hidden": False, "id": "app_owned_by", "index": 4, "name": "Owner"}
        )
        index = 5
        for each in value[4:]:
            each["index"] = index
            index += 1
    if "upcoming_target" not in ids:
        value.append(
            {
                "hidden": False,
                "id": "upcoming_target",
                "index": len(value) + 1,
                "name": "Upcoming Target",
            }
        )
    return value


def create_new_user_settings(db_session, input_prepper):
    """
    Create a new database entry for user settings.

    Args:
        db_session: The database session used for querying and committing.
        input_prepper: An object containing parsed input data and tenant/user details.

    Returns
    -------
    dict: A dictionary representation of the newly created user settings.

    """
    configs = input_prepper.input_parser
    params = {k: configs[k] for k in configs.keys() if k in MODIFIABLE_DB_FIELDS}
    add_tenant_fields(params, input_prepper)
    config = models.UserSettings(**params)
    ca_config = get_ca_configs(db_session, input_prepper)
    updated_value, return_value = add_missing_ca_ids_to_value(config.value, ca_config)[
        :2
    ]
    config.value = updated_value

    try:
        db_session.add(config)
        db_session.flush()
    except Exception as e:
        raise RuntimeError(f"Failed to flush the database session: {e}") from e

    commit_db_session(db_session)
    config_to_return = config.to_dict()
    config_to_return["value"] = return_value
    return config_to_return


def update_user_settings(db_session, input_data, user_settings_object):
    """Update user settings."""
    params = {
        k: input_data.get(k) for k in input_data.keys() if (k in MODIFIABLE_DB_FIELDS)
    }
    for p in params.keys():
        user_settings_object.__setattr__(p, params[p])
    user_setting_value = copy.deepcopy(user_settings_object.to_dict()["value"])
    user_settings_object.value = delete_names_for_custom_attributes(
        user_settings_object.value
    )

    try:
        db_session.add(user_settings_object)
        commit_db_session(db_session)
    except BaseException as e:
        return adapt_error_for_hasura(
            [
                dict(
                    message=f"Could not update User settings: {e}",
                    error_code="CANNOT_UPDATE_USER_SETTINGS",
                )
            ],
            HTTPStatus.BAD_REQUEST,
        )
    user_settings_dict = user_settings_object.to_dict()
    user_settings_dict["value"] = user_setting_value

    return user_settings_dict


def get_ca_configs(db_session, input_prepper):
    """Get custom attribute configs."""
    return (
        db_session.query(
            models.CustomAttributesConfig.id, models.CustomAttributesConfig.label
        )
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(deleted_at_epoch=0)
        .filter_by(is_archived=False)
        .filter_by(is_deleted=False)
        .filter(
            or_(
                models.CustomAttributesConfig.is_objective,
                models.CustomAttributesConfig.is_keyresult,
            )
        )
        .order_by(models.CustomAttributesConfig.id.asc())
        .all()
    )


def add_missing_ca_ids_to_value(value, ca_config):
    """Add missing ids to value."""
    is_missing_value = False
    ca_config_ids = {str(c.id) for c in ca_config}
    user_settings_ids = {
        item["id"] for item in value if item["column_type"] == "custom_attribute"
    }
    missing_ids = ca_config_ids - user_settings_ids
    missing_ca_configs = user_settings_ids - ca_config_ids
    updated_value = value.copy()
    ca_dict = {str(c.id): c.label for c in ca_config}

    if missing_ids:
        is_missing_value = True
        for missing_id in missing_ids:
            updated_value.append(
                {
                    "id": str(missing_id),
                    # "name": ca_dict.get(missing_id),
                    "hidden": True,
                    "column_type": "custom_attribute",
                }
            )
    return_value = copy.deepcopy(updated_value)
    return_value = update_names(return_value, ca_dict)
    if missing_ca_configs:
        is_missing_value = True
        updated_value = delete_by_ids(updated_value, missing_ca_configs)
    return updated_value, return_value, is_missing_value


def delete_by_ids(data, ids_to_remove):
    """Delete items from data by ids."""
    return [item for item in data if item.get("id") not in ids_to_remove]


def update_names(base_data, updates_dict):
    """Update names using ca dict."""
    for item in base_data:
        if item["id"] in updates_dict:
            item["name"] = updates_dict[item["id"]]  # update the name

    return base_data


def delete_names_for_custom_attributes(base_data):
    """Delete names for custom attributes."""
    for item in base_data:
        if item["column_type"] == "custom_attribute":
            item.pop("name")  # update the name

    return base_data
