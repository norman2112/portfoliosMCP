"""Manager class for progress point custom actions."""
from datetime import datetime
from http import HTTPStatus

from open_alchemy import models
from sqlalchemy import nullslast

from okrs_api.model_helpers.activity_logger import DeletionLogger
from okrs_api.model_helpers.common import commit_db_session, set_last_updated_by_fields
from okrs_api.model_helpers.deleter import Deleter
from okrs_api.model_helpers.key_results import (
    get_by_id_and_tenant as get_kr_by_id_and_tenant,
)
from okrs_api.model_helpers.progress_points import (
    create_new_progress_point,
    get_by_id_and_tenant as get_pp_by_id_and_tenant,
    get_latest_progress_point_by_krid,
)
from okrs_api.model_helpers.targets import get_targets_by_krid, get_mapped_target
from okrs_api.utils import minmax, adapt_error_for_hasura


class ProgressPointsManager:
    """Class to handle the progres point custom actions."""

    def __init__(self, input_prepper=None):
        """Initialize the ProgressPointsManager with input_prepper."""
        self.input_prepper = input_prepper

    def create_progress_points(self):
        """Insert Progress Point and re-calculates progress percentages."""
        input_data = self.input_prepper.input_parser
        with self.input_prepper.db_session() as db_session:
            key_result_id = input_data["key_result_id"]
            measured_at_str = input_data["measured_at"]
            value = input_data["value"]
            comment = input_data.get("comment", "")
            try:
                measured_at = datetime.strptime(measured_at_str, "%Y-%m-%d").date()
            except ValueError as e:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message=f"Invalid date format : {e}",
                            error_code="INVALID_DATE_FORMAT",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )

            key_result = get_kr_by_id_and_tenant(
                db_session,
                key_result_id,
                self.input_prepper.tenant_group_id,
                self.input_prepper.org_id,
            )
            if not key_result:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Key result not found",
                            error_code="KEY_RESULT_NOT_FOUND",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )

            objective = key_result.objective
            targets = get_targets_by_krid(db_session, key_result_id)
            target_id = get_mapped_target(targets, measured_at)
            existing_progress_point = (
                db_session.query(
                    models.ProgressPoint.id,
                )
                .filter_by(
                    key_result_id=key_result_id,
                    measured_at=measured_at,
                    deleted_at_epoch=0,
                )
                .first()
            )
            if existing_progress_point:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Progress entry already exists with this date",
                            error_code="PROGRESS_POINT_DATE_EXIST",
                            progress_point={
                                "id": existing_progress_point[0],
                                "value": value,
                                "comment": comment,
                            },
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )

            latest_progress_point = get_latest_progress_point_by_krid(
                db_session, key_result_id
            )
            is_latest_updated = False
            if (
                not latest_progress_point
                or latest_progress_point.measured_at < measured_at
            ):
                is_latest_updated = True
            new_progress_point_data = {
                "key_result_id": key_result_id,
                "measured_at": measured_at,
                "value": value,
                "comment": comment,
                "target_id": target_id,
            }
            new_progress_point = create_new_progress_point(
                self.input_prepper, new_progress_point_data
            )
            if is_latest_updated:
                calculator = KeyResultProgressCalculator(
                    starting_value=key_result.starting_value,
                    target_value=key_result.target_value,
                    latest_progress_value=value,
                )

                kr_progress_percentage = calculator.progress_percentage()
                key_result.progress_percentage = kr_progress_percentage
                set_last_updated_by_fields(key_result, self.input_prepper)
                new_progress_point.key_result_progress_percentage = (
                    kr_progress_percentage
                )

                objective_calculator = ObjectiveProgressCalculator(
                    objective_id=objective.id, db_session=db_session
                )
                obj_progress_percentage = objective_calculator.progress_percentage()
                objective.progress_percentage = obj_progress_percentage
                set_last_updated_by_fields(objective, self.input_prepper)
                db_session.add(key_result)
                new_progress_point.objective_progress_percentage = (
                    obj_progress_percentage
                )
            db_session.add(new_progress_point)
            commit_db_session(db_session)
            return {"id": new_progress_point.id}, HTTPStatus.OK

    def update_progress_percentage(self):
        """Update Progress Point and re-calculates progress percentages."""
        input_data = self.input_prepper.input_parser
        with self.input_prepper.db_session() as db_session:
            progress_point_id = input_data["id"]
            value = input_data["value"]
            comment = input_data.get("comment", "")

            progress_point = get_pp_by_id_and_tenant(
                db_session,
                progress_point_id,
                self.input_prepper.tenant_group_id,
                self.input_prepper.org_id,
            )
            if not progress_point:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Progress point not found",
                            error_code="PROGRESS_POINT_NOT_FOUND",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
            key_result = progress_point.key_result
            objective = key_result.objective

            latest_progress_point = get_latest_progress_point_by_krid(
                db_session, key_result.id
            )

            is_latest_updated = False
            if latest_progress_point.id == progress_point_id:
                is_latest_updated = True

            if is_latest_updated:
                key_result_calculator = KeyResultProgressCalculator(
                    starting_value=key_result.starting_value,
                    target_value=key_result.target_value,
                    latest_progress_value=value,
                )
                kr_progress_percentage = key_result_calculator.progress_percentage()
                key_result.progress_percentage = kr_progress_percentage
                set_last_updated_by_fields(key_result, self.input_prepper)

                objective_calculator = ObjectiveProgressCalculator(
                    objective_id=objective.id, db_session=db_session
                )
                obj_progress_percentage = objective_calculator.progress_percentage()
                objective.progress_percentage = obj_progress_percentage
                set_last_updated_by_fields(objective, self.input_prepper)

                progress_point.objective_progress_percentage = obj_progress_percentage
                progress_point.key_result_progress_percentage = kr_progress_percentage

            progress_point.value = value
            progress_point.comment = comment
            set_last_updated_by_fields(progress_point, self.input_prepper)
            db_session.add(progress_point)
            commit_db_session(db_session)
            return {"id": progress_point.id}, HTTPStatus.OK

    def delete_progress_percentage(self):
        """Delete Progress Point and re-calculates progress percentages."""
        input_data = self.input_prepper.input_parser
        with self.input_prepper.db_session() as db_session:
            progress_point_id = input_data["id"]

            progress_point = get_pp_by_id_and_tenant(
                db_session,
                progress_point_id,
                self.input_prepper.tenant_group_id,
                self.input_prepper.org_id,
            )
            if not progress_point:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Progress point not found",
                            error_code="PROGRESS_POINT_NOT_FOUND",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
            key_result = progress_point.key_result
            objective = key_result.objective

            latest_progress_point = (
                db_session.query(models.ProgressPoint)
                .filter(models.ProgressPoint.id != progress_point_id)
                .filter_by(key_result_id=key_result.id, deleted_at_epoch=0)
                .order_by(
                    nullslast(models.ProgressPoint.measured_at.desc()),
                    models.ProgressPoint.id.desc(),
                )
                .first()
            )
            is_latest_updated = False
            if (
                not latest_progress_point
                or latest_progress_point.measured_at < progress_point.measured_at
            ):
                is_latest_updated = True

            if is_latest_updated:
                latest_progress_value = (
                    key_result.starting_value
                    if not latest_progress_point
                    else latest_progress_point.value
                )
                kr_calculator = KeyResultProgressCalculator(
                    starting_value=key_result.starting_value,
                    target_value=key_result.target_value,
                    latest_progress_value=latest_progress_value,
                )

                kr_progress_percentage = kr_calculator.progress_percentage()
                key_result.progress_percentage = kr_progress_percentage
                set_last_updated_by_fields(key_result, self.input_prepper)

                objective_calculator = ObjectiveProgressCalculator(
                    objective_id=objective.id, db_session=db_session
                )
                obj_progress_percentage = objective_calculator.progress_percentage()
                objective.progress_percentage = obj_progress_percentage
                set_last_updated_by_fields(objective, self.input_prepper)
                if latest_progress_point:
                    latest_progress_point.key_result_progress_percentage = (
                        kr_progress_percentage
                    )
                    latest_progress_point.objective_progress_percentage = (
                        obj_progress_percentage
                    )
                    set_last_updated_by_fields(
                        latest_progress_point, self.input_prepper
                    )
                    db_session.add(latest_progress_point)
            set_last_updated_by_fields(progress_point, self.input_prepper)
            deleter = Deleter(db_session=db_session, model_instance=progress_point)
            deleter.delete()

            delete_logger = DeletionLogger(
                instance=progress_point,
                db_session=db_session,
                user_id=self.input_prepper.user_id,
                planview_user_id=self.input_prepper.planview_user_id,
            )
            delete_logger.create_log()

            commit_db_session(db_session)
            return {"id": progress_point.id}, HTTPStatus.OK


class ObjectiveProgressCalculator:
    """Calculate the progress percentage for an Objective."""

    def __init__(self, objective_id, db_session):
        """Initialize ObjectiveProgressCalculator with an objective_id and db_session."""
        self.objective_id = objective_id
        self.db_session = db_session

    def fetch_objective_key_results(self):
        """Fetch all the active key results for the given objective_id."""
        objective_key_results = (
            self.db_session.query(
                models.KeyResult.id, models.KeyResult.progress_percentage
            )
            .filter_by(objective_id=self.objective_id, deleted_at_epoch=0)
            .all()
        )
        return objective_key_results

    def progress_percentage(self):
        """Calculate the objective progress percentage."""
        obj_progress_percentage = 0
        objective_key_results = self.fetch_objective_key_results()
        if objective_key_results:
            progress_sum = sum(
                minmax(kr.progress_percentage) for kr in objective_key_results
            )
            obj_progress_percentage = round(progress_sum / len(objective_key_results))
        return obj_progress_percentage


class KeyResultProgressCalculator:
    """Calculate the progress percentage for a KeyResult."""

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
