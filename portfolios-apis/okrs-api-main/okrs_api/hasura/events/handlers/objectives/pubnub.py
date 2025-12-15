"""Handler for Objectives Pubnub events."""

from okrs_api.hasura.events.handler_utils.utils import send_events_to_objective_tree
from okrs_api.hasura.events.handlers.base import Base


class Handler(Base):
    """
    Handle Objective events.

    Handle events for:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = [
        "name",
        "starts_at",
        "ends_at",
        "parent_objective_id",
        "level_depth",
        "app_owned_by",
        "description",
    ]

    def insert_event(self):
        """Handle the insertion event."""

        return self._send_pubnub_event("insert")

    def update_event(self):
        """Handle the update event."""

        return self._send_pubnub_event("update")

    def delete_event(self):
        """Handle delete event."""

        return self._send_pubnub_event("delete")

    def _send_pubnub_event(self, event_type):
        objective_id = self.event_parser.find_value_for_key("id")
        message = dict(id=objective_id, type="objectives", action=event_type)
        send_events_to_objective_tree(self.db_session, objective_id, message)
        return True
