"""Handler for all operations on the KeyResults."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.progress import ProgressMixin
from okrs_api.utils import minmax


class Handler(Base, ProgressMixin):
    """
    Handler that writes progress percentages when Key Results change.

    Writes percentage for relevant Key Result events.
    Triggered by Key Result:
    - Insertions
    - Updates
    - Deletions
    """

    UPDATE_KEYS = ["starting_value", "target_value", "objective_id", "value_type"]

    def insert_event(self):
        """
        Handle the insert event.

        A Key Result has been added.
        """
        return self._update_progress()

    def update_event(self):
        """
        Handle the update event.

        A Key Result has been updated.
        """
        return self._update_progress()

    def delete_event(self):
        """
        Handle the delete event.

        A Key Result has been deleted.
        """
        if not self.objective():
            return True

        self._update_objective_progress()
        return self._commit_db_session()

    def objective(self):
        """Return the Objective, parsed from the event data."""
        return self.db_session.query(models.Objective).get(self._objective_id)

    def old_objective(self):
        """Return the Objective, parsed from the old data."""
        return self.db_session.query(models.Objective).get(self._old_objective_id)

    def _calculate_old_objective_progress(self):
        """Calculate the progress percentage, given an Old Objective."""
        key_results = (
            self.db_session.query(models.KeyResult)
            .filter_by(objective_id=self._old_objective_id, deleted_at_epoch=0)
            .all()
        )

        if len(key_results) == 0:
            # No key results means no progress. (0)
            return 0

        progress_sum = sum(minmax(kr.progress_percentage) for kr in key_results)
        return progress_sum / len(key_results)

    def _update_old_objective_progress(self):
        """Update the progress for the Old Objective."""
        self._update_progress_percentage(
            instance=self.old_objective(),
            calculator_func=self._calculate_old_objective_progress,
        )

    def _update_progress(self):
        """
        Commit progress percentages on Key Result and Objective.

        Also write-back the progress point progress percentages back to the
        event data.
        """
        if not self.objective():
            return True

        self._update_key_result_progress()
        if self._old_objective_id:
            self._update_old_objective_progress()
        self._update_objective_progress()
        status = self._commit_db_session()
        self._writeback_progress()
        return status

    @property
    def _objective_id(self):
        """Return the objective id from the event data."""
        return self.event_parser.find_value_for_key("objective_id")

    @property
    def _old_objective_id(self):
        """Return the objective id from the old data."""
        return self.event_parser.old_data.get("objective_id")

    @property
    def _key_result_id(self):
        """Return the Key Result id from the event data."""
        return self.event_parser.find_value_for_key("id")

    def _writeback_progress(self):
        """Write back the progress percentages to the event_parser."""
        key_result = self.key_result()
        if not key_result:
            return

        self.event_parser.writeback(
            {
                "progress_percentage": key_result.progress_percentage,
            }
        )
