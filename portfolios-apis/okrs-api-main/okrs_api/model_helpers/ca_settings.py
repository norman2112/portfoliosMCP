"""Util classes and functions for custom attributes settings."""

from open_alchemy import models
from okrs_api.model_helpers.common import commit_db_session

CUSTOM_ATTRIBUTES_DB_FIELDS = ["label", "enabled", "tooltip", "label_hidden"]


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


def get_existing_custom_attributes_settings(db_session, input_prepper):
    """Get existing custom attribute settings row for a tenant group."""

    dbresp = (
        db_session.query(models.CustomAttributesSettings)
        .filter_by(tenant_group_id_str=input_prepper.tenant_group_id)
        .filter_by(deleted_at_epoch=0)
        .first()
    )
    return dbresp


def create_new_custom_attributes_settings(db_session, input_prepper, data):
    """Insert new custom attribute settings row for a tenant group."""

    params = {k: data[k] for k in data.keys() if k in CUSTOM_ATTRIBUTES_DB_FIELDS}
    add_tenant_fields(params, input_prepper)
    settings = models.CustomAttributesSettings(**params)
    db_session.add(settings)
    commit_db_session(db_session)
    return settings
