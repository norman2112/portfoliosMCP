"""Handler for Pubnub for CA Value changes."""


from open_alchemy import models
from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog
from okrs_api.pubnub.utils import pubnub_push, get_container_channel_name


class Handler(Base, ActivityLog):
    """
    Handle Objective events.

    Handle events for:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = ["ca_config_id", "object_id", "value", "object_type"]

    def insert_event(self):
        """Handle the insertion event."""
        return self._send_pubnub_event("custom_attributes_insert")

    def update_event(self):
        """Handle the update event."""
        return self._send_pubnub_event("custom_attributes_update")

    #
    # def internal_delete_event(self):
    #     """
    #     Handle an internal delete event.
    #
    #     An internal delete event is not triggered by Hasura, but rather, by
    #     the internals of OKRS-api, posing as a Hasura delete event.
    #     """
    #     return self._record_to_activity_log()

    def _send_pubnub_event(self, event_type):
        """Send a pubnub event for object."""

        object_id = self.event_parser.find_value_for_key("object_id")
        object_type = self.event_parser.find_value_for_key("object_type")
        if object_type == "objective":
            message = dict(id=object_id, type="objectives", action=event_type)
            channel_name = self._get_channel_name(object_id)
            pubnub_push(channel_name, message)
        else:
            key_result = self.db_session.query(models.KeyResult).get(object_id)
            channel_name = self._get_channel_name(key_result.objective_id)
            message = dict(id=key_result.id, type="key_results", action=event_type)
            pubnub_push(channel_name, message)
        return True

    def _get_channel_name(self, objective_id):
        """Get Channel name by user objective id."""
        (
            app_name,
            container_id,
            tenant_id_str,
            tenant_group_id_str,
        ) = self._get_work_item_container(objective_id)
        channel_name = get_container_channel_name(
            tenant_id_str, tenant_group_id_str, app_name, container_id
        )

        return channel_name

    def _get_work_item_container(self, objective_id):
        """Get WIC from key result."""

        obj = self.db_session.query(models.Objective).get(objective_id)
        if not obj:
            # Very unlikely, but could be part of cascading delete
            return "", None, "", ""
        wic = (
            self.db_session.query(models.WorkItemContainer)
            .filter_by(id=obj.work_item_container_id)
            .first()
        )
        return wic.app_name, wic.external_id, wic.tenant_id_str, wic.tenant_group_id_str
