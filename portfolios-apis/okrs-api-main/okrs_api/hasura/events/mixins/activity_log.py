"""Mixin and collaborators for activity log-related work."""

from open_alchemy import models

from okrs_api.utils import utc_timestamp


class ActivityLog:
    """Mixin for ActivityLog functionality."""

    APP_USER_KEYS_BY_OPERATION = {
        "insert": "app_created_by",
        "update": "app_last_updated_by",
        "delete": "app_last_updated_by",
    }

    def activity_log_factory(
        self, base_attribs=None, merge_info=None, additional_attr=None
    ):
        """
        Return a basic log entry, based on the parameters.

        :param dict base_attribs: the non-info attribs of this log
        :param dict merge_info: mergeable values into the `info` key
        :param dict additional_attr: mergeable values into the `info` key
        """
        merge_info = merge_info or {}
        base_attribs = base_attribs or {}
        deduced_attribs = {
            "info": self._info_data(merge_info),
            "action": self._action_name,
            "tenant_id_str": self.event_parser.tenant_id_str,
            "tenant_group_id_str": self.event_parser.tenant_group_id_str,
            "created_at": utc_timestamp(),
        }
        # Merge all attribs
        attribs = base_attribs | deduced_attribs | self._app_user_dict()
        if additional_attr:
            attribs["info"].update(additional_attr)
        return models.ActivityLog(**attribs)

    @property
    def _operation(self):
        return self.event_parser.operation

    @property
    def _action_name(self):
        return f"{self._operation}.{self.event_parser.table}"

    def _info_data(self, merge_info):
        """Generate the info data based on the operation."""
        return getattr(self, f"_{self._operation}_info")(merge_info)

    def _insert_info(self, merge_info):
        merge_info = merge_info.get("new", merge_info)
        return self._prepped_data("new") | merge_info

    def _update_info(self, merge_info):
        """Return the old data and the changed new data."""
        new_data = self._prepped_data("new") | merge_info.get("new", {})
        old_data = self._prepped_data("old") | merge_info.get("old", merge_info)
        changed = {k: new_data[k] for k in new_data if old_data.get(k) != new_data[k]}
        return {
            "new": changed,
            "old": old_data,
        }

    def _delete_info(self, merge_info):
        merge_info = merge_info.get("old", merge_info)
        return self._prepped_data("old") | merge_info

    def _prepped_data(self, type_key):
        """Prep and return the data from the event parser."""
        data = getattr(self.event_parser, f"{type_key}_data")
        prepper = InfoDataPrepper(data=data, table_name=self.event_parser.table)
        return prepper.prepped_data()

    def _app_user_dict(self):
        """
        Return the appropriate user column based on the operation.

        Return  `app_last_updated_by` and `app_created_by` fields,
        depending on the
        """
        user_key = self.APP_USER_KEYS_BY_OPERATION.get(self._operation)
        if not user_key:
            return {}
        return self.event_parser.subset_data([user_key])


class InfoDataPrepper:
    """Prepper for the info data that is sent by Hasura."""

    PREFIXABLE_KEYS = ["name", "progress_percentage", "value"]

    EVENT_DATA_KEYS = {
        "objectives": [
            "name",
            "starts_at",
            "ends_at",
            "parent_objective_id",
            "level_depth",
            "app_owned_by",
            "description",
            "rolled_up_progress_percentage",
        ],
        "key_results": [
            "name",
            "progress_percentage",
            "starting_value",
            "target_value",
            "starts_at",
            "ends_at",
            "objective_id",
            "app_owned_by",
            "description",
        ],
        "progress_points": [
            "measured_at",
            "value",
            "target_id",
            "key_result_progress_percentage",
            "objective_progress_percentage",
        ],
        "targets": ["id", "starts_at", "ends_at", "value"],
    }

    def __init__(self, data, table_name):
        """
        Initialize the prepper.

        :param dict data: the data to be prepped
        :param str table_name: the table name
        """
        self.data = data
        self.table_name = table_name

    def prepped_data(self):
        """Prep the data, prefixing it and slicing it to just what we need."""
        final_data = {}
        for key in self._keys_needed:
            new_key = self._prefixed_key(key)
            final_data[new_key] = self.data.get(key)
        return final_data

    @property
    def _keys_needed(self):
        """Return the keys needed for the table."""
        return self.EVENT_DATA_KEYS.get(self.table_name, [])

    @property
    def _record_type(self):
        """Return the record type (objective, key_result, etc)."""
        return self.table_name.removesuffix("s")

    def _prefixed_key(self, key):
        """
        Prefix the key with the record type if in the list.

        If not prefixable, simply return the original key.
        """

        if key not in self.PREFIXABLE_KEYS:
            return key

        return f"{self._record_type}_{key}"
