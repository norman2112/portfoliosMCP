"""Manager class for Work Item Containers."""
from time import time_ns
from typing import List

from open_alchemy import models
from sqlalchemy import or_
from okrs_api.model_helpers.common import commit_db_session
from okrs_api.model_helpers.deleter import Deleter


class WorkItemContainersManager:
    """Class to handle the Work Item Containers."""

    def __init__(self, input_prepper):
        """Initialize the WorkItemContainersManager with input_prepper."""
        self.input_prepper = input_prepper
        self.wic_objectives = []

    def delete_work_item_container_entities(
        self, work_item_containers_external_ids: List[str], container_type  # Change to
    ):
        """Delete work item container entities."""
        deleted_wics = []
        with self.input_prepper.db_session() as db_session:
            for wic_external_id in work_item_containers_external_ids:
                wic_list = (
                    db_session.query(models.WorkItemContainer)
                    .filter(
                        models.WorkItemContainer.external_id == wic_external_id,
                        models.WorkItemContainer.container_type == container_type,
                        models.WorkItemContainer.deleted_at_epoch == 0,
                        or_(
                            models.Objective.tenant_group_id_str
                            == self.input_prepper.tenant_group_id,
                            models.Objective.tenant_id_str == self.input_prepper.org_id,
                        ),
                    )
                    .all()
                )

                if not wic_list:
                    print(
                        f"No work item container found for external "
                        f"id {wic_external_id} and external type {container_type}"
                    )
                    continue

                if len(wic_list) > 1:
                    print(
                        f"Multiple work item containers found for external "
                        f"id {wic_external_id} and external type {container_type}"
                    )
                    continue
                wic = wic_list[0]
                deleter = Deleter(db_session=db_session, model_instance=wic)
                deleter.delete()

                deleted_wics.append(wic.id)
                self.remove_parent_for_child_objectives(wic.id, db_session)
                self.delete_custom_attribute_values(
                    "objective", self.wic_objectives, db_session
                )
                key_result_ids = self.get_all_key_results(
                    self.wic_objectives, db_session
                )
                self.delete_custom_attribute_values(
                    "keyresult", key_result_ids, db_session
                )
            commit_db_session(db_session)
        return deleted_wics

    def remove_parent_for_child_objectives(self, wic_id, db_session):
        """Remove parent work item container entities."""
        child_objectives = self.get_all_child_objectives_from_other_wic(
            wic_id, db_session
        )
        if child_objectives:
            for child_objective in child_objectives:
                child_objective.parent_objective_id = None
                db_session.add(child_objective)

    def get_all_objectives_of_wic(self, wic_id, db_session):
        """Get all work item container entities."""
        try:
            objectives_list = (
                db_session.query(models.Objective.id)
                .filter(
                    models.Objective.work_item_container_id == wic_id,
                    models.Objective.deleted_at_epoch != 0,
                    or_(
                        models.Objective.tenant_group_id_str
                        == self.input_prepper.tenant_group_id,
                        models.Objective.tenant_id_str == self.input_prepper.org_id,
                    ),
                )
                .all()
            )
            objectives = [obj[0] for obj in objectives_list]
            return objectives
        except Exception as e:
            raise e

    def get_all_child_objectives_from_other_wic(self, wic_id, db_session):
        """Get all child objectives from other wic."""
        child_objectives_for_delete = []
        self.wic_objectives = self.get_all_objectives_of_wic(wic_id, db_session)
        child_objectives = (
            db_session.query(models.Objective)
            .filter(
                models.Objective.parent_objective_id.in_(self.wic_objectives),
                models.Objective.deleted_at_epoch == 0,
                models.Objective.work_item_container_id != wic_id,
                or_(
                    models.Objective.tenant_group_id_str
                    == self.input_prepper.tenant_group_id,
                    models.Objective.tenant_id_str == self.input_prepper.org_id,
                ),
            )
            .all()
        )
        for child in child_objectives:
            child_objectives_for_delete.append(child)
        return child_objectives_for_delete

    def delete_custom_attribute_values(self, object_type, object_ids, db_session):
        """Delete custom attribute values."""
        if not object_ids:
            return
        try:
            custom_attribute_values = (
                db_session.query(models.CustomAttributesValue)
                .filter(
                    models.CustomAttributesValue.object_type == object_type,
                    models.CustomAttributesValue.deleted_at_epoch == 0,
                    models.CustomAttributesValue.object_id.in_(object_ids),
                )
                .all()
            )

            for custom_attribute_value in custom_attribute_values:
                custom_attribute_value.deleted_at_epoch = time_ns()
                db_session.add(custom_attribute_value)
        except Exception as e:
            raise e

    def get_all_key_results(self, objective_ids: [], db_session):
        """Get all key results."""
        try:
            key_result_list = (
                db_session.query(models.KeyResult.id)
                .filter(
                    models.KeyResult.objective_id.in_(objective_ids),
                    or_(
                        models.KeyResult.tenant_group_id_str
                        == self.input_prepper.tenant_group_id,
                        models.KeyResult.tenant_id_str == self.input_prepper.org_id,
                    ),
                )
                .all()
            )
            key_result_ids = [kr[0] for kr in key_result_list]
            return key_result_ids
        except Exception as e:
            raise e
