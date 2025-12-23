"""Handler for Key Results Activity Log changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
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
        """
        Handle the insertion event.

        Merge in the objective info for the current objective.
        """
        merge_info = {"new": self._current_objective_merge_info()}
        return self._record_to_activity_log(merge_info)

    def update_event(self):
        """
        Handle the update event.

        Merge objective information for both new and old keys.
        """
        current_info = self._current_objective_merge_info()
        merge_info = {
            "new": current_info,
            "old": current_info,
        }

        if self._objective_has_changed():
            merge_info["old"] = self._old_objective_merge_info()

        return self._record_to_activity_log(merge_info)

    def internal_delete_event(self):
        """Handle the delete event."""
        merge_info = {"old": self._old_objective_merge_info()}
        return self._record_to_activity_log(merge_info)

    def _record_to_activity_log(self, merge_info):
        """Instantiate and save a new activity log."""
        objective_id = self.event_parser.find_value_for_key("objective_id")
        objective = self._get_objective(objective_id)
        if not objective:
            # Assume this is part of a cascading delete, and does not need to
            # have an activity log.
            return True

        log = self.activity_log_factory(
            base_attribs={
                "objective_id": objective_id,
                "key_result_id": self.event_parser.find_value_for_key("id"),
            },
            merge_info=merge_info,
        )
        self.db_session.add(log)
        return self._commit_db_session()

    def _objective_has_changed(self):
        """Determine if the objective was changed."""
        return self.event_parser.in_changed_keys(["objective_id"])

    def _get_objective(self, objective_id):
        if not objective_id:
            return None

        return self.db_session.query(models.Objective).get(objective_id)

    def _objective_merge_info(self, objective_id=None):
        """
        Return info from the related objective.

        If the objective is not found, return a blank dict.
        """
        objective = self._get_objective(objective_id)
        if not objective:
            return None

        return {
            "objective_name": objective.name,
            "objective_progress_percentage": objective.progress_percentage,
        }

    def _current_objective_merge_info(self):
        """Return the objective merge info for the current objective."""
        current_objective_id = self.event_parser.find_value_for_key("objective_id")
        return self._objective_merge_info(current_objective_id) or {}

    def _old_objective_merge_info(self):
        """Return the objective merge info for the old objective."""
        old_objective_id = self.event_parser.old_data.get("objective_id")
        return self._objective_merge_info(old_objective_id) or {}
