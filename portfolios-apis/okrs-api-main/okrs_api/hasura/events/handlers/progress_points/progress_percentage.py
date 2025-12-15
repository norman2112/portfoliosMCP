"""Handlers for ProgressPoint changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.progress import ProgressMixin


class Handler(Base, ProgressMixin):
    """
    Handler Mixin that writes progress percentages.

    Write to the Progress Point, KeyResult and Objective.

    Handles Progress Point:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = ["measured_at", "value"]

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
        return self._update_progress()

    def update_event(self):
        """
        Handle the update event.

        A Progress Point has been updated.
        """
        return self._update_progress()

    def delete_event(self):
        """
        Handle the delete event.

        A Progress Point has been deleted.
        """
        return self._update_progress()

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

    def _update_progress(self):
        """
        Write progress percentages to the database.

        - Find Key Result from the event data.
        - Calculate and commit the progress percentage(s) for Objective,
        Key Result, and the Progress Point.
        - Also store all progress percentages in the progress point itself.
        """

        if not self.objective():
            # a no-op. There is no objective.
            return True

        self._update_key_result_progress()
        self._update_objective_progress()
        self._update_progress_point_percentages()
        return self._commit_db_session()

    def _update_progress_point_percentages(self):
        """
        Update the progress point percentages.

        If the progress point exists, and the progress points percentages have
        changed, set the progress percentage values and add the progress point
        to the db_session.

        This will also write back the data to the event parser.
        """

        pp = self.latest_progress_point()
        if not pp:
            return

        existing_percentages = (
            pp.key_result_progress_percentage,
            pp.objective_progress_percentage,
        )
        calculated_percentages = (
            self.key_result().progress_percentage,
            self.objective().progress_percentage,
        )

        if existing_percentages == calculated_percentages:
            return

        (
            pp.key_result_progress_percentage,
            pp.objective_progress_percentage,
        ) = calculated_percentages
        self.db_session.add(pp)
        self._writeback_progress(pp)

    def _writeback_progress(self, progress_point):
        """Write back the progress to the progress point."""
        objective_progress = progress_point.objective_progress_percentage
        key_result_progress = progress_point.key_result_progress_percentage
        self.event_parser.writeback(
            {
                "objective_progress_percentage": objective_progress,
                "key_result_progress_percentage": key_result_progress,
            }
        )
