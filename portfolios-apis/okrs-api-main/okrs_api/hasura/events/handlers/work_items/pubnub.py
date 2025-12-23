"""Handler for Key Results Pubnub events."""
from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import pubnub_push, get_container_channel_name


class Handler(Base):
    """
    Handles Work Item delete.

    Handles the following operations:
    - Deletions
    """

    def __init__(self, *args, **kwargs):
        """Initialize the handler."""
        super().__init__(*args, **kwargs)

    # def insert_event(self):
    #     """Handle the insertion event."""
    #
    #     return self._send_pubnub_event("insert")
    #
    # def update_event(self):
    #     """Handle the update event."""
    #
    #     return self._send_pubnub_event("update")

    async def delete_event(self):
        """Handle the delete event."""
        return await self._send_pubnub_event("delete")

    async def _send_pubnub_event(self, event_type):
        """Send events to objectives and key results on change."""
        tenant_group_id_str = self.event_parser.find_value_for_key(
            "tenant_group_id_str"
        )
        tenant_id_str = self.event_parser.find_value_for_key("tenant_id_str")

        app_name = self.event_parser.find_value_for_key("app_name")
        external_id = self.event_parser.find_value_for_key("external_id")
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
