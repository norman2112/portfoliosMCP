"""Test the Handler for KeyResult updates, inserts, and deletions."""

import pytest

from open_alchemy import models

from okrs_api.hasura.events.handlers.key_results.progress_percentage import (
    Handler as ProgressHandler,
)
from okrs_api.hasura.events.handlers.key_results.activity_log import (
    Handler as ActivityLogHandler,
)
from okrs_api.hasura.events.handlers.key_results.pubnub import (
    Handler as PubnubHandler,
)
from okrs_api.hasura.events.mixins.progress import KeyResultProgressCalculator
from tests.hasura.events.payloads import EventDataFactory
from tests.hasura.events.payloads import event_payload


@pytest.fixture
def key_result_payload():
    """Return a function for generating event data for key results."""

    def _key_result_payload(operation="insert", key_result=None):
        factory = EventDataFactory(
            table="key_results",
            operation=operation,
            model_instance=key_result,
        )
        return factory.event()

    return _key_result_payload


class TestKeyResultActivityLog:
    """Tests for the activity log for the key result."""

    @pytest.mark.usefixtures("init_models")
    def test_update(self, mocker, event_handler_factory, key_result_payload):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=key_result_payload(operation="update"),
        )
        objective = models.Objective(
            name="Test Objective",
            progress_percentage=20,
            app_owned_by=1234,
            description="hello world",
        )
        mocker.patch.object(handler, "_get_objective", return_value=objective)
        handler.update_event()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == "update.key_results"
        assert info["new"]["key_result_name"] == "Increase Coverage to 90%"
        assert info["old"]["objective_name"] == "Test Objective"
        assert info["old"]["objective_progress_percentage"] == 20

    @pytest.mark.parametrize(
        "operation, action",
        [
            pytest.param("insert", "insert.key_results", id="insert-event"),
            pytest.param(
                "internal_delete", "delete.key_results", id="internal-delete-event"
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_insert_and_delete(
        self, mocker, event_handler_factory, key_result_payload, operation, action
    ):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=key_result_payload(operation=operation),
        )
        objective = models.Objective(name="Test Objective", progress_percentage=6)
        mocker.patch.object(handler, "_get_objective", return_value=objective)
        getattr(handler, f"{operation}_event")()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == action
        assert info["key_result_name"] == "Increase Coverage to 100%"
        assert info["objective_name"] == "Test Objective"
        assert info["objective_progress_percentage"] == 6

    @pytest.mark.usefixtures("init_models")
    def test_no_objective_noop(self, event_handler_factory, key_result_payload):
        """Ensure that no log is created if the objective cannot be found."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=key_result_payload(operation="delete"),
        )
        result = handler.internal_delete_event()
        log = handler.db_session.query(models.ActivityLog).first()
        assert result
        assert not log


class TestKeyResultProgressCalculation:
    """Tests for the key results operations."""

    DEFAULT_TENANT_ID_STR = "LEANKIT~d09-10113280894"

    @pytest.mark.integration
    def test_insert_key_result(
        self,
        db_session,
        create_db_basic_setting,
        event_handler_factory,
        key_result_payload,
    ):
        """Ensure that the event parser is written back to."""
        create_db_basic_setting()
        progress_point = models.ProgressPoint(
            value=10, measured_at="2030-01-01", tenant_id_str=self.DEFAULT_TENANT_ID_STR
        )
        objective = models.Objective(
            name="Test Objective",
            level_depth=3,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=models.WorkItemContainer(
                external_id="123",
                external_type="leankit",
                tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            ),
        )
        key_result = models.KeyResult(
            name="Test Key Result",
            starting_value=0,
            target_value=100,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            progress_points=[progress_point],
            objective=objective,
        )
        db_session.add(key_result)
        db_session.commit()
        handler = event_handler_factory(
            handler_klass=ProgressHandler,
            input_data=key_result_payload(operation="insert", key_result=key_result),
            db_session=db_session,
        )
        assert handler.insert_event()
        new_data = handler.event_parser.new_data
        assert new_data["progress_percentage"] == 10

    @pytest.mark.integration
    def test_last_key_result_deletion(
        self,
        db_session,
        setting_factory,
        key_result_factory,
        event_handler_factory,
        key_result_payload,
    ):
        """
        Ensure progress percentage is correct on objective.

        When the last Key Result is deleted, we want to ensure that the
        Objective progress percentage is set to 0.
        """
        setting_factory()
        db_session.commit()
        key_result = key_result_factory(objective__progress_percentage=11)
        db_session.commit()

        objective = key_result.objective

        handler = event_handler_factory(
            handler_klass=ProgressHandler,
            input_data=key_result_payload(
                operation="delete",
                key_result=key_result,
            ),
            db_session=db_session,
        )
        handler.delete_event()

        assert objective.progress_percentage == 0

    def test_objective_no_key_results(self, mocker, event_handler_factory):
        """
        Ensure correct calculation of the objective progress percentage.
        """
        objective = models.Objective(name="Write better tests for no key results.")
        handler = event_handler_factory(handler_klass=ProgressHandler, input_data={})
        mocker.patch.object(handler, "objective", mocker.Mock(return_value=objective))

        actual = handler._calculate_objective_progress()
        assert actual == 0

    @pytest.mark.parametrize(
        "deleted_at_epoch, expected_progress",
        [
            pytest.param(9999999, 91, id="one-key-result"),
            pytest.param(0, 51, id="both-key-results"),
        ],
    )
    @pytest.mark.integration
    def test_key_result_soft_deleted(
        self,
        db_session,
        event_handler_factory,
        setting_factory,
        progress_point_factory,
        deleted_at_epoch,
        expected_progress,
    ):
        """Ensure that if a key result is soft-deleted, progress is correct."""
        # Setup database. Two key results. One is soft-deleted.
        setting_factory()
        pp1 = progress_point_factory(
            key_result__deleted_at_epoch=deleted_at_epoch,
            key_result__progress_percentage=10,
        )
        objective = pp1.key_result.objective
        progress_point_factory(
            key_result__progress_percentage=91,
            key_result__objective=objective,
        )
        kr1 = pp1.key_result
        db_session.commit()

        # begin test
        input_data = event_payload(
            table="key_results", operation="delete", model_instance=kr1
        )
        handler = event_handler_factory(
            handler_klass=ProgressHandler,
            input_data=input_data,
            db_session=db_session,
        )

        handler.delete_event()
        db_session.refresh(objective)
        assert objective.progress_percentage == expected_progress


class TestKeyResultProgressCalculator:
    """Ensure the Progress Calculator for the Key Result works properly."""

    @pytest.mark.parametrize(
        "starting_value, target_value, latest_progress_point_value, expected",
        [
            pytest.param(None, None, 50, 100, id="null-values-supplied"),
            pytest.param(0, 0, 50, 100, id="zero-values-supplied"),
            pytest.param(100, 100, 50, 100, id="same-values-supplied"),
            pytest.param(0, 50, 50, 100, id="progress-matched-final"),
            pytest.param(0, 100, 50, 50, id="progress-half-of-final"),
            pytest.param(100, 0, 50, 50, id="progress-reversed-half-of-final"),
            pytest.param(0, 10, None, 0, id="progress-none"),
        ],
    )
    def test_progress_percentage(
        self, starting_value, target_value, latest_progress_point_value, expected
    ):
        """
        Ensure proper calculation for key result progress.
        """

        calculator = KeyResultProgressCalculator(
            starting_value=starting_value,
            target_value=target_value,
            latest_progress_value=latest_progress_point_value,
        )
        assert calculator.progress_percentage() == expected


class TestProgressPoints:
    """Test progress point DB constraints."""

    DEFAULT_TENANT_ID_STR = "LEANKIT~d09-10113280894"

    @pytest.fixture
    def objectives_and_key_results(self, db_session, create_db_basic_setting):
        create_db_basic_setting()

        self.objective = models.Objective(
            name="Test Objective",
            level_depth=3,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=models.WorkItemContainer(
                external_id="123",
                external_type="leankit",
                tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            ),
        )
        self.key_result = models.KeyResult(
            name="Test Key Result",
            starting_value=0,
            target_value=100,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            objective=self.objective,
        )
        db_session.add(self.objective)
        db_session.add(self.key_result)
        db_session.commit()

    @pytest.mark.integration
    def test_no_duplicate_progress_points(self, db_session, objectives_and_key_results):
        """
        Ensure that for a date there can be only one progress entry.
        """
        progress_point1 = models.ProgressPoint(
            value=10,
            measured_at="2030-01-01",
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            key_result_id=self.key_result.id,
        )
        progress_point2 = models.ProgressPoint(
            value=12,
            measured_at="2030-01-01",
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            key_result_id=self.key_result.id,
        )

        db_session.add(progress_point1)
        db_session.add(progress_point2)
        with pytest.raises(Exception) as exec_info:
            db_session.commit()
        assert "uq_key_result_id_measured_at" in str(exec_info)

    @pytest.mark.integration
    def test_single_non_deleted_entry(self, db_session, objectives_and_key_results):
        """
        Ensure that for a date there can be only one non-deleted progress entry.
        It is possible to enter more than once if all other entries are deleted.
        """
        progress_point1 = models.ProgressPoint(
            value=10,
            measured_at="2030-01-01",
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            key_result_id=self.key_result.id,
        )
        progress_point2 = models.ProgressPoint(
            value=12,
            measured_at="2030-01-01",
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            key_result_id=self.key_result.id,
        )
        progress_point3 = models.ProgressPoint(
            value=14,
            measured_at="2030-01-01",
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            key_result_id=self.key_result.id,
        )

        progress_point1.deleted_at_epoch = 1668750631
        progress_point2.deleted_at_epoch = 1668750651

        db_session.add(progress_point1)
        db_session.add(progress_point2)
        db_session.add(progress_point3)

        db_session.commit()

        assert len(self.key_result.progress_points) == 3


class TestPubnubHandler:
    """Test the pubnub handlers for objectives."""

    @pytest.mark.parametrize(
        "operation, response",
        [
            pytest.param("insert", True),
            pytest.param("update", True),
            pytest.param("delete", True),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_objective_changes(
        self, mocker, event_handler_factory, key_result_payload, operation, response
    ):
        """Ensure that we send a pubnub event on objective changes."""

        handler = event_handler_factory(
            handler_klass=PubnubHandler,
            input_data=key_result_payload(operation=operation),
        )

        mocker.patch.object(handler, "_send_pubnub_event", return_value=True)

        result = getattr(handler, f"{operation}_event")()

        assert result == response
