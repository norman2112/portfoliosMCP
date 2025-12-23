"""Model helpers for Progress Points."""
from sqlalchemy import or_, nullslast
from open_alchemy import models

from okrs_api.model_helpers.common import add_tenant_and_user_fields

MODIFIABLE_DB_FIELDS = [
    "key_result_id",
    "target_id",
    "measured_at",
    "value",
    "comment",
    "key_result_progress_percentage",
    "objective_progress_percentage",
]


def create_new_progress_point(input_prepper, data):
    """Create a new DB entry for progress_point."""
    params = {k: data[k] for k in data.keys() if k in MODIFIABLE_DB_FIELDS}
    add_tenant_and_user_fields(params, input_prepper)
    progress_point = models.ProgressPoint(**params)
    return progress_point


def get_by_id_and_tenant(db_session, progress_point_id, tenant_group_id, org_id):
    """Retrieve progress point from DB by id, tenant_group_id and tenant_id."""
    progress_point = (
        db_session.query(models.ProgressPoint)
        .filter(
            or_(
                models.ProgressPoint.tenant_group_id_str == tenant_group_id,
                models.ProgressPoint.tenant_id_str == org_id,
            )
        )
        .filter_by(
            id=progress_point_id,
            deleted_at_epoch=0,
        )
        .first()
    )
    return progress_point


def get_latest_progress_point_by_krid(db_session, key_result_id):
    """Retrieve the latest progress point from DB by key_result_id."""
    latest_progress_point = (
        db_session.query(
            models.ProgressPoint.id,
            models.ProgressPoint.measured_at,
        )
        .filter_by(key_result_id=key_result_id, deleted_at_epoch=0)
        .order_by(
            nullslast(models.ProgressPoint.measured_at.desc()),
            models.ProgressPoint.id.desc(),
        )
        .first()
    )
    return latest_progress_point


def get_progress_points_by_krid(db_session, key_result_id):
    """Retrieve the progress points from DB by key_result_id."""
    # Todo: check if there are any null measured_at
    progress_points = (
        db_session.query(models.ProgressPoint)
        .filter_by(key_result_id=key_result_id, deleted_at_epoch=0)
        .all()
    )
    return progress_points
