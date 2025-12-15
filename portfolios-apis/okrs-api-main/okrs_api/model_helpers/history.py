"""Utilities for getting history."""
from open_alchemy import models
from sqlalchemy import or_, and_

from okrs_api.model_helpers.settings import SettingsManager


def fetch_history(db_session, input_prepper):
    """Fetch all values for an object."""
    object_id = input_prepper.input_parser.id
    object_type = input_prepper.input_parser.type

    tenant_group_id = input_prepper.tenant_group_id
    tenenat_id = input_prepper.org_id

    manager = SettingsManager(
        org_id=input_prepper.org_id,
        tenant_group_id=input_prepper.tenant_group_id,
        created_by=input_prepper.planview_user_id,
        db_session=db_session,
    )
    settings = manager.get_settings()
    roll_up_progress_flag = settings.roll_up_progress
    if object_type == "objective":
        history = (
            db_session.query(models.ActivityLog)
            .filter(
                or_(
                    models.ActivityLog.tenant_group_id_str == tenant_group_id,
                    models.ActivityLog.tenant_id_str == tenenat_id,
                )
            )
            .filter(
                or_(
                    models.ActivityLog.objective_id
                    == object_id,  # objective_id matches the given object_id
                    and_(
                        models.ActivityLog.objective_id.is_(
                            None
                        ),  # objective_id is NULL
                        models.ActivityLog.key_result_id.is_(
                            None
                        ),  # key_result_id is NULL
                        models.ActivityLog.progress_point_id.is_(
                            None
                        ),  # progress_point_id is NULL
                        models.ActivityLog.action
                        != "update.listviewcolumnconfig.user_settings",
                        models.ActivityLog.action
                        != "insert.listviewcolumnconfig.user_settings",
                    ),
                )
            )
            .order_by(models.ActivityLog.created_at.desc())
            .all()
        )
    else:
        history = (
            db_session.query(models.ActivityLog)
            .filter(
                or_(
                    models.ActivityLog.tenant_group_id_str == tenant_group_id,
                    models.ActivityLog.tenant_id_str == tenenat_id,
                )
            )
            .filter_by(key_result_id=object_id)
            .order_by(models.ActivityLog.created_at.desc())
            .all()
        )

    return list(
        filter(None, (get_each_record(each, roll_up_progress_flag) for each in history))
    )


def get_each_record(value, roll_up_progress_flag):
    """Extract format ofo each record from db."""
    value_dict = value.to_dict()
    data_fields = [
        "id",
        "action",
        "app_created_by",
        "app_last_updated_by",
        "created_at",
        "info",
        "key_result_id",
        "objective_id",
        "progress_point_id",
        "updated_at",
        "work_item_id",
    ]
    info_dict = value_dict["info"]
    if (
        not roll_up_progress_flag
        and info_dict.get("new", {}).get("rolled_up_progress_percentage") is not None
    ):
        return None
    if roll_up_progress_flag:
        if "objective_progress_percentage" in info_dict:
            del info_dict["objective_progress_percentage"]
        if "new" in info_dict and "objective_progress_percentage" in info_dict["new"]:
            del info_dict["new"]["objective_progress_percentage"]
    data = {}
    for k in data_fields:
        try:
            data[k] = value_dict[k]
        except KeyError:
            data[k] = None
    return data
