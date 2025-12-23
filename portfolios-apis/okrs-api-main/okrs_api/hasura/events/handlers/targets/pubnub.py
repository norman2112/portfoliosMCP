"""Handler for Targets operations for Pubnub."""

from open_alchemy import models
from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import get_container_channel_name, pubnub_push


class Handler(Base):
    """
    Handler for all Target related operations.

    Triggered by Targets:
    - Insert
    - Update
    - Delete
    """

    UPDATE_KEYS = ["starts_at", "ends_at", "value"]

    def __init__(self, *args, **kwargs):
        """Initialize the handler."""
        super().__init__(*args, **kwargs)

    async def insert_event(self):
        """Handle the insert event."""
        return self._send_pubnub_event("targets_insert")

    async def update_event(self):
        """Handle the update event."""
        return self._send_pubnub_event("targets_update")

    async def delete_event(self):
        """Handle the delete event."""
        return self._send_pubnub_event("targets_delete")

    def _send_pubnub_event(self, event_type):
        """Send a pubnub event for object."""

        key_result_id = self.event_parser.find_value_for_key("key_result_id")
        key_result = self.db_session.query(models.KeyResult).get(key_result_id)
        objective = key_result.objective
        wic = objective.work_item_container

        channel_name = get_container_channel_name(
            wic.tenant_id_str, wic.tenant_group_id_str, wic.app_name, wic.external_id
        )
        message = dict(id=key_result.id, type="key_results", action=event_type)
        pubnub_push(channel_name, message)

        return True
