"""Mixin to add into a handler to help with calculations."""
from open_alchemy import models
from sqlalchemy import nullslast

from okrs_api.utils import minmax


class ProgressMixin:
    """
    Progress Percentage helper mixin for Event handlers.

    This mixin assumes that the Handler inherits from the Base handler.
    It also requires the following in the class being mixed in.
    `key_result`, `objective` functions as well as `_key_result_id` property.
    """

    def objective(self):
        """Implement in mixed in class."""
        raise NotImplementedError

    def key_result(self):
        """Get the Key Result from the event data."""
        return self.db_session.query(models.KeyResult).get(self._key_result_id)

    @property
    def _key_result_id(self):
        """Implement in mixed in class."""
        raise NotImplementedError

    @property
    def _objective_id(self):
        """Implement in mixed in class."""
        raise NotImplementedError

    def _calculate_key_result_progress(self):
        """Calculate the progress percentage for a key result."""
        key_result = self.key_result()
        if not key_result:
            return

        calculator = KeyResultProgressCalculator(
            starting_value=key_result.starting_value,
            target_value=key_result.target_value,
            latest_progress_value=self._latest_progress_point_value,
        )

        return calculator.progress_percentage()

    def _calculate_objective_progress(self):
        """Calculate the progress percentage, given an Objective."""
        key_results = (
            self.db_session.query(models.KeyResult)
            .filter_by(objective_id=self._objective_id, deleted_at_epoch=0)
            .all()
        )

        if len(key_results) == 0:
            # No key results means no progress. (0)
            return 0

        progress_sum = sum(minmax(kr.progress_percentage) for kr in key_results)
        return progress_sum / len(key_results)

    def _find_latest_progress_point(self, key_result_id):
        """
        Return the latest progress point value, given a key result id.

        :param db_session db_session:
        :param Integer key_result_id:
        """
        return (
            self.db_session.query(models.ProgressPoint)
            .filter_by(key_result_id=key_result_id, deleted_at_epoch=0)
            .order_by(
                nullslast(models.ProgressPoint.measured_at.desc()),
                models.ProgressPoint.id.desc(),
            )
            .first()
        )

    def latest_progress_point(self):
        """
        Return the latest progress point.

        Uses the value of `_key_result_id` to determine it.
        """
        return self._find_latest_progress_point(key_result_id=self._key_result_id)

    @property
    def _latest_progress_point_value(self):
        """Return the value from the latest progress point."""

        if not self.latest_progress_point():
            return None

        return self.latest_progress_point().value

    def _update_progress_percentage(self, instance, calculator_func):
        """
        Update the progress percentage on the instance provided.

        :param model instance: an instance of a model
        :param any calculator_func: a function to calculate a progress percentage.

        If the instance exists, and the progress percentage has changed, set the
        instance progress percentage value and add the instance to
        the db_session.
        """

        if not instance:
            return

        calculated_progress = calculator_func()
        if instance.progress_percentage == calculated_progress:
            return

        instance.progress_percentage = calculated_progress
        self.db_session.add(instance)

    def _update_key_result_progress(self):
        """Update the progress for the Key Result."""
        self._update_progress_percentage(
            instance=self.key_result(),
            calculator_func=self._calculate_key_result_progress,
        )

    def _update_objective_progress(self):
        """Update the progress for the Objective."""
        self._update_progress_percentage(
            instance=self.objective(),
            calculator_func=self._calculate_objective_progress,
        )


class KeyResultProgressCalculator:
    """
    Calculate the progress percentage for a KeyResult.

    This is a collaborator for the ProgressMixin.
    """

    def __init__(
        self, starting_value=None, target_value=None, latest_progress_value=None
    ):
        """
        Calculate the progress for a key result.

        :param Integer starting_value: the starting value of the key result
        :param Integer target_value: the target value of the key result
        :param Integer latest_progress_value: the latest progress point value
        """
        self.starting_value = starting_value or 0
        self.target_value = target_value or 0
        self._latest_progress_value = latest_progress_value

    @property
    def progress_is_inverted(self):
        """Check if forward progress is a decreasing value rather than increasing."""
        return self.starting_value > self.target_value

    @property
    def latest_progress_value(self):
        """
        Return the latest progress value.

        If the latest progress point value is `None`, it is assumed that there are
        no progress points. If there are no progress points, then the latest
        progress value is the starting value.
        """
        if self._latest_progress_value is None:
            return self.starting_value

        return self._latest_progress_value

    @property
    def numerator(self):
        """
        Get the numerator for progress.

        Invert the result (make negative), if progress is inverted.
        """
        sign = -1 if self.progress_is_inverted else 1
        return sign * (self.latest_progress_value - self.starting_value)

    @property
    def denominator(self):
        """Get the denominator for our progress calculation."""
        return abs(self.target_value - self.starting_value)

    def progress_percentage(self):
        """Calculate the progress percentage."""
        # It is possible for the denominator to be zero.
        if self.denominator == 0:
            # Progress is complete.
            return 100

        return round(self.numerator / self.denominator * 100)
