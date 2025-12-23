"""Manager class for Objectives."""
from open_alchemy import models
from sqlalchemy import and_
from aiohttp.web import Response

CONTAINER_TYPE_NAME_MAP = {
    "lk_board": "Board",
    "e1_strategy": "Strategy",
    "e1_work": "Work",
}


class ObjectivesManager:
    """Class to handle the Objectives."""

    def __init__(self, input_prepper=None):
        """Initialize the ObjectivesManager with input_prepper."""
        self.input_prepper = input_prepper

    def get_total_count(self, db_session, id_list):
        """Get the total number of objectives."""
        base_obj_query = db_session.query(models.Objective.id).filter_by(
            tenant_group_id_str=self.input_prepper.tenant_group_id, deleted_at_epoch=0
        )
        if id_list:
            base_obj_query = base_obj_query.filter(models.Objective.id.in_(id_list))
        total_count = base_obj_query.count()
        return total_count

    def fetch_objectives(self):
        """Fetch objectives."""
        user_limit = self.input_prepper.input_parser.limit or 10
        user_offset = self.input_prepper.input_parser.offset or 0
        limit = min(max(int(user_limit), 1), 500)  # Restrict limit to 1-500
        offset = max(int(user_offset), 0)  # Ensure offset is non-negative
        ids = self.input_prepper.input_parser.ids
        id_list = [int(i) for i in ids.split(",")] if ids else []
        with self.input_prepper.db_session() as db_session:
            total_records = self.get_total_count(db_session, id_list)
            objectives_query = db_session.query(
                models.Objective.id,
                models.Objective.name,
                models.Objective.description,
                models.Objective.starts_at,
                models.Objective.ends_at,
                models.Objective.level_depth,
                models.Objective.parent_objective_id,
                models.Objective.progress_percentage,
                models.Objective.rolled_up_progress_percentage,
                models.Objective.work_item_container_id,
                models.Objective.owned_by,
                models.Objective.created_at,
                models.WorkItemContainer.external_id,
                models.WorkItemContainer.container_type,
            )
            objectives_query = objectives_query.join(
                models.WorkItemContainer,
                models.Objective.work_item_container_id == models.WorkItemContainer.id,
            )
            if id_list:
                objectives_query = objectives_query.filter(
                    models.Objective.id.in_(id_list)
                )
            objectives = (
                objectives_query.filter_by(
                    tenant_group_id_str=self.input_prepper.tenant_group_id
                )
                .filter_by(deleted_at_epoch=0)
                .order_by(models.Objective.id)
                .limit(limit)
                .offset(offset)
                .all()
            )
            result = []
            for objective in objectives:
                curr_objective = {
                    "id": objective.id,
                    "name": objective.name,
                    "description": objective.description,
                    "starts_at": objective.starts_at,
                    "ends_at": objective.ends_at,
                    "level_depth": objective.level_depth,
                    "parent_objective_id": objective.parent_objective_id,
                    "progress_percentage": objective.progress_percentage,
                    "rolled_up_progress_percentage": objective.rolled_up_progress_percentage,
                    "work_item_container_id": objective.work_item_container_id,
                    "owned_by": objective.owned_by,
                    "created_at": objective.created_at,
                    "scope_id": objective.external_id,
                    "scope_type": CONTAINER_TYPE_NAME_MAP[objective.container_type],
                }
                result.append(curr_objective)
            return {"total_records": total_records, "objectives": result}

    def fetch_objectives_by_wic_id(self):
        """Fetch objectives."""
        work_item_container_id = self.input_prepper.input_parser.work_item_container_id
        with self.input_prepper.db_session() as db_session:
            objectives_query = db_session.query(
                models.Objective.id,
                models.Objective.name,
                models.Objective.description,
                models.Objective.starts_at,
                models.Objective.ends_at,
                models.Objective.level_depth,
                models.Objective.parent_objective_id,
                models.Objective.progress_percentage,
                models.Objective.rolled_up_progress_percentage,
                models.Objective.work_item_container_id,
                models.Objective.owned_by,
                models.Objective.created_at,
                models.WorkItemContainer.external_id,
                models.WorkItemContainer.container_type,
            )
            objectives_query = objectives_query.join(
                models.WorkItemContainer,
                models.Objective.work_item_container_id == models.WorkItemContainer.id,
            )
            objectives = (
                objectives_query.filter(
                    models.Objective.tenant_group_id_str
                    == self.input_prepper.tenant_group_id,
                    models.Objective.work_item_container_id == work_item_container_id,
                    models.Objective.deleted_at_epoch == 0,
                )
                .order_by(models.Objective.id)
                .all()
            )
            result = []
            for objective in objectives:
                curr_objective = {
                    "id": objective.id,
                    "name": objective.name,
                    "description": objective.description,
                    "starts_at": objective.starts_at,
                    "ends_at": objective.ends_at,
                    "level_depth": objective.level_depth,
                    "parent_objective_id": objective.parent_objective_id,
                    "progress_percentage": objective.progress_percentage,
                    "rolled_up_progress_percentage": objective.rolled_up_progress_percentage,
                    "work_item_container_id": objective.work_item_container_id,
                    "owned_by": objective.owned_by,
                    "created_at": objective.created_at,
                    "scope_id": objective.external_id,
                    "scope_type": CONTAINER_TYPE_NAME_MAP[objective.container_type],
                }
                result.append(curr_objective)
            return result

    def fetch_objective_by_id(self):
        """Fetch objectives."""
        objective_id = self.input_prepper.input_parser.id
        with self.input_prepper.db_session() as db_session:
            objectives_query = db_session.query(
                models.Objective.id,
                models.Objective.name,
                models.Objective.description,
                models.Objective.starts_at,
                models.Objective.ends_at,
                models.Objective.level_depth,
                models.Objective.parent_objective_id,
                models.Objective.progress_percentage,
                models.Objective.rolled_up_progress_percentage,
                models.Objective.work_item_container_id,
                models.Objective.owned_by,
                models.Objective.created_at,
                models.WorkItemContainer.external_id,
                models.WorkItemContainer.container_type,
            )
            objectives_query = objectives_query.join(
                models.WorkItemContainer,
                models.Objective.work_item_container_id == models.WorkItemContainer.id,
            )

            objective = objectives_query.filter(
                and_(
                    models.Objective.tenant_group_id_str
                    == self.input_prepper.tenant_group_id,
                    models.Objective.id == objective_id,
                    models.Objective.deleted_at_epoch == 0,
                )
            ).first()
            if not objective:
                return Response(
                    text="null", status=200, content_type="application/json"
                )
            return {
                "id": objective.id,
                "name": objective.name,
                "description": objective.description,
                "starts_at": objective.starts_at,
                "ends_at": objective.ends_at,
                "level_depth": objective.level_depth,
                "parent_objective_id": objective.parent_objective_id,
                "progress_percentage": objective.progress_percentage,
                "rolled_up_progress_percentage": objective.rolled_up_progress_percentage,
                "work_item_container_id": objective.work_item_container_id,
                "owned_by": objective.owned_by,
                "created_at": objective.created_at,
                "scope_id": objective.external_id,
                "scope_type": CONTAINER_TYPE_NAME_MAP[objective.container_type],
            }
