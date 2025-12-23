"""Manager class for Activity Okrs."""
from open_alchemy import models
from sqlalchemy import or_, and_, select, literal_column


class ActivityOKRManager:
    """Handles retrieval and structuring of OKRs associated with activities."""

    def __init__(self, activity_ids, container_type, input_prepper):
        """Initialize the ActivityOKRManager with input_prepper."""
        self.activity_ids = activity_ids
        self.container_type = container_type
        self.input_prepper = input_prepper

    def get_objectives_and_key_results(self):
        """Fetch and return objectives and key results data."""
        if len(self.activity_ids) > 500:
            raise ValueError("Cannot process more than 500 activity IDs at once")
        with self.input_prepper.db_session() as db_session:
            directly_linked_objectives = self._get_directly_linked_objectives(
                db_session
            )
            if not directly_linked_objectives:
                return {"objectives": [], "work_item_containers": [], "work_items": []}
            ancestral_objectives = self._fetch_ancestral_objectives(
                directly_linked_objectives, db_session
            )
            wic_ids = list(set(obj.wic_id for obj in ancestral_objectives))
            wics = self._fetch_wic(wic_ids, db_session)
            obj_ids = list(set(obj.child_id for obj in ancestral_objectives))
            krs_wis = self._fetch_kr_and_wi(obj_ids, db_session)
            return self._stitch_data(ancestral_objectives, wics, krs_wis)

    def _get_tenant_filter(self, model):
        """Return tenant filter."""
        return or_(
            model.tenant_group_id_str == self.input_prepper.tenant_group_id,
            model.tenant_id_str == self.input_prepper.org_id,
        )

    def _get_directly_linked_objectives(self, db_session):
        """Fetch and return the directly linked objectives."""
        directly_linked_objectives = (
            db_session.query(models.WorkItem.id, models.KeyResult.objective_id)
            .join(
                models.KeyResultWorkItemMapping,
                models.WorkItem.id == models.KeyResultWorkItemMapping.work_item_id,
            )
            .join(
                models.KeyResult,
                and_(
                    models.KeyResultWorkItemMapping.key_result_id
                    == models.KeyResult.id,
                    models.KeyResult.deleted_at_epoch == 0,
                ),
            )
            .filter(
                and_(
                    models.WorkItem.external_id.in_(self.activity_ids),
                    models.WorkItem.container_type == self.container_type,
                    self._get_tenant_filter(models.WorkItem),
                )
            )
            .all()
        )
        return [obj[1] for obj in directly_linked_objectives]

    def _fetch_ancestral_objectives(self, directly_linked_objectives, db_session):
        """Fetch ancestral objectives using a recursive Common Table Expression (CTE)."""
        # Alias the Objective table
        obj = models.Objective.__table__

        # Base CTE: starting objectives
        base_cte = select(
            obj.c.id.label("child_id"),
            obj.c.name.label("child_name"),
            obj.c.description.label("description"),
            obj.c.starts_at.label("starts_at"),
            obj.c.ends_at.label("ends_at"),
            obj.c.progress_percentage.label("progress_percentage"),
            obj.c.rolled_up_progress_percentage.label("rolled_up_progress_percentage"),
            obj.c.level_depth.label("level_depth"),
            obj.c.parent_objective_id.label("parent_objective_id"),
            obj.c.work_item_container_id.label("wic_id"),
            literal_column("1").label("level"),
        ).where(
            obj.c.id.in_(directly_linked_objectives),
            obj.c.deleted_at_epoch == 0,
            self._get_tenant_filter(obj.c),
        )

        # Recursive CTE definition
        recursive_cte = base_cte.cte(name="objective_hierarchy", recursive=True)

        # Alias for reference in recursive part
        hierarchy = recursive_cte.alias()
        parent = obj.alias("o")

        recursive_part = select(
            parent.c.id.label("child_id"),
            parent.c.name.label("child_name"),
            parent.c.description.label("description"),
            parent.c.starts_at.label("starts_at"),
            parent.c.ends_at.label("ends_at"),
            parent.c.progress_percentage.label("progress_percentage"),
            parent.c.rolled_up_progress_percentage.label(
                "rolled_up_progress_percentage"
            ),
            parent.c.level_depth.label("level_depth"),
            parent.c.parent_objective_id.label("parent_objective_id"),
            parent.c.work_item_container_id.label("wic_id"),
            (hierarchy.c.level + 1).label("level"),
        ).where(
            parent.c.id == hierarchy.c.parent_objective_id,
            hierarchy.c.level < 5,
            parent.c.deleted_at_epoch == 0,
            self._get_tenant_filter(parent.c),
        )

        # Final CTE combining base and recursive part
        objective_hierarchy_cte = recursive_cte.union_all(recursive_part)

        # Final select from the CTE
        final_query = select(
            objective_hierarchy_cte.c.child_id,
            objective_hierarchy_cte.c.child_name,
            objective_hierarchy_cte.c.description,
            objective_hierarchy_cte.c.starts_at,
            objective_hierarchy_cte.c.ends_at,
            objective_hierarchy_cte.c.progress_percentage,
            objective_hierarchy_cte.c.rolled_up_progress_percentage,
            objective_hierarchy_cte.c.level_depth,
            objective_hierarchy_cte.c.parent_objective_id,
            objective_hierarchy_cte.c.wic_id,
            objective_hierarchy_cte.c.level,
        ).order_by(objective_hierarchy_cte.c.child_id, objective_hierarchy_cte.c.level)
        rows = db_session.execute(final_query).fetchall()
        return rows

    def _fetch_wic(self, wic_ids, db_session):
        wics = (
            db_session.query(
                models.WorkItemContainer.id,
                models.WorkItemContainer.external_id,
                models.WorkItemContainer.external_title.label("title"),
                models.WorkItemContainer.container_type,
                models.WorkItemContainerRole.okr_role,
            )
            .join(
                models.WorkItemContainerRole,
                and_(
                    models.WorkItemContainer.id
                    == models.WorkItemContainerRole.work_item_container_id,
                    models.WorkItemContainerRole.okr_role != "none",
                    or_(
                        models.WorkItemContainerRole.created_by
                        == self.input_prepper.planview_user_id,
                        and_(
                            models.WorkItemContainerRole.app_created_by
                            == self.input_prepper.user_id,
                            models.WorkItemContainerRole.app_created_by != "",
                        ),
                    ),
                ),
            )
            .filter(
                and_(
                    models.WorkItemContainer.id.in_(wic_ids),
                    models.WorkItemContainer.deleted_at_epoch == 0,
                    self._get_tenant_filter(models.WorkItemContainer),
                )
            )
            .all()
        )
        return wics

    def _fetch_kr_and_wi(self, obj_ids, db_session):
        krs_wis = (
            db_session.query(
                models.KeyResult.id.label("id"),
                models.KeyResult.objective_id.label("objective_id"),
                models.KeyResult.name.label("name"),
                models.KeyResult.description.label("description"),
                models.KeyResult.starts_at.label("overall_starts_at"),
                models.KeyResult.ends_at.label("overall_ends_at"),
                models.KeyResult.progress_percentage.label("progress_percentage"),
                models.KeyResult.starting_value.label("starting_value"),
                models.KeyResult.target_value.label("final_target_value"),
                models.WorkItem.id.label("wid"),
                models.WorkItem.external_id.label("external_id"),
                models.WorkItem.container_type.label("container_type"),
            )
            .outerjoin(
                models.KeyResultWorkItemMapping,
                models.KeyResult.id == models.KeyResultWorkItemMapping.key_result_id,
            )
            .outerjoin(
                models.WorkItem,
                models.KeyResultWorkItemMapping.work_item_id == models.WorkItem.id,
            )
            .filter(
                and_(
                    models.KeyResult.objective_id.in_(obj_ids),
                    models.KeyResult.deleted_at_epoch == 0,
                    self._get_tenant_filter(models.KeyResult),
                )
            )
            .all()
        )
        return krs_wis

    def _stitch_data(self, ancestral_objectives, wics, krs_wis):
        """Organize and structure the retrieved data into a cohesive result structure."""
        result = {"objectives": [], "work_item_containers": [], "work_items": []}
        wic_ids = {wic.id for wic in wics}

        # Process objectives
        stitched_objectives = self._process_objectives(ancestral_objectives, wic_ids)

        # Process key results and work items
        stitched_krs, stitched_wis = self._process_key_results_and_work_items(
            krs_wis, stitched_objectives
        )

        # Process work item containers
        stitched_wics = self._process_work_item_containers(wics)

        # Associate key results with their parent objectives
        self._associate_key_results_with_objectives(stitched_krs, stitched_objectives)

        result["work_item_containers"] = stitched_wics
        result["work_items"] = list(stitched_wis.values())
        result["objectives"] = list(stitched_objectives.values())
        return result

    @staticmethod
    def _process_objectives(ancestral_objectives, wic_ids):
        """Extract and structure objective data."""
        stitched_objectives = {}

        for obj in ancestral_objectives:
            if obj.child_id not in stitched_objectives and obj.wic_id in wic_ids:
                stitched_objectives[obj.child_id] = {
                    "id": obj.child_id,
                    "name": obj.child_name,
                    "description": obj.description,
                    "starts_at": obj.starts_at,
                    "ends_at": obj.ends_at,
                    "progress_percentage": obj.progress_percentage,
                    "rolled_up_progress_percentage": obj.rolled_up_progress_percentage,
                    "level_depth": obj.level_depth,
                    "parent_objective_id": obj.parent_objective_id,
                    "work_item_container_id": obj.wic_id,
                    "key_results": [],
                }

        return stitched_objectives

    @staticmethod
    def _process_key_results_and_work_items(krs_wis, stitched_objectives):
        """Extract and structure key results and work items data."""
        stitched_krs = {}
        stitched_wis = {}

        for kr_wi in krs_wis:
            # Process key results
            if kr_wi.objective_id not in stitched_objectives:
                continue
            if kr_wi.id not in stitched_krs:
                stitched_krs[kr_wi.id] = {
                    "id": kr_wi.id,
                    "objective_id": kr_wi.objective_id,
                    "name": kr_wi.name,
                    "description": kr_wi.description,
                    "overall_starts_at": kr_wi.overall_starts_at,
                    "overall_ends_at": kr_wi.overall_ends_at,
                    "starting_value": kr_wi.starting_value,
                    "final_target_value": kr_wi.final_target_value,
                    "progress_percentage": kr_wi.progress_percentage,
                    "work_item_ids": [],
                }

            if kr_wi.wid:
                # Associate work items with key results
                stitched_krs[kr_wi.id]["work_item_ids"].append(kr_wi.wid)

                # Process work items
                if kr_wi.wid not in stitched_wis:
                    stitched_wis[kr_wi.wid] = {
                        "id": kr_wi.wid,
                        "external_id": kr_wi.external_id,
                        "container_type": kr_wi.container_type,
                    }

        return stitched_krs, stitched_wis

    @staticmethod
    def _process_work_item_containers(wics):
        """Extract and structure work item container data."""
        return [
            {
                "id": wic.id,
                "external_id": wic.external_id,
                "title": wic.title,
                "container_type": wic.container_type,
            }
            for wic in wics
        ]

    @staticmethod
    def _associate_key_results_with_objectives(stitched_krs, stitched_objectives):
        """Associate key results with their parent objectives."""
        for key_result in stitched_krs.values():
            objective_id = key_result["objective_id"]
            if objective_id in stitched_objectives:
                stitched_objectives[objective_id]["key_results"].append(key_result)
