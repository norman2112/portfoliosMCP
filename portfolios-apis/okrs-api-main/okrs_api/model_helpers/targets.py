"""Util classes and functions for targets."""
from datetime import timedelta

from open_alchemy import models

from okrs_api.model_helpers.common import (
    add_tenant_and_user_fields,
    set_last_updated_by_fields,
)
from okrs_api.utils import parse_datetime_str, append_error

CREATABLE_DB_FIELDS = [
    "key_result_id",
    "starts_at",
    "ends_at",
    "value",
]

MODIFIABLE_DB_FIELDS = [
    "starts_at",
    "ends_at",
    "value",
]


def create_target(input_prepper, data):
    """Create a new DB entry for target."""
    params = {k: data[k] for k in data.keys() if k in CREATABLE_DB_FIELDS}
    add_tenant_and_user_fields(params, input_prepper, add_pv_fields=True)
    target = models.Target(**params)
    return target


def update_target(input_prepper, target_object, data):
    """Create a new DB entry for target."""
    target_object.starts_at = data["starts_at"]
    target_object.ends_at = data["ends_at"]
    target_object.value = data["value"]
    set_last_updated_by_fields(target_object, input_prepper, add_pv_fields=True)


def delete_target(input_prepper, target_object):
    """Create a new DB entry for target."""
    target_object.is_deleted = True
    set_last_updated_by_fields(target_object, input_prepper, add_pv_fields=True)


def get_targets_by_krid(db_session, key_result_id):
    """Retrieve the targets from DB by key_result_id."""
    targets = (
        db_session.query(models.Target)
        .filter_by(key_result_id=key_result_id, is_deleted=False)
        .order_by(models.Target.starts_at)
        .all()
    )
    return targets


def is_valid_target(target):
    """Validate a target."""
    if not target.get("starts_at"):
        return False, "starts_at is required"
    if not target.get("ends_at"):
        return False, "ends_at is required"
    if target.get("value") is None:
        return False, "target value is required"
    try:
        target["starts_at"] = parse_datetime_str(target["starts_at"])
        target["ends_at"] = parse_datetime_str(target["ends_at"])
    except ValueError:
        return False, "Invalid date format"
    return True, None


def is_targets_sequence_valid(targets):
    """Validate targets sequence."""
    for index, target in enumerate(targets):
        starts_at = target["starts_at"]
        ends_at = target["ends_at"]
        if starts_at > ends_at:
            return False, "Target start date greater than target end date"
        if index > 0:
            previous_date = starts_at - timedelta(days=1)
            if previous_date != targets[index - 1]["ends_at"]:
                return False, "Incorrect date range for the targets"
    return True, None


def validate_targets(targets):  # noqa: C901, R0912
    """Validate if we have the correct data for targets."""

    errors = []
    if not targets or len(targets) == 0:
        append_error(errors, "TARGETS_MISSING", "No targets provided")
        return errors, None
    if len(targets) > 12:
        append_error(errors, "TOO_MANY_TARGETS", "Number of targets exceeds 12")
        return errors, None
    for target in targets:
        is_valid_status, validity_message = is_valid_target(target)
        if not is_valid_status:
            append_error(errors, "INVALID_TARGET", f"{validity_message}")
    if errors:
        return errors, None
    sorted_targets = sorted(targets, key=lambda t: t["starts_at"])
    is_valid_status, validity_message = is_targets_sequence_valid(sorted_targets)
    if not is_valid_status:
        append_error(errors, "INVALID_TARGET", f"{validity_message}")
    return errors, sorted_targets


def validate_input_and_generate_targets(key_result_payload):
    """Validate if we have the correct data for targets and generate targets' data."""
    errors = []
    if not (
        key_result_payload.starts_at
        and key_result_payload.ends_at
        and key_result_payload.target_value is not None
    ):
        append_error(errors, "CANNOT_CREATE_TARGET", "Target values are missing")
        return errors, None
    try:
        key_result_payload["starts_at"] = parse_datetime_str(
            key_result_payload["starts_at"]
        )
        key_result_payload["ends_at"] = parse_datetime_str(
            key_result_payload["ends_at"]
        )
    except ValueError as ve:
        append_error(errors, "CANNOT_CREATE_TARGET", f"{ve}")
        return errors, None
    targets = [
        {
            "starts_at": key_result_payload["starts_at"],
            "ends_at": key_result_payload["ends_at"],
            "value": key_result_payload["target_value"],
        }
    ]
    return errors, targets


def get_mapped_target(targets, measured_at):
    """Iterate over targets and get the related target id for the provided measured_at."""
    if not targets:
        return None
    for target in targets:
        if target.starts_at.date() <= measured_at <= target.ends_at.date():
            return target.id
    if measured_at < targets[0].starts_at.date():
        return targets[0].id
    return targets[-1].id
