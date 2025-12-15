"""Handler for Settings Activity Log changes."""

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
    """
    Handle Settings events.

    Handle events for:
    - Updates
    """

    UPDATE_KEYS = [
        "roll_up_progress",
    ]

    def update_event(self):
        """Handle the update event."""
        merge_info = {
            "new": {
                "roll_up_progress": self.event_parser.find_value_for_key(
                    "roll_up_progress"
                )
            },
            "old": {
                "roll_up_progress": self.event_parser.old_data.get("roll_up_progress")
            },
        }
        base_attribs = {
            "last_updated_by": self.event_parser.new_data.get("last_updated_by"),
            "created_by": self.event_parser.new_data.get("last_updated_by"),
        }
        return self._record_to_activity_log(merge_info, base_attribs)

    def _record_to_activity_log(self, merge_info, base_attribs):
        """Instantiate and save a new activity log."""

        log = self.activity_log_factory(
            merge_info=merge_info,
            base_attribs=base_attribs,
        )
        self.db_session.add(log)
        return self._commit_db_session()
