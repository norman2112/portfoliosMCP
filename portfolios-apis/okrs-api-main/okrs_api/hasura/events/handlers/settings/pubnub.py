"""Handler for Settings operations for Pubnub."""


from okrs_api.hasura.events.handlers.base import Base
from okrs_api.integration_hub.auth import TokenFetcher
from okrs_api.pubnub.utils import get_tenant_channel_name, pubnub_push
from okrs_api.tenant_parser import TenantParser


class Handler(Base):
    """
    Handler for all Settings-related operations.

    Triggered by Settings:
    - Inserts
    - Updates
    """

    UPDATE_KEYS = ["level_config"]

    async def insert_event(self):
        """
        Perform code related to an INSERT.

        Take the following actions when a settings record is created:
        - send a pubnub event to any subscriber that might be listening for settings.
        """

        # A Setting has been created.
        # We need to send this event to subscribers of the tenant group id channel.
        return self._send_pubnub_event("insert")

    async def update_event(self):
        """
        Perform code related to an INSERT.

        Take the following actions when a settings record is created:
        - send a pubnub event to any subscriber that might be listening for settings.
        """

        # A Setting has been changed.
        # We need to send this event to subscribers of the tenant group id channel.
        return self._send_pubnub_event("update")

    def _send_pubnub_event(self, event_type):
        """Send a pubnub event to the tenant channel."""

        tenant_group = self.event_parser.find_value_for_key("tenant_group_id_str")

        if not tenant_group:
            tenant_group = self.event_parser.find_value_for_key("tenant_id_str")

        channel_name = get_tenant_channel_name(tenant_group)
        message = dict(id=self._setting_id, type="settings", action=event_type)

        pubnub_push(channel_name, message)

        return True

    def _tenant_parser(self):
        """Return the TenantParser for the tenant_id_str."""
        tenant_id_str = self.event_parser.find_value_for_key("tenant_id_str")
        return TenantParser(tenant_id_str)

    def _token_fetcher(self):
        """Return the token fetcher for admin credentials."""
        return TokenFetcher(
            client_session=self.client_session,
            app_settings=self.app_settings,
            admin=True,
        )

    @property
    def _setting_id(self):
        """Return the Setting ID of the Setting that was modified."""
        return self.event_parser.find_value_for_key("id")
