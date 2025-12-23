"""Handler for Key Results Pubnub events."""
from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import pubnub_push, get_container_channel_name


class Handler(Base):
    """
    Handles Key Results mapping events.

    Handles the following operations:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = [
        "key_result_id",
        "work_item_id",
    ]

    def __init__(self, *args, **kwargs):
        """Initialize the handler."""
        super().__init__(*args, **kwargs)

    def insert_event(self):
        """Handle the insertion event."""

        return self._send_pubnub_event("insert")

    def update_event(self):
        """Handle the update event."""

        return self._send_pubnub_event("update")

    def delete_event(self):
        """Handle the delete event."""
        return self._send_pubnub_event("delete")

    def _send_pubnub_event(self, event_type):
        """Send events to objectives and key results on change."""
        tenant_group_id_str = self.event_parser.find_value_for_key(
            "tenant_group_id_str"
        )
        tenant_id_str = self.event_parser.find_value_for_key("tenant_id_str")

        work_item = self._get_work_item()
        if not work_item:
            # Cannot send an event as there is no valid work item
            return True

        app_name = work_item.app_name
        external_id = work_item.external_id

        channel_name = get_container_channel_name(
            tenant_id_str, tenant_group_id_str, app_name, external_id
        )

        message = dict(
            id=self.event_parser.find_value_for_key("id"),
            external_id=external_id,
            type="key_result_work_item_mappings",
            action=event_type,
        )

        pubnub_push(channel_name, message)

        return True

    def _get_work_item(self):
        work_item_id = self.event_parser.find_value_for_key("work_item_id")
        return self.db_session.query(models.WorkItem).get(work_item_id)
