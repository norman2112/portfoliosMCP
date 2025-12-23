"""Handlers for ProgressPoint changes."""

from open_alchemy import models

from okrs_api.hasura.events.handler_utils.utils import send_events_to_objective_tree
from okrs_api.hasura.events.handlers.base import Base
from okrs_api.pubnub.utils import get_container_channel_name, pubnub_push


class Handler(Base):
    """
    Handler Mixin that writes progress percentages.

    Write to the Progress Point, KeyResult and Objective.

    Handles Progress Point:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = ["measured_at", "value", "comment", "deleted_at_epoch"]

    def __init__(self, *args, **kwargs):
        """Initialize this class with additional params."""
        super().__init__(*args, **kwargs)
        # The following attribs are used for memoization.
        self._objective = None

    def insert_event(self):
        """
        Handle the insert event.

        A Progress Point has been added.
        """
        return self._send_pubnub_event("insert")

    def update_event(self):
        """
        Handle the update event.

        A Progress Point has been updated.
        """
        return self._send_pubnub_event("update")

    def delete_event(self):
        """
        Handle the delete event.

        A Progress Point has been deleted.
        """
        return self._send_pubnub_event("delete")

    def objective(self):
        """Get the Objective from the Key Result, if the Key Result exists."""
        key_result = self.key_result()
        if not key_result:
            return None

        if not self._objective:
            self._objective = self.db_session.query(models.Objective).get(
                key_result.objective_id
            )

        return self._objective

    def key_result(self):
        """Get the Key Result for the Progress Point."""

        return self.db_session.query(models.KeyResult).get(self._key_result_id)

    def work_item_container(self):
        """Get the associated work item container for this progress point."""

        objective = self.objective()

        if not objective:
            return None

        return self.db_session.query(models.WorkItemContainer).get(
            objective.work_item_container_id
        )

    @property
    def _key_result_id(self):
        """Return the key result id from the event data."""

        return self.event_parser.find_value_for_key("key_result_id")

    @property
    def _objective_id(self):
        """Return the objective id from the objective."""
        objective = self.objective()
        if not objective:
            return None

        return objective.id

    def _send_pubnub_event(self, event_type):
        """Send pubnub events on Progress Point changes."""

        tenant_group_id_str = self.event_parser.find_value_for_key(
            "tenant_group_id_str"
        )
        tenant_id_str = self.event_parser.find_value_for_key("tenant_id_str")

        wic = self.work_item_container()
        if not wic:
            # Cannot find a work item container, cannot send message
            return True

        app_name, container_id = wic.app_name, wic.external_id

        channel_name = get_container_channel_name(
            tenant_id_str, tenant_group_id_str, app_name, container_id
        )

        progress_id = self.event_parser.find_value_for_key("id")
        message = dict(id=progress_id, type="progress_points", action=event_type)
        pubnub_push(channel_name, message)

        event = f"progress_point_{event_type}"

        key_result = self.key_result()
        if key_result:
            message = dict(id=key_result.id, type="key_results", action=event)
            pubnub_push(channel_name, message)

        objective = self.objective()
        if objective:
            message = dict(id=objective.id, type="objectives", action=event)
            send_events_to_objective_tree(self.db_session, objective.id, message)

        return True
