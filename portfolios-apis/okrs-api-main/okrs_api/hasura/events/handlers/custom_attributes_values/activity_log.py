"""Handler for Objectives Activity Log changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
    """
    Handle Objective events.

    Handle events for:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = ["ca_config_id", "object_id", "value", "object_type"]

    def insert_event(self):
        """Handle the insertion event."""
        return self._record_to_activity_log()

    def update_event(self):
        """Handle the update event."""
        return self._record_to_activity_log()

    def internal_delete_event(self):
        """
        Handle an internal delete event.

        An internal delete event is not triggered by Hasura, but rather, by
        the internals of OKRS-api, posing as a Hasura delete event.
        """
        return self._record_to_activity_log()

    @property
    def _action_name(self):
        return (
            f"{self._operation}.{self.event_parser.find_value_for_key('object_type')}."
            f"custom_attributes"
        )

    def _record_to_activity_log(self):
        """Instantiate and save a new activity log."""
        object_id = self.event_parser.find_value_for_key("object_id")
        object_type = self.event_parser.find_value_for_key("object_type")
        if object_type == "objective":
            base_attribs = {"objective_id": object_id}
        else:
            key_result = self.db_session.query(models.KeyResult).get(object_id)
            objective_id = key_result.objective_id
            base_attribs = {"objective_id": objective_id, "key_result_id": object_id}
            key_result_name = key_result.name
            self.event_parser.old_data["key_result_name"] = key_result_name
            self.event_parser.new_data["key_result_name"] = key_result_name
        log = self.activity_log_factory(
            base_attribs=base_attribs,
            merge_info={
                "old": self.event_parser.old_data,
                "new": self.event_parser.new_data,
            },
        )

        self.db_session.add(log)
        return self._commit_db_session()

    def _get_ca_config_info(self):
        """Return the ca_config_id and ca_config_name."""
        ca_config_id = self.event_parser.find_value_for_key("ca_config_id")
        ca_config = self.db_session.query(models.CustomAttributesConfig).get(
            ca_config_id
        )

        return {
            "ca_config_id": ca_config.id,
            "ca_config_label": ca_config.label,
            "ca_config_value": ca_config.value,
            "ca_config_type": ca_config.ca_config_type,
            "ca_config_is_archived": ca_config.is_archived,
            "ca_config_is_deleted": ca_config.is_deleted,
        }

    def _insert_info(self, merge_info):
        merge_info = merge_info.get("new", merge_info)
        merge_info.update(self._get_ca_config_info())
        return self._prepped_data("new") | merge_info

    def _update_info(self, merge_info):
        """Return the old data and the changed new data."""
        new_data = self._prepped_data("new") | merge_info.get("new", {})
        old_data = self._prepped_data("old") | merge_info.get("old", merge_info)
        changed = {k: new_data[k] for k in new_data if old_data.get(k) != new_data[k]}
        info = {
            "new": changed,
            "old": old_data,
        }
        info.update(self._get_ca_config_info())
        object_type = self.event_parser.find_value_for_key("object_type")
        if object_type == "keyresult":
            info.update({"key_result_name": old_data["key_result_name"]})
        return info

    def _delete_info(self, merge_info):
        merge_info = merge_info.get("old", merge_info)
        merge_info.update(self._get_ca_config_info())
        return self._prepped_data("old") | merge_info
