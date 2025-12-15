"""Handler for rolling up progress for Objectives."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.utils import minmax


class Handler(Base):
    """
    Handler that calculates and writes rolled-up progress percentages.

    Triggered when an Objective's progress changes.
    """

    UPDATE_KEYS = ["parent_objective_id", "progress_percentage", "deleted_at_epoch"]
    # TODO: Check if this is really needed since just adding an objectives
    #  does not changed the rolled up progress

    def insert_event(self):
        """
        Handle the insert event.

        An Objective has been added.
        """
        self.roll_up_progress_percentage(self.event_parser.find_value_for_key("id"))
        status = self._commit_db_session()
        return status

    def update_event(self):
        """
        Handle the update event.

        An Objective has been updated.
        """
        self.roll_up_progress_percentage(self.event_parser.find_value_for_key("id"))
        status = self._commit_db_session()
        return status

    # TODO: Check if this is really needed
    def delete_event(self):
        """
        Handle the delete event.

        An Objective has been deleted.
        """
        self.roll_up_progress_percentage(self.event_parser.find_value_for_key("id"))
        status = self._commit_db_session()
        return status

    def _rollup_progress(self):
        """Roll up progress percentages."""
        self.roll_up_progress_percentage(self.event_parser.find_value_for_key("id"))
        status = self._commit_db_session()
        return status

    def fetch_child_objectives(self, objective_id):
        """Fetch all the active child objectives for the given objective_id."""
        child_objectives = (
            self.db_session.query(
                models.Objective.id,
                models.Objective.progress_percentage,
                models.Objective.rolled_up_progress_percentage,
            )
            .filter_by(parent_objective_id=objective_id, deleted_at_epoch=0)
            .all()
        )
        return child_objectives

    def get_rolled_up_progress_percentage(self, objective):
        """
        Calculate the rolled-up progress percentage for a given Objective.

        Takes into account its child objectives and key results.
        """

        progress_percentage = objective.progress_percentage
        child_objectives = self.fetch_child_objectives(objective.id)
        rolled_up_obj_progress_percentage = objective.progress_percentage

        if child_objectives:
            child_objectives_progress_sum = sum(
                minmax(child_objective.rolled_up_progress_percentage)
                for child_objective in child_objectives
            )
            child_objs_progress_percentage = round(
                child_objectives_progress_sum / len(child_objectives)
            )

            key_results = (
                self.db_session.query(models.KeyResult)
                .filter_by(objective_id=objective.id, deleted_at_epoch=0)
                .all()
            )

            if len(key_results) == 0:
                # No key results means no progress. (0)
                return child_objs_progress_percentage

            rolled_up_obj_progress_percentage = round(
                (progress_percentage + child_objs_progress_percentage) / 2
            )
        return rolled_up_obj_progress_percentage

    def roll_up_progress_percentage(self, objective_id):
        """
        Roll up the progress for all objectives iteratively.

        Commits each objective's update as it is processed.
        """
        if not objective_id:
            return

        current_id = objective_id
        first_iteration = True
        while current_id:
            with self.db_session as db_session:
                # Fetch the current objective
                if first_iteration:
                    objective = (
                        db_session.query(models.Objective)
                        .filter_by(
                            id=current_id
                        )  # Just remove deleted_at_epoch filter for delete objective event???
                        .first()
                    )
                else:
                    objective = (
                        db_session.query(models.Objective)
                        .filter_by(id=current_id, deleted_at_epoch=0)
                        .first()
                    )
                if not objective:
                    break  # Stop if the objective doesn't exist

                # Calculate rolled-up progress percentage
                rolled_up_progress_percentage = self.get_rolled_up_progress_percentage(
                    objective
                )
                objective.rolled_up_progress_percentage = rolled_up_progress_percentage

                # Commit this objective's update to the database
                db_session.add(objective)
                self._commit_db_session()

                # Move to the parent objective
                if first_iteration and objective.parent_objective_id is None:
                    current_id = self.event_parser.old_data.get(
                        "parent_objective_id", None
                    )
                else:
                    current_id = objective.parent_objective_id
                first_iteration = False
