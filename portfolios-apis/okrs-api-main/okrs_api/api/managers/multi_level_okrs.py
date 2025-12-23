# pylint: disable=C0302,R1702
"""Manager class for multi level okrs custom action."""
from http import HTTPStatus
from datetime import datetime, time
from sqlalchemy import or_, and_, select, func, true, text
from open_alchemy import models
from okrs_api.utils import parse_datetime_str
from okrs_api.api.managers.user_settings import UserSettingsManager
from okrs_api.api.controller.error_helpers import bad_request_error


class MultiLevelOKR:
    """Class to handle the multi level okrs."""

    def __init__(self, input_prepper=None):
        """Initialize the MultiLevelOKR with input_prepper."""
        self.input_prepper = input_prepper
        self.objectives_map = {}
        self.wic_map = {}
        self.current_wic_id = None
        self.is_card_view = input_prepper.input_parser.is_card_view
        self.list_view_column_config = []
        self.custom_attribute_config = []
        self.custom_attribute_config_map = {}
        self.ca_columns_enabled = []
        self.ca_filter_list = []

    def _is_upcoming_target_needed(self):
        """Check if upcoming target query is needed."""
        if self.is_card_view:
            return False
        if not self.list_view_column_config:
            # show upcoming target column in list view by default
            return True
        return UserSettingsManager().is_column_enabled(
            self.list_view_column_config, "upcoming_target", "static"
        )

    @staticmethod
    def _get_latest_progress_point_query():
        """Return latest progress point query."""
        return (
            select(
                models.ProgressPoint.measured_at.label("measured_at"),
                models.ProgressPoint.value.label("pp_value"),
            )
            .filter(models.ProgressPoint.key_result_id == models.KeyResult.id)
            .filter(models.ProgressPoint.deleted_at_epoch == 0)
            .order_by(models.ProgressPoint.measured_at.desc())
            .limit(1)
            .correlate(models.KeyResult)
            .lateral()
        )

    @staticmethod
    def _get_upcoming_target_subquery():
        """Return upcoming target subquery."""
        today = datetime.combine(datetime.utcnow().date(), time.min)
        return (
            select(
                models.Target.ends_at.label("upcoming_target_ends_at"),
                models.Target.value.label("upcoming_target_value"),
            )
            .filter(models.Target.key_result_id == models.KeyResult.id)
            .filter(models.Target.is_deleted.is_(False))
            .filter(models.Target.ends_at >= today)
            .order_by(models.Target.ends_at.asc())
            .limit(1)
            .correlate(models.KeyResult)
            .lateral()
        )

    def _get_tenant_filter(self, model):
        """Return tenant filter."""
        return or_(
            model.tenant_group_id_str == self.input_prepper.tenant_group_id,
            model.tenant_id_str == self.input_prepper.org_id,
        )

    def _fetch_user_settings(self, db_session):
        """Fetch user settings."""
        user_setting = (
            db_session.query(models.UserSettings.value)
            .filter(
                and_(
                    models.UserSettings.is_deleted.is_(False),
                    self._get_tenant_filter(models.UserSettings),
                    or_(
                        models.UserSettings.user_id
                        == self.input_prepper.planview_user_id,
                        models.UserSettings.app_user_id == self.input_prepper.user_id,
                    ),
                    models.UserSettings.type == "listviewcolumnconfig",
                )
            )
            .first()
        )
        if user_setting and user_setting.value:
            self.list_view_column_config = user_setting.value

    def _fetch_wic_query(self, db_session):
        """Return the query to fetch work item containers."""
        return (
            db_session.query(
                models.WorkItemContainer.id,
                models.WorkItemContainer.external_id,
                models.WorkItemContainer.external_title.label("title"),
                models.WorkItemContainer.container_type,
                models.WorkItemContainer.app_name,
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
                    models.WorkItemContainer.deleted_at_epoch == 0,
                    self._get_tenant_filter(models.WorkItemContainer),
                )
            )
        )

    def _fetch_wic(self, db_session):
        """Fetch work item container based on the external ID."""
        allowed_external_id = self.input_prepper.input_parser.external_id
        wic_query = self._fetch_wic_query(db_session)
        wic_query = wic_query.filter(
            models.WorkItemContainer.external_id == allowed_external_id
        )
        wic = wic_query.first()
        if not wic:
            raise ValueError(
                f"Work Item Container with external_id {allowed_external_id} not found."
            )
        self.current_wic_id = wic.id

    def _fetch_wics(self, db_session, objectives):
        """Fetch work item containers for the given objectives."""
        wic_ids = {objective.work_item_container_id for objective in objectives}
        wic_query = self._fetch_wic_query(db_session)
        wic_query = wic_query.filter(models.WorkItemContainer.id.in_(wic_ids))
        wics = wic_query.all()
        for wic in wics:
            self.wic_map[wic.id] = {
                "id": wic.id,
                "external_id": wic.external_id,
                "external_title": wic.title,
                "container_type": wic.container_type,
                "app_name": wic.app_name,
            }

    def _fetch_key_results(
        self, db_session, objectives, is_upcoming_target_needed=False
    ):
        """Fetch key results for the given objectives."""
        objective_ids = list({objective.id for objective in objectives})
        batch_size = 1000
        key_results = []

        latest_pp_subquery = self._get_latest_progress_point_query()
        upcoming_target_subquery = (
            self._get_upcoming_target_subquery() if is_upcoming_target_needed else None
        )

        query_fields = [
            models.KeyResult.id,
            models.KeyResult.objective_id,
            models.KeyResult.name,
            models.KeyResult.starts_at,
            models.KeyResult.ends_at,
            models.KeyResult.progress_percentage,
            models.KeyResult.starting_value,
            models.KeyResult.target_value,
            models.KeyResult.app_owned_by,
            latest_pp_subquery,
        ]
        if is_upcoming_target_needed:
            query_fields.append(upcoming_target_subquery)

        for i in range(0, len(objective_ids), batch_size):
            batch_ids = objective_ids[i : i + batch_size]
            krs_query = (
                db_session.query(*query_fields)
                .select_from(models.KeyResult)
                .outerjoin(latest_pp_subquery, true())
            )
            if is_upcoming_target_needed:
                krs_query = krs_query.outerjoin(upcoming_target_subquery, true())
            krs_query = krs_query.filter(
                and_(
                    models.KeyResult.objective_id.in_(batch_ids),
                    models.KeyResult.deleted_at_epoch == 0,
                    self._get_tenant_filter(models.KeyResult),
                )
            )
            key_results.extend(krs_query.all())

        return key_results

    def _fetch_objectives(self, db_session):
        """Fetch multi level objectives from the database."""
        query = text(
            """
            WITH RECURSIVE base_objectives AS (
                SELECT
                    id, name, starts_at, ends_at, progress_percentage,
                    rolled_up_progress_percentage, level_depth,
                    parent_objective_id, app_owned_by, work_item_container_id
                FROM objectives
                WHERE
                    deleted_at_epoch = 0
                    AND (tenant_group_id_str = :tenant_group_id OR tenant_id_str = :tenant_id)
                    AND work_item_container_id = :wic_id
            ),

            parent_objectives AS (
                -- Level 1 parents
                SELECT
                    id, name, starts_at, ends_at, progress_percentage,
                    rolled_up_progress_percentage, level_depth,
                    parent_objective_id, app_owned_by, work_item_container_id,
                    1 AS level
                FROM objectives
                WHERE
                    id IN (SELECT parent_objective_id
                           FROM base_objectives
                           WHERE parent_objective_id IS NOT NULL)
                    AND deleted_at_epoch = 0
                    AND (tenant_group_id_str = :tenant_group_id OR tenant_id_str = :tenant_id)
                    AND work_item_container_id != :wic_id

                UNION ALL

                -- Level 2 and 3 parents
                SELECT
                    o.id, o.name, o.starts_at, o.ends_at, o.progress_percentage,
                    o.rolled_up_progress_percentage, o.level_depth,
                    o.parent_objective_id, o.app_owned_by, o.work_item_container_id,
                    p.level + 1
                FROM objectives o
                JOIN parent_objectives p ON o.id = p.parent_objective_id
                WHERE
                    p.level < 3
                    AND p.parent_objective_id IS NOT NULL
                    AND o.deleted_at_epoch = 0
                    AND (o.tenant_group_id_str = :tenant_group_id OR o.tenant_id_str = :tenant_id)
                    AND o.work_item_container_id != :wic_id
            ),

            child_objectives AS (
                -- Level 1 children
                SELECT
                    o.id, o.name, o.starts_at, o.ends_at, o.progress_percentage,
                    o.rolled_up_progress_percentage, o.level_depth,
                    o.parent_objective_id, o.app_owned_by, o.work_item_container_id,
                    1 AS level
                FROM objectives o
                WHERE
                    o.parent_objective_id IN (SELECT id FROM base_objectives)
                    AND o.deleted_at_epoch = 0
                    AND (o.tenant_group_id_str = :tenant_group_id OR o.tenant_id_str = :tenant_id)
                    AND o.work_item_container_id != :wic_id

                UNION ALL

                -- Level 2 and 3 children
                SELECT
                    o2.id, o2.name, o2.starts_at, o2.ends_at, o2.progress_percentage,
                    o2.rolled_up_progress_percentage, o2.level_depth,
                    o2.parent_objective_id, o2.app_owned_by, o2.work_item_container_id,
                    c.level + 1
                FROM objectives o2
                JOIN child_objectives c ON o2.parent_objective_id = c.id
                WHERE
                    c.level < 3
                    AND o2.deleted_at_epoch = 0
                    AND (o2.tenant_group_id_str = :tenant_group_id OR o2.tenant_id_str = :tenant_id)
                    AND o2.work_item_container_id != :wic_id
            )

            SELECT *, NULL AS level FROM base_objectives
            UNION
            SELECT * FROM parent_objectives
            UNION
            SELECT * FROM child_objectives;
        """
        )

        params = {
            "wic_id": self.current_wic_id,
            "tenant_group_id": self.input_prepper.tenant_group_id,
            "tenant_id": self.input_prepper.org_id,
        }
        result = db_session.execute(query, params).fetchall()
        return result

    def _filter_objectives_by_wic_id(self, objectives):
        """Filter objectives by work item container ID."""
        filtered_objectives = []
        for objective in objectives:
            if objective.work_item_container_id in self.wic_map:
                filtered_objectives.append(objective)
        return filtered_objectives

    def _process_objectives(self, objectives):
        """Process objectives."""
        for objective in objectives:
            if objective.id not in self.objectives_map:
                self.objectives_map[objective.id] = {
                    "id": objective.id,
                    "work_item_container_id": objective.work_item_container_id,
                    "name": objective.name,
                    "starts_at": objective.starts_at,
                    "ends_at": objective.ends_at,
                    "progress_percentage": objective.progress_percentage,
                    "rolled_up_progress_percentage": objective.rolled_up_progress_percentage,
                    "level_depth": objective.level_depth,
                    "parent_objective_id": objective.parent_objective_id,
                    "app_owned_by": objective.app_owned_by,
                    "latest_progress_measured_at": None,
                    "child_objectives_count": 0,
                    "key_results_count": 0,
                    "custom_attribute_values": [],
                    "key_results": [],
                }

    def _process_key_results(self, key_results, is_upcoming_target_needed=False):
        """Process key results and update objectives."""
        for key_result in key_results:
            objective_id = key_result.objective_id
            current_objective = self.objectives_map[objective_id]
            current_objective["key_results_count"] += 1
            kr_measured_at = key_result.measured_at
            if kr_measured_at:
                objective_measured_at = current_objective["latest_progress_measured_at"]
                if (
                    objective_measured_at is None
                    or objective_measured_at < kr_measured_at
                ):
                    current_objective["latest_progress_measured_at"] = kr_measured_at
            current_key_result = {
                "id": key_result.id,
                "name": key_result.name,
                "starts_at": key_result.starts_at,
                "ends_at": key_result.ends_at,
                "objective_id": key_result.objective_id,
                "work_item_container_id": current_objective["work_item_container_id"],
                "progress_percentage": key_result.progress_percentage,
                "starting_value": key_result.starting_value,
                "target_value": key_result.target_value,
                "upcoming_target_date": None,
                "upcoming_target_value": None,
                "value_type": "count",
                "app_owned_by": key_result.app_owned_by,
                "progress_point": {
                    "measured_at": key_result.measured_at,
                    "value": key_result.pp_value,
                },
                "custom_attribute_values": [],
            }
            if is_upcoming_target_needed:
                current_key_result[
                    "upcoming_target_date"
                ] = key_result.upcoming_target_ends_at
                current_key_result[
                    "upcoming_target_value"
                ] = key_result.upcoming_target_value
            current_objective["key_results"].append(current_key_result)

    def apply_primary_filters(self, okrs):
        """Apply primary filter on OKRs."""
        allowed_from_date = parse_datetime_str(
            self.input_prepper.input_parser.from_date
        )
        allowed_to_date = parse_datetime_str(self.input_prepper.input_parser.to_date)
        allowed_level_depths = self.input_prepper.input_parser.level_depth
        level_filtered_objectives = []
        for objective in okrs:
            if objective["level_depth"] in allowed_level_depths:
                level_filtered_objectives.append(objective)
        date_filtered_objectives = []
        for objective in level_filtered_objectives:
            if not (
                objective["starts_at"] <= allowed_to_date
                and objective["ends_at"] >= allowed_from_date
            ):
                continue
            filtered_key_results = []
            for kr in objective["key_results"]:
                if not (
                    kr["starts_at"] <= allowed_to_date
                    and kr["ends_at"] >= allowed_from_date
                ):
                    continue
                filtered_key_results.append(kr)
            objective["key_results"] = filtered_key_results
            date_filtered_objectives.append(objective)
        return date_filtered_objectives


# pylint: disable=too-many-public-methods
class MultiLevelOKRManager(MultiLevelOKR):
    """Class to handle the multi level okrs."""

    def _is_custom_column_needed(self, column_name, column_type="static"):
        """Check if custom column is needed."""
        if self.is_card_view:
            return False
        return UserSettingsManager().is_column_enabled(
            self.list_view_column_config, column_name, column_type
        )

    def _get_enabled_custom_attributes(self):
        """Get user enabled custom attributes."""
        enabled_ca_ids = []
        for custom_attribute in self.custom_attribute_config:
            if self._is_custom_column_needed(
                str(custom_attribute.id), "custom_attribute"
            ):
                enabled_ca_ids.append(custom_attribute.id)
        return enabled_ca_ids

    def _fetch_active_custom_attributes(self, db_session):
        """Fetch active custom attributes."""
        if not self.input_prepper.tenant_group_id:
            return
        custom_attribute_config = (
            db_session.query(models.CustomAttributesConfig)
            .filter(
                models.CustomAttributesConfig.is_deleted.is_(False),
                models.CustomAttributesConfig.is_archived.is_(False),
                models.CustomAttributesConfig.tenant_group_id_str
                == self.input_prepper.tenant_group_id,
            )
            .all()
        )
        self.custom_attribute_config = custom_attribute_config

    def _fetch_custom_attribute_values(
        self, db_session, object_ids, enabled_ca_ids, object_type
    ):
        """Fetch custom attribute values for given object IDs, enabled CA IDs, and object type."""
        if not enabled_ca_ids:
            return []
        objective_custom_attribute_values = (
            db_session.query(
                models.CustomAttributesValue.object_id,
                models.CustomAttributesValue.ca_config_id,
                models.CustomAttributesValue.value,
            )
            .filter(
                models.CustomAttributesValue.object_id.in_(object_ids),
                models.CustomAttributesValue.ca_config_id.in_(enabled_ca_ids),
                models.CustomAttributesValue.object_type == object_type,
                models.CustomAttributesValue.deleted_at_epoch == 0,
                self._get_tenant_filter(models.CustomAttributesValue),
            )
            .all()
        )
        return objective_custom_attribute_values

    @staticmethod
    def _get_ca_config_value(config_values, value_id):
        """Get the config value for a given value ID."""
        for config_value in config_values:
            if config_value["id"] == value_id:
                return config_value["value"]
        return ""

    def _get_custom_attribute_value_map(
        self, custom_attribute_values, custom_attribute_config_map
    ):
        """Create a map of custom attribute values grouped by object ID."""
        custom_attribute_value_map = {}
        for cav in custom_attribute_values:
            object_id = cav.object_id
            ca_config_id = cav.ca_config_id
            value = cav.value

            config = custom_attribute_config_map[ca_config_id]
            ca_type = config.ca_config_type
            ca_config_values = []

            if value:
                if ca_type in ("text", "numeric", "date"):
                    ca_config_values.append(value)
                elif ca_type == "singleselect":
                    ca_config_values.append(
                        self._get_ca_config_value(config.value, value)
                    )
                else:
                    for v in value:
                        ca_config_values.append(
                            self._get_ca_config_value(config.value, v)
                        )

            if object_id not in custom_attribute_value_map:
                custom_attribute_value_map[object_id] = []
            custom_attribute_value_map[object_id].append(
                {
                    "ca_config_id": ca_config_id,
                    "values": ca_config_values,
                    "ca_config_type": ca_type,
                }
            )
        return custom_attribute_value_map

    def _append_objectives_custom_attribute_values(
        self, custom_attribute_values, result, custom_attribute_config_map
    ):
        """Append custom attribute values to objectives in the result."""
        objectives = result["objectives"]
        custom_attribute_value_map = self._get_custom_attribute_value_map(
            custom_attribute_values, custom_attribute_config_map
        )
        for objective in objectives:
            objective["custom_attribute_values"] = custom_attribute_value_map.get(
                objective["id"], []
            )

    def _append_krs_custom_attribute_values(
        self, custom_attribute_values, result, custom_attribute_config_map
    ):
        """Append custom attribute values to key results in the result."""
        objectives = result["objectives"]
        custom_attribute_value_map = self._get_custom_attribute_value_map(
            custom_attribute_values, custom_attribute_config_map
        )
        for objective in objectives:
            key_results = objective["key_results"]
            for key_result in key_results:
                key_result["custom_attribute_values"] = custom_attribute_value_map.get(
                    key_result["id"], []
                )

    def _get_custom_attribute_value(self, db_session, result):
        """Fetch and append custom attribute values to objectives and key results."""
        enabled_ca_ids_objectives = []
        enabled_ca_ids_krs = []
        custom_attribute_config_map = {}
        for custom_attribute in self.custom_attribute_config:
            if custom_attribute.is_objective:
                enabled_ca_ids_objectives.append(custom_attribute.id)
            if custom_attribute.is_keyresult:
                enabled_ca_ids_krs.append(custom_attribute.id)
            custom_attribute_config_map[custom_attribute.id] = custom_attribute
            self.custom_attribute_config_map = custom_attribute_config_map
        objective_ids = []
        key_result_ids = []
        for objective in result["objectives"]:
            objective_ids.append(objective["id"])
            key_results = objective["key_results"]
            for key_result in key_results:
                key_result_ids.append(key_result["id"])
        objective_custom_attribute_values = self._fetch_custom_attribute_values(
            db_session, objective_ids, enabled_ca_ids_objectives, "objective"
        )
        self._append_objectives_custom_attribute_values(
            objective_custom_attribute_values, result, custom_attribute_config_map
        )
        kr_custom_attribute_values = self._fetch_custom_attribute_values(
            db_session, key_result_ids, enabled_ca_ids_krs, "keyresult"
        )
        self._append_krs_custom_attribute_values(
            kr_custom_attribute_values, result, custom_attribute_config_map
        )

    def fetch_multi_level_okr(self):
        """Fetch the multi level okr data."""
        with self.input_prepper.db_session() as db_session:
            try:
                self._fetch_wic(db_session)
            except ValueError as e:
                print("CANNOT_FETCH_OKRS", str(e))
                return {"objectives": [], "work_item_containers": []}, HTTPStatus.OK
            objectives = self._fetch_objectives(db_session)
            if not objectives:
                return {"objectives": [], "work_item_containers": []}, HTTPStatus.OK
            self._fetch_wics(db_session, objectives)
            objectives = self._filter_objectives_by_wic_id(objectives)
            if not self.is_card_view:
                self._fetch_user_settings(db_session)
            is_upcoming_target_needed = self._is_upcoming_target_needed()
            key_results = self._fetch_key_results(
                db_session, objectives, is_upcoming_target_needed
            )
            self._process_objectives(objectives)
            self._process_key_results(key_results, is_upcoming_target_needed)
            okrs = list(self.objectives_map.values())
            primary_filtered = self.apply_primary_filters(okrs)
            filtered_okrs = self.apply_filters(primary_filtered)
            if self.is_card_view:
                self.append_child_count(filtered_okrs, db_session)
            sorted_okrs = self.apply_sort(filtered_okrs)
            processed_wics = self.process_wics(self.wic_map, sorted_okrs)
            result = {
                "work_item_containers": processed_wics,
                "objectives": sorted_okrs,
            }
            if self.is_card_view:
                return result, HTTPStatus.OK
            self._fetch_active_custom_attributes(db_session)
            self._get_custom_attribute_value(db_session, result)
            if self.input_prepper.input_parser.custom_attributes_filters_list:
                self.apply_custom_attribute_filters(result)
            return result, HTTPStatus.OK

    def apply_filters(self, okrs):
        """Apply keyword, from_date, and to_date filters sequentially on OKRs."""
        filter_keyword = self.input_prepper.input_parser.filter_keyword
        filter_from_date = self.input_prepper.input_parser.filter_from_date
        filter_to_date = self.input_prepper.input_parser.filter_to_date
        filter_is_unassigned = self.input_prepper.input_parser.filter_is_unassigned
        filter_owners = self.input_prepper.input_parser.filter_owners
        filter_wics = self.input_prepper.input_parser.filter_work_item_container_ids

        parent_filtered = self.parent_objective_filter(okrs)
        child_filtered = self.child_objective_filter(parent_filtered)
        keyword_filtered = self.keyword_filter(child_filtered, filter_keyword)
        from_date_filtered = self.from_date_filter(keyword_filtered, filter_from_date)
        to_date_filtered = self.to_date_filter(from_date_filtered, filter_to_date)
        owner_filtered = self.owner_filter(
            to_date_filtered, filter_is_unassigned, filter_owners
        )
        wics_filtered = self.work_item_container_filter(
            owner_filtered,
            filter_wics,
        )
        return wics_filtered

    def parent_objective_filter(self, okrs):
        """Filter objectives by parent_objective_id."""
        parent_objective_ids = (
            self.input_prepper.input_parser.filter_parent_objective_ids
        )
        if not parent_objective_ids:
            return okrs
        parent_filtered = []
        for objective in okrs:
            if (
                objective["parent_objective_id"] in parent_objective_ids
                or objective["id"] in parent_objective_ids
            ):
                parent_filtered.append(objective)
        return parent_filtered

    def child_objective_filter(self, okrs):
        """Filter objectives by child_objective_id."""
        child_objective_ids = self.input_prepper.input_parser.filter_child_objective_ids
        if not child_objective_ids:
            return okrs
        child_filtered = []
        for objective in okrs:
            if objective["id"] in child_objective_ids:
                child_filtered.append(objective)
        return child_filtered

    @staticmethod
    def keyword_filter(okrs, filter_keyword):
        """Filter objectives and their key results based on a keyword."""
        if not filter_keyword:
            return okrs
        filter_keyword_lower = filter_keyword.lower()
        filtered_objectives = []
        for objective in okrs:
            filtered_key_results = []
            for kr in objective["key_results"]:
                if filter_keyword_lower in kr["name"].lower():
                    filtered_key_results.append(kr)
            if (
                filter_keyword_lower in objective["name"].lower()
                or filtered_key_results
            ):
                objective["key_results"] = filtered_key_results
                filtered_objectives.append(objective)
        return filtered_objectives

    @staticmethod
    def from_date_filter(okrs, filter_from_date):
        """Filter objectives and key results based on date comparisons."""
        if not filter_from_date:
            return okrs
        filter_from_date = parse_datetime_str(filter_from_date)
        filtered_objectives = []
        for objective in okrs:
            filtered_key_results = []
            for kr in objective["key_results"]:
                if filter_from_date <= kr["starts_at"]:
                    filtered_key_results.append(kr)
            if filter_from_date <= objective["starts_at"] or filtered_key_results:
                objective["key_results"] = filtered_key_results
                filtered_objectives.append(objective)
        return filtered_objectives

    @staticmethod
    def to_date_filter(okrs, filter_to_date):
        """Filter objectives and key results based on date comparisons."""
        if not filter_to_date:
            return okrs
        filter_to_date = parse_datetime_str(filter_to_date)
        filtered_objectives = []
        for objective in okrs:
            filtered_key_results = []
            for kr in objective["key_results"]:
                if filter_to_date >= kr["ends_at"]:
                    filtered_key_results.append(kr)
            if filter_to_date >= objective["ends_at"] or filtered_key_results:
                objective["key_results"] = filtered_key_results
                filtered_objectives.append(objective)
        return filtered_objectives

    def apply_sort(self, okrs):
        """Sort OKRs and their key results based on the specified order and field."""
        order_by = self.input_prepper.input_parser.order_by
        order = self.input_prepper.input_parser.order
        reverse_order = order == "desc"
        for objective in okrs:
            objective["key_results"] = sorted(
                objective["key_results"],
                key=lambda x: x[order_by],
                reverse=reverse_order,
            )
        sorted_okrs = sorted(
            okrs,
            key=lambda x: x[order_by].lower() if order_by == "name" else x[order_by],
            reverse=reverse_order,
        )
        return sorted_okrs

    @staticmethod
    def owner_filter(okrs, is_unassigned, filter_owners):
        """Filter objectives and key results based on ownership criteria."""
        if not is_unassigned and not filter_owners:
            return okrs
        filtered_objectives = []
        for objective in okrs:
            filtered_key_results = []
            for kr in objective["key_results"]:
                if (
                    is_unassigned
                    and kr["app_owned_by"] is None
                    or filter_owners
                    and kr["app_owned_by"] in filter_owners
                ):
                    filtered_key_results.append(kr)
            if (
                is_unassigned
                and objective["app_owned_by"] is None
                or filter_owners
                and objective["app_owned_by"] in filter_owners
                or filtered_key_results
            ):
                objective["key_results"] = filtered_key_results
                filtered_objectives.append(objective)
        return filtered_objectives

    @staticmethod
    def process_wics(wic_map, okrs):
        """Process WICS results."""
        work_item_container_ids = {okr["work_item_container_id"] for okr in okrs}
        processed_wics = []
        for wic_id in work_item_container_ids:
            processed_wics.append(wic_map[wic_id])
        return processed_wics

    @staticmethod
    def append_child_count(okrs, db_session):
        """Append child count of each objective."""
        objective_ids = [objective["id"] for objective in okrs]
        child_counts_result = (
            db_session.query(
                models.Objective.parent_objective_id,
                func.count(models.Objective.id).label("child_count"),
            )
            .filter(
                and_(
                    models.Objective.parent_objective_id.in_(objective_ids),
                    models.Objective.deleted_at_epoch == 0,
                )
            )
            .group_by(models.Objective.parent_objective_id)
            .all()
        )
        child_counts = dict(child_counts_result)
        for objective in okrs:
            if objective["id"] in child_counts:
                objective["child_objectives_count"] = child_counts[objective["id"]]

    def apply_custom_attribute_filters(self, result):
        """Filter objectives and key results based on custom attribute values."""
        filter_custom_attributes = (
            self.input_prepper.input_parser.custom_attributes_filters_list
        )
        filter_custom_attributes_map = self.map_ca_values(
            filter_custom_attributes, self.custom_attribute_config_map
        )

        ca_filtered_objectives_key_results = self.apply_filters_for_key_results(
            result["objectives"], filter_custom_attributes_map
        )

        objectives = self.apply_filters_for_objectives(
            ca_filtered_objectives_key_results, filter_custom_attributes_map
        )
        result.update({"objectives": objectives})
        return result

    def apply_filters_for_objectives(self, objectives, filter_custom_attributes):
        """Filter objectives based on single select custom attribute values."""
        if not filter_custom_attributes:
            return objectives
        ca_filter_methods = {
            "singleselect": self.apply_single_select_filters,
            "multiselect": self.apply_multi_select_filters,
            "numeric": self.apply_numeric_filters,
            "date": self.apply_date_filters,
            "text": self.apply_text_filters,
        }
        filtered_objectives = objectives
        for ca_filters in filter_custom_attributes:
            ca_type = ca_filters.get("ca_config_type")
            if ca_type in ca_filter_methods:
                filtered_objectives = ca_filter_methods[ca_type](
                    filtered_objectives, ca_filters
                )
        return filtered_objectives

    def apply_filters_for_key_results(self, objectives, filter_custom_attributes):
        """Filter key results based on single select custom attribute values."""
        if not filter_custom_attributes:
            return objectives
        ca_filter_methods = {
            "singleselect": self.apply_single_select_filters,
            "multiselect": self.apply_multi_select_filters,
            "numeric": self.apply_numeric_filters,
            "date": self.apply_date_filters,
            "text": self.apply_text_filters,
        }
        for objective in objectives:
            key_results = objective["key_results"]
            for ca_filters in filter_custom_attributes:
                ca_type = ca_filters.get("ca_config_type")
                if ca_type in ca_filter_methods:
                    key_results = ca_filter_methods[ca_type](key_results, ca_filters)
            objective["key_results"] = key_results
        return objectives

    @staticmethod
    def apply_single_select_filters(item_list, filter_single_selects):
        """Apply single select filters on the item list."""
        if not filter_single_selects:
            return item_list
        filtered_items = []
        for item in item_list:
            if item.get("key_results", None):
                filtered_items.append(item)
                continue
            for item_ca in item["custom_attribute_values"]:
                if item_ca["ca_config_id"] == filter_single_selects["ca_config_id"]:
                    if any(
                        value in filter_single_selects["values"]
                        for value in item_ca["values"]
                    ):
                        filtered_items.append(item)
        return filtered_items

    @staticmethod
    def apply_multi_select_filters(item_list, filter_multi_selects):
        """Apply multi select filters on the item list."""
        if not filter_multi_selects:
            return item_list
        filtered_items = []
        for item in item_list:
            if item.get("key_results", None):
                filtered_items.append(item)
                continue
            for item_ca in item["custom_attribute_values"]:
                if item_ca["ca_config_id"] == filter_multi_selects["ca_config_id"]:
                    if all(
                        value in item_ca["values"]
                        for value in filter_multi_selects["values"]
                    ):
                        filtered_items.append(item)
                        break
        return filtered_items

    @staticmethod
    def apply_numeric_filters(item_list, numeric_filter):
        """Apply numeric range filters on the item list."""
        if not numeric_filter:
            return item_list

        # Extract and parse numeric bounds, handle None gracefully
        from_value = numeric_filter["values"][0]
        to_value = numeric_filter["values"][1]
        from_num = int(from_value) if from_value is not None else None
        to_num = int(to_value) if to_value is not None else None

        # If both are None, return all items
        if from_num is None and to_num is None:
            return []

        filtered_items = []
        for item in item_list:
            if item.get("key_results", None):
                filtered_items.append(item)
                continue
            for item_ca in item["custom_attribute_values"]:
                if (
                    item_ca["ca_config_id"] == numeric_filter["ca_config_id"]
                    and item_ca["values"]
                ):
                    try:
                        target = int(item_ca["values"][0])
                    except (TypeError, ValueError):
                        continue  # Skip invalid numeric values
                    if (from_num is None or from_num <= target) and (
                        to_num is None or target <= to_num
                    ):
                        filtered_items.append(item)
                        break  # Avoid duplicates if multiple CAs match
        return filtered_items

    @staticmethod
    def apply_date_filters(item_list, numeric_filter):
        """Apply date range filters on the item list."""
        if not numeric_filter:
            return item_list

        from_date = numeric_filter["values"][0]
        to_date = numeric_filter["values"][1]

        # Parse dates only if not None
        from_date_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else None
        to_date_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else None

        # If both are None, return all items
        if from_date_dt is None and to_date_dt is None:
            return []

        filtered_items = []
        for item in item_list:
            if item.get("key_results", None):
                filtered_items.append(item)
                continue
            for item_ca in item["custom_attribute_values"]:
                if (
                    item_ca["ca_config_id"] == numeric_filter["ca_config_id"]
                    and item_ca["values"]
                ):
                    target = datetime.strptime(item_ca["values"][0], "%Y-%m-%d")
                    # Check range, handling None boundaries
                    if (from_date_dt is None or from_date_dt <= target) and (
                        to_date_dt is None or target <= to_date_dt
                    ):
                        filtered_items.append(item)
                        break  # Avoid duplicates if multiple CAs match
        return filtered_items

    @staticmethod
    def apply_text_filters(item_list, filter_single_selects):
        """Apply text filters on the item list."""
        if not filter_single_selects:
            return item_list
        filtered_items = []
        for item in item_list:
            if item.get("key_results", None):
                filtered_items.append(item)
                continue
            for item_ca in item["custom_attribute_values"]:
                if item_ca["ca_config_id"] == filter_single_selects["ca_config_id"]:
                    if item_ca["values"]:
                        item_ca_value = item_ca["values"][0].lower()
                        filter_ca_values = filter_single_selects["values"].lower()
                        if filter_ca_values.lower() in item_ca_value:
                            filtered_items.append(item)
        return filtered_items

    @staticmethod
    def map_ca_values(ca_input: list, configs: dict):
        """Map value IDs in ca_input to their actual labels using CustomAttributesConfig."""
        mapped = []
        print(configs)
        for attr in ca_input:
            ca_id = attr.get("ca_config_id")
            ca_type = attr.get("ca_config_type")
            cfg = configs.get(ca_id)
            if not cfg:
                continue

            # Build lookup map for this config's values
            value_map = {}
            if getattr(cfg, "value", None):
                for v in cfg.value:
                    if ca_type in ("singleselect", "multiselect"):
                        value_map[v["id"]] = v["value"]

            # Replace IDs with labels for select types, else keep as is
            raw_values = attr.get("value", [])
            resolved_values = (
                [value_map.get(v, v) for v in raw_values]
                if ca_type in ("singleselect", "multiselect")
                else raw_values
            )

            mapped.append(
                {
                    "ca_config_id": ca_id,
                    "ca_config_type": ca_type,
                    "values": resolved_values,
                }
            )

        return mapped

    @staticmethod
    def work_item_container_filter(okrs, filter_wic_ids):
        """Filter objectives based on work item container IDs."""
        if not filter_wic_ids:
            return okrs
        filtered_objectives = []
        for objective in okrs:
            if objective["work_item_container_id"] in filter_wic_ids:
                filtered_objectives.append(objective)
        return filtered_objectives


class MultiLevelOKRListsManager(MultiLevelOKR):
    """Class to handle the multi level okrs lists."""

    def fetch_multi_level_okr_filter_lists(self):
        """Fetch the multi level okr filter lists data."""
        with self.input_prepper.db_session() as db_session:
            try:
                self._fetch_wic(db_session)
            except ValueError as e:
                return bad_request_error(str(e), "CANNOT_FETCH_OKRS")
            objectives = self._fetch_objectives(db_session)
            if not objectives:
                return {
                    "child_objectives": [],
                    "parent_objectives": [],
                    "owners": [],
                }, HTTPStatus.OK
            self._fetch_wics(db_session, objectives)
            objectives = self._filter_objectives_by_wic_id(objectives)
            key_results = self._fetch_key_results(db_session, objectives)
            if not self.is_card_view:
                self._fetch_user_settings(db_session)
                self.get_ca_filter_list()
            self._process_objectives(objectives)
            self._process_key_results(key_results)
            okrs = list(self.objectives_map.values())
            primary_filtered = self.apply_primary_filters(okrs)
            result = self.get_filter_lists(primary_filtered)
            return result, HTTPStatus.OK

    def get_filter_lists(self, okrs):
        """Get the filters lists."""
        child_objectives, parent_objective_ids = self.get_child_objective_filter_list(
            okrs
        )
        parent_objectives = self.get_parent_objective_filter_list(
            okrs, parent_objective_ids
        )
        owners = self.get_owner_filter_list(okrs)
        wics = self.get_wic_list(okrs, self.wic_map)
        result = {
            "parent_objectives": parent_objectives,
            "child_objectives": child_objectives,
            "owners": owners,
            "ca_filters_list": self.ca_filter_list,
            "work_item_containers": wics,
        }
        return result

    @staticmethod
    def get_child_objective_filter_list(okrs):
        """Get child objectives filter list."""
        child_objectives = []
        parent_objective_ids = set()
        for objective in okrs:
            if objective["parent_objective_id"] is not None:
                child_objectives.append(
                    {
                        "id": objective["id"],
                        "parent_objective_id": objective["parent_objective_id"],
                        "name": objective["name"],
                    }
                )
                parent_objective_ids.add(objective["parent_objective_id"])
        return child_objectives, parent_objective_ids

    @staticmethod
    def get_parent_objective_filter_list(okrs, parent_objective_ids):
        """Get parent objectives filter list."""
        parent_objectives = []
        for objective in okrs:
            if objective["id"] in parent_objective_ids:
                parent_objectives.append(
                    {
                        "id": objective["id"],
                        "parent_objective_id": objective["parent_objective_id"],
                        "name": objective["name"],
                    }
                )
        return parent_objectives

    @staticmethod
    def get_owner_filter_list(okrs):
        """Get owner filter list."""
        owners = set()
        for objective in okrs:
            for kr in objective["key_results"]:
                if kr["app_owned_by"] is not None:
                    owners.add(kr["app_owned_by"])
            if objective["app_owned_by"] is not None:
                owners.add(objective["app_owned_by"])
        return list(owners)

    @staticmethod
    def get_wic_list(okrs, wic_map):
        """Get work item container filter list."""
        wic_list = []
        wic_set = set()
        for objective in okrs:
            wic_id = objective["work_item_container_id"]
            if wic_id not in wic_set:
                wic_set.add(wic_id)
                wic_list.append(wic_map[wic_id])
        return wic_list

    def get_ca_filter_list(self):
        """Get the custom attribute filter list."""
        self.get_ca_list_view_column_config()
        self.ca_filter_list = self.map_ca_filter_list()

    def get_ca_list_view_column_config(self):
        """Get the list view column config."""
        with self.input_prepper.db_session() as db_session:
            self._fetch_user_settings(db_session)
            for column_obj in self.list_view_column_config:
                if column_obj[
                    "column_type"
                ] == "custom_attribute" and not column_obj.get("hidden", False):
                    self.ca_columns_enabled.append(column_obj["id"])

    def map_ca_filter_list(self):
        """Map the custom attribute filter list."""
        ca_filter_list = []
        with self.input_prepper.db_session() as db_session:
            ca_records = (
                db_session.query(models.CustomAttributesConfig)
                .filter(
                    and_(
                        models.CustomAttributesConfig.is_deleted.is_(False),
                        models.CustomAttributesConfig.is_archived.is_(False),
                        self._get_tenant_filter(models.CustomAttributesConfig),
                    )
                )
                .all()
            )
        for ca in ca_records:
            ca_filter_list.append(
                {
                    "id": ca.id,
                    "label": ca.label,
                    "ca_config_type": ca.ca_config_type,
                    "tooltip": ca.tooltip,
                    "value": ca.value,
                }
            )
        return ca_filter_list
