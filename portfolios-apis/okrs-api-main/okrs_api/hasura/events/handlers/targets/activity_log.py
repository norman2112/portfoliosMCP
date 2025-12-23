"""Handler for Targets Activity Log changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
    """
    Handle Targets events.

    Handle events for:
    - Insert
    - Update
    - Delete
    """

    UPDATE_KEYS = ["starts_at", "ends_at", "value"]

    def insert_event(self):
        """Handle the insertion event."""
        return self._record_to_activity_log()

    def update_event(self):
        """Handle the update event."""
        return self._record_to_activity_log()

    def delete_event(self):
        """Handle the delete event."""
        return self._record_to_activity_log()

    def _record_to_activity_log(self):
        """Instantiate and save a new activity log."""
        key_result_id = self.event_parser.find_value_for_key("key_result_id")
        key_result = self.db_session.query(models.KeyResult).get(key_result_id)
        objective_id = key_result.objective_id
        base_attribs = {"objective_id": objective_id, "key_result_id": key_result_id}
        additional_attr = {"key_result_name": key_result.name}
        log = self.activity_log_factory(
            base_attribs=base_attribs, additional_attr=additional_attr
        )
        self.db_session.add(log)
        return self._commit_db_session()
