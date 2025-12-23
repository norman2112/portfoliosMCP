"""Handler for user settings Activity Log changes."""

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
    """
    Handle Objective events.

    Handle events for:
    - Insertions
    - Updates
    """

    UPDATE_KEYS = ["user_id", "app_user_id", "value", "type"]

    def insert_event(self):
        """Handle the insertion event."""
        return self._record_to_activity_log()

    def update_event(self):
        """Handle the update event."""
        return self._record_to_activity_log()

    @property
    def _action_name(self):
        return (
            f"{self._operation}.{self.event_parser.find_value_for_key('type')}."
            f"user_settings"
        )

    def _record_to_activity_log(self):
        """Instantiate and save a new activity log."""
        log = self.activity_log_factory(
            merge_info={
                "old": self.event_parser.old_data,
                "new": self.event_parser.new_data,
            },
        )

        self.db_session.add(log)
        return self._commit_db_session()
