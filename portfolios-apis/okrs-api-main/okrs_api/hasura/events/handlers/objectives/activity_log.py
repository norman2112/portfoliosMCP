"""Handler for Objectives Activity Log changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
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
        "rolled_up_progress_percentage",
    ]

    def insert_event(self):
        """Handle the insertion event."""
        return self._record_to_activity_log()

    def update_event(self):
        """Handle the update event."""
        return self._record_to_activity_log()

    def internal_delete_event(self):
        """
        Handle an internal delete event.

        An internal delete event is not triggered by Hasura, but rather, by
        the internals of OKRS-api, posing as a Hasura delete event.
        """
        return self._record_to_activity_log()

    def _record_to_activity_log(self):
        """Instantiate and save a new activity log."""
        log = self.activity_log_factory(
            base_attribs={"objective_id": self.event_parser.find_value_for_key("id")},
            merge_info={
                "new": {
                    "parent_objective_name": self._get_parent_objective_name(),
                },
                "old": {
                    "parent_objective_name": self._get_parent_objective_name(old=True),
                },
            },
        )
        self.db_session.add(log)
        return self._commit_db_session()

    def _get_parent_objective_name(self, old=False):
        """
        Return the parent objective name, if a parent objective exists.

        :param bool old: get the old parent objective if True
        """

        parent_objective_id = (
            self.event_parser.old_data.get("parent_objective_id")
            if old
            else self.event_parser.find_value_for_key("parent_objective_id")
        )

        if not parent_objective_id:
            return None

        parent_objective = self.db_session.query(models.Objective).get(
            parent_objective_id
        )

        if not parent_objective:
            return None

        return parent_objective.name
