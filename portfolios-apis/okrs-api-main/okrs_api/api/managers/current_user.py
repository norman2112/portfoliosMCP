"""Manager class for current user custom actions."""
from http import HTTPStatus

from open_alchemy import models
from sqlalchemy import or_
from okrs_api.api.controller.helpers import (
    get_app_name_for_product_type,
    get_container_type_for_product_type,
    get_container_type,
)


class CurrentUserManager:
    """Class to handle the current user custom actions."""

    def __init__(self, input_prepper=None):
        """Initialize the CurrentUserManager with input_prepper."""
        self.input_prepper = input_prepper

    def get_wics(self, context_ids, db_session):
        """Get available wics for the user."""
        available_work_item_containers = []
        if context_ids:
            available_work_item_containers = (
                db_session.query(models.WorkItemContainer)
                .filter(
                    or_(
                        models.WorkItemContainer.tenant_group_id_str
                        == self.input_prepper.tenant_group_id,
                        models.WorkItemContainer.tenant_id_str
                        == self.input_prepper.org_id,
                    )
                )
                .filter(models.WorkItemContainer.external_id.in_(context_ids))
                .filter_by(
                    deleted_at_epoch=0,
                )
                .all()
            )
        return available_work_item_containers

    def fetch_user_role_info(self, db_session, product_types):
        """Fetch current user's roles information from WorkItemContainerRole."""
        container_types = [
            get_container_type_for_product_type(product_type)
            for product_type in product_types
        ]
        emty_container_types = [
            get_container_type(product_type) for product_type in product_types
        ]
        container_types.extend(emty_container_types)
        app_names = [
            get_app_name_for_product_type(product_type)
            for product_type in product_types
        ]

        user_roles = (
            db_session.query(
                models.WorkItemContainer.external_id,
                models.WorkItemContainer.external_type,
                models.WorkItemContainerRole.okr_role,
                models.WorkItemContainerRole.app_role,
            )
            .join(
                models.WorkItemContainerRole,
                models.WorkItemContainer.id
                == models.WorkItemContainerRole.work_item_container_id,
            )
            .filter(
                or_(
                    models.WorkItemContainer.tenant_id_str == self.input_prepper.org_id,
                    models.WorkItemContainer.tenant_group_id_str
                    == self.input_prepper.tenant_group_id,
                )
            )
            .filter(models.WorkItemContainer.app_name.in_(app_names))
            .filter(models.WorkItemContainer.container_type.in_(container_types))
            .filter(models.WorkItemContainer.deleted_at_epoch == 0)
            .filter(
                or_(
                    models.WorkItemContainerRole.created_by
                    == self.input_prepper.planview_user_id,
                    models.WorkItemContainerRole.app_created_by
                    == self.input_prepper.user_id,
                )
            )
            .all()
        )
        return user_roles

    def get_current_user_v2(self, product_types):
        """Retrieve current user's roles information."""
        with self.input_prepper.db_session() as db_session:
            user_roles = self.fetch_user_role_info(db_session, product_types)
            result = []
            for user_role in user_roles:
                result.append(
                    {
                        "context_id": user_role[0],
                        "product_type": user_role[1],
                        "okr_role": user_role[2],
                        "app_role": user_role[3],
                    }
                )
        return {"work_item_container_roles": result}, HTTPStatus.OK
