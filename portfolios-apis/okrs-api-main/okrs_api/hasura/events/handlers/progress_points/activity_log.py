"""Handler for Objectives Activity Log changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
    """
    Handle ProgressPoint events.

    Handles the following:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = ["measured_at", "value"]

    def __init__(self, *args, **kwargs):
        """Initialize for the base handler."""
        super().__init__(*args, **kwargs)
        # for memoizing
        self._progress_point = None
        self._key_result = None
        self._objective = None

    def insert_event(self):
        """Handle the insertion event."""
        return self._record_to_activity_log()

    def update_event(self):
        """Handle the update event."""
        return self._record_to_activity_log()

    def internal_delete_event(self):
        """Handle an internal delete event."""
        return self._record_to_activity_log()

    def _record_to_activity_log(self):
        """Instantiate and save a new activity log."""

        if not self.key_result():
            # Assumed to be the result of a cascading delete.
            # So this should be a no-op, as it is not reflective of a
            # specific user interaction that needs to be logged.
            return True

        log = self.activity_log_factory(
            base_attribs=self._make_base_attribs(),
            merge_info=self._make_merge_info(),
        )

        self.db_session.add(log)
        return self._commit_db_session()

    def _insert_info(self, merge_info):
        merge_info = merge_info.get("new", merge_info)
        # For when a progress entry is made for a date previous to an existing entry date
        if (
            merge_info.get("key_result_progress_percentage") is None
            and merge_info.get("key_result_progress_percentage") is None
        ):
            merge_info[
                "key_result_progress_percentage"
            ] = self.key_result().progress_percentage
            merge_info[
                "objective_progress_percentage"
            ] = self.objective().progress_percentage
        return self._prepped_data("new") | merge_info

    def _update_info(self, merge_info):
        """Return the old data and the changed new data."""
        new_data = self._prepped_data("new") | merge_info.get("new", {})
        old_data = self._prepped_data("old") | merge_info.get("old", merge_info)
        if (
            old_data["key_result_progress_percentage"] == 0
            and old_data["objective_progress_percentage"] == 0
        ):
            old_data[
                "key_result_progress_percentage"
            ] = self.key_result().progress_percentage
            old_data[
                "objective_progress_percentage"
            ] = self.objective().progress_percentage
            new_data[
                "key_result_progress_percentage"
            ] = self.key_result().progress_percentage
            new_data[
                "objective_progress_percentage"
            ] = self.objective().progress_percentage
        changed = {k: new_data[k] for k in new_data if old_data.get(k) != new_data[k]}
        return {
            "new": changed,
            "old": old_data,
        }

    def _delete_info(self, merge_info):
        merge_info = merge_info.get("old", merge_info)
        merge_info[
            "key_result_progress_percentage"
        ] = self.key_result().progress_percentage
        merge_info[
            "objective_progress_percentage"
        ] = self.objective().progress_percentage
        return self._prepped_data("old") | merge_info

    def progress_point(self):
        """Return the progress point represented in the event data."""
        if not self._progress_point:
            self._progress_point = self.db_session.query(models.ProgressPoint).get(
                self.event_parser.find_value_for_key("id")
            )

        return self._progress_point

    def key_result(self):
        """Return the key result attached to the progress point."""

        if not self._key_result:
            self._key_result = self.db_session.query(models.KeyResult).get(
                self.event_parser.find_value_for_key("key_result_id")
            )

        return self._key_result

    def objective(self):
        """Return the objective attached to the key result."""
        if not self.key_result():
            return None

        if not self._objective:
            self._objective = self.key_result().objective

        return self._objective

    def _make_base_attribs(self):
        """Make the base attribs, combining event data and db queries."""
        attribs = {
            "progress_point_id": self.event_parser.find_value_for_key("id"),
            "key_result_id": self.event_parser.find_value_for_key("key_result_id"),
        }
        if self.objective():
            attribs["objective_id"] = self.objective().id

        return attribs

    def _make_merge_info(self):
        """Make the merge info, combining event data and db queries."""
        attribs = {"key_result_name": self.key_result().name}

        if self.objective():
            attribs["objective_name"] = self.objective().name

        return attribs
