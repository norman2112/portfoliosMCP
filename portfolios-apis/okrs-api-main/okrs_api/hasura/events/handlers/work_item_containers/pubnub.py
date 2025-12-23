"""Event handler for all WorkItemContainer operations."""

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import get_container_channel_name, pubnub_push


class Handler(Base):
    """Handler for the WorkItemContainer operations."""

    UPDATE_KEYS = [
        "level_depth_default",
        "objective_editing_levels",
        "external_id",
        "external_title",
    ]

    def insert_event(self):
        """Send pubnub event on insert."""

        return self._send_pubnub_event("insert")

    def update_event(self):
        """Send pubnub event on insert."""

        return self._send_pubnub_event("update")

    @property
    def tenant_id_str(self):
        """Return the `tenant_id_str` that was passed in."""
        return self.event_parser.find_value_for_key("tenant_id_str")

    @property
    def tenant_group_id_str(self):
        """Return the `tenant_group_id_str` that was passed in."""
        return self.event_parser.find_value_for_key("tenant_group_id_str")

    def _send_pubnub_event(self, event_type):
        """Send the pubnub event for this event."""
        app_name = self.event_parser.find_value_for_key("app_name")
        container_id = self.event_parser.find_value_for_key("external_id")

        channel_name = get_container_channel_name(
            self.tenant_id_str, self.tenant_group_id_str, app_name, container_id
        )

        wic_id = self.event_parser.find_value_for_key("id")
        external_id = self.event_parser.find_value_for_key("external_id")
        message = dict(
            id=wic_id,
            external_id=external_id,
            type="work_item_containers",
            action=event_type,
        )
        pubnub_push(channel_name, message)

        return True
