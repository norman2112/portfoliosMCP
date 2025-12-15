"""Handler for Key Results Pubnub events."""
from open_alchemy import models

from okrs_api.hasura.events.handler_utils.utils import send_events_to_objective_tree
from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import pubnub_push, get_container_channel_name


class Handler(Base):
    """
    Handles Key Results.

    Handles the following operations:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = [
        "starting_value",
        "target_value",
        "objective_id",
        "value_type",
        "starts_at",
        "ends_at",
        "data_source",
        "name",
        "app_owned_by",
        "description",
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

    # pylint: disable=unbalanced-tuple-unpacking

    def _send_pubnub_event(self, event_type):
        """Send events to objectives and key results on change."""

        (
            app_name,
            container_id,
            tenant_id_str,
            tenant_group_id_str,
        ) = self._get_work_item_container()

        if container_id is None:
            # Cannot send an event as there is no container
            return True

        channel_name = get_container_channel_name(
            tenant_id_str, tenant_group_id_str, app_name, container_id
        )

        old_objective = self.event_parser.old_data.get("objective_id")
        current_objective = self.event_parser.find_value_for_key("objective_id")
        kr_id = self.event_parser.find_value_for_key("id")

        if old_objective and (old_objective != current_objective):
            message = dict(
                id=old_objective, type="objectives", action="key_results_" + event_type
            )
            send_events_to_objective_tree(self.db_session, old_objective, message)

        if current_objective:
            message = dict(
                id=current_objective,
                type="objectives",
                action="key_results_" + event_type,
            )
            send_events_to_objective_tree(self.db_session, current_objective, message)

        message = dict(id=kr_id, type="key_results", action=event_type)
        pubnub_push(channel_name, message)
        return True

    def _get_work_item_container(self):
        obj_id = self.event_parser.find_value_for_key("objective_id")
        obj = self.db_session.query(models.Objective).get(obj_id)
        if not obj:
            # Very unlikely, but could be part of cascading delete
            return "", None, "", ""
        wic = (
            self.db_session.query(models.WorkItemContainer)
            .filter_by(id=obj.work_item_container_id)
            .first()
        )
        return wic.app_name, wic.external_id, wic.tenant_id_str, wic.tenant_group_id_str
