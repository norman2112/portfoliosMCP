"""Manager class for list activity containers custom actions."""

from open_alchemy import models
from sqlalchemy import or_, not_
from okrs_api.api.controller.helpers import (
    get_app_name_for_product_type,
    get_container_type_for_product_type,
    get_container_type,
)


class ListActivitityContainersManager:
    """Class to handle the list activity containers actions."""

    def __init__(self, input_prepper=None):
        """Initialize the ListActivitityContainersManager with input_prepper."""
        self.input_prepper = input_prepper

    def update_container_external_titles(self, updated_list):
        """Update the external titles in work item containers."""
        with self.input_prepper.db_session() as db_session:
            ids_to_update = [item["id"] for item in updated_list]

            objects_to_update = (
                db_session.query(models.WorkItemContainer)
                .filter(models.WorkItemContainer.id.in_(ids_to_update))
                .all()
            )

            for obj in objects_to_update:
                for item in updated_list:
                    if obj.id == item["id"] and obj.external_id == item["external_id"]:
                        obj.external_title = item["title"]
                        break
            db_session.commit()

    # TODO: WHen merging with work update this method to filter out by container_type
    def get_all_work_item_containers(self, product_types):
        """Retrives all work item containers from the database for which the user has access to."""
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
        with self.input_prepper.db_session() as db_session:
            work_item_containers = (
                db_session.query(
                    models.WorkItemContainer.id,
                    models.WorkItemContainer.external_title,
                    models.WorkItemContainer.external_id,
                    models.WorkItemContainer.external_type,
                    models.WorkItemContainer.app_name,
                )
                .select_from(models.WorkItemContainerRole)
                .join(
                    models.WorkItemContainer,
                    models.WorkItemContainerRole.work_item_container_id
                    == models.WorkItemContainer.id,
                )
                .filter(
                    or_(
                        models.WorkItemContainer.tenant_group_id_str
                        == self.input_prepper.tenant_group_id,
                        models.WorkItemContainer.tenant_id_str
                        == self.input_prepper.org_id,
                    )
                )
                .filter(
                    or_(
                        models.WorkItemContainerRole.created_by
                        == self.input_prepper.planview_user_id,
                        models.WorkItemContainerRole.app_created_by
                        == self.input_prepper.user_id,
                    )
                )
                .filter(models.WorkItemContainer.app_name.in_(app_names))
                .filter(models.WorkItemContainer.container_type.in_(container_types))
                .filter(not_(models.WorkItemContainerRole.okr_role == "none"))
                .filter_by(deleted_at_epoch=0)
                .all()
            )
        return work_item_containers

    def get_work_item_container(self, product_types=None):
        """Retrives work item containers for which the user has access to."""
        work_item_containers = self.get_all_work_item_containers(product_types)
        work_item_containers_dict = [row._asdict() for row in work_item_containers]
        for wic in work_item_containers_dict:
            wic["title"] = wic.pop("external_title")

        return work_item_containers_dict
