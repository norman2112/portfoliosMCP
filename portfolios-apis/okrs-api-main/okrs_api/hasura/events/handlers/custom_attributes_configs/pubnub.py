"""Handler for Settings operations for Pubnub."""


from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import get_tenant_channel_name, pubnub_push


class Handler(Base):
    """
    Handler for all CustomAttributesConfig-related operations.

    Triggered by Settings:
    - Inserts
    - Updates
    - Deletes
    """

    UPDATE_KEYS = [
        "is_archived",
        "is_default",
        "is_deleted",
        "is_keyresult",
        "is_objective",
        "is_mandatory_keyresult",
        "is_mandatory_objective",
        "label",
        "tooltip",
        "value",
    ]

    async def insert_event(self):
        """
        Perform code related to an INSERT.

        Take the following actions when a settings record is created:
        - send a pubnub event to any subscriber that might be listening for settings.
        """

        return self._send_pubnub_event("insert")

    async def update_event(self):
        """
        Perform code related to an UPDATE.

        Take the following actions when a settings record is created:
        - send a pubnub event to any subscriber that might be listening for settings.
        """

        return self._send_pubnub_event("update")

    async def delete_event(self):
        """
        Perform code related to an DELETE.

        Take the following actions when a settings record is created:
        - send a pubnub event to any subscriber that might be listening for settings.
        """

        return self._send_pubnub_event("delete")

    def _send_pubnub_event(self, event_type):
        """Send a pubnub event to the tenant channel."""

        tenant_group_id_str = self.event_parser.find_value_for_key(
            "tenant_group_id_str"
        )
        channel_name = get_tenant_channel_name(tenant_group_id_str)
        message = dict(
            id=self._config_id, type="custom_attributes_configs", action=event_type
        )

        pubnub_push(channel_name, message)

        return True

    @property
    def _config_id(self):
        """Return the Setting ID of the Setting that was modified."""
        return self.event_parser.find_value_for_key("id")
