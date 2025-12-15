"""Test the ProgressPoint operations for insertion, update, and delete."""

from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from open_alchemy import models
import pytest

from okrs_api.hasura.events.handlers.progress_points.activity_log import (
    Handler as ActivityLogHandler,
)
from okrs_api.hasura.events.handlers.progress_points.progress_percentage import (
    Handler as ProgressHandler,
)
from okrs_api.hasura.events.handlers.progress_points.pubnub import (
    Handler as PubnubHandler,
)
from tests.hasura.events.payloads import EventDataFactory
from tests.hasura.events.payloads import event_payload


@pytest.fixture
def progress_point_payload():
    """Return a function for generating event data for progress_points."""

    def _progress_point_payload(operation="insert", progress_point=None):
        factory = EventDataFactory(
            table="progress_points",
            operation=operation,
            model_instance=progress_point,
        )
        return factory.event()

    return _progress_point_payload


class TestProgressPointActivityLog:
    """Tests for the activity log for an progress_point."""

    @pytest.mark.usefixtures("init_models")
    def test_update(self, mocker, event_handler_factory, progress_point_payload):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=progress_point_payload(operation="update"),
        )
        objective = models.Objective(name="Test Objective")
        key_result = models.KeyResult(name="Test Key Result", objective=objective)
        mocker.patch.object(handler, "key_result", return_value=key_result)
        handler.update_event()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == "update.progress_points"
        assert info["new"]["progress_point_value"] == 40
        assert info["old"]["objective_name"] == "Test Objective"
        assert info["old"]["key_result_name"] == "Test Key Result"

    @pytest.mark.parametrize(
        "operation, action",
        [
            pytest.param("insert", "insert.progress_points", id="insert-event"),
            pytest.param(
                "internal_delete", "delete.progress_points", id="internal-delete-event"
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_insert_and_delete(
        self, mocker, event_handler_factory, progress_point_payload, operation, action
    ):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=progress_point_payload(operation=operation),
        )
        objective = models.Objective(name="Test Objective")
        key_result = models.KeyResult(name="Test Key Result", objective=objective)
        mocker.patch.object(handler, "key_result", return_value=key_result)
        getattr(handler, f"{operation}_event")()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == action
        assert info["progress_point_value"] == 0
        assert info["key_result_name"] == "Test Key Result"
        assert info["objective_name"] == "Test Objective"

    @pytest.mark.usefixtures("init_models")
    def test_delete_with_no_key_result(
        self, event_handler_factory, progress_point_payload
    ):
        """
        Ensure that no activity log is created.

        If there is no key result, then we can assume that the event is part of
        a cascading delete, and therefore, is not relevant to the activity log.
        """
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=progress_point_payload(operation="delete"),
        )
        result = handler.internal_delete_event()
        log = handler.db_session.query(models.ActivityLog).first()
        assert result
        assert not log


class TestProgressCalculation:
    """Ensure that progress calculation is correct."""

    DEFAULT_TENANT_ID_STR = "LEANKIT~d09-10113280894"

    @pytest.mark.usefixtures("init_models")
    def test_objective_progress_calculation(self, mocker, event_handler_factory):
        """Ensure that the progress calculation is correct."""
        # Begin Setup
        db_session = UnifiedAlchemyMagicMock()
        key_results = [
            models.KeyResult(progress_percentage=0, objective_id=1),
            models.KeyResult(progress_percentage=20, objective_id=1),
        ]
        objective = models.Objective(
            id=1,
            name="Write better tests.",
            key_results=key_results,
            progress_percentage=0,
        )
        db_session.add(objective)
        db_session.add_all(key_results)

        # Begin Test
        handler = event_handler_factory(
            handler_klass=ProgressHandler, input_data={}, db_session=db_session
        )
        mocker.patch.object(handler, "objective", mocker.Mock(return_value=objective))
        actual = handler._calculate_objective_progress()
        expected = 10
        assert actual == expected

    def test_key_results_deleted(self, mocker, event_handler_factory):
        """Ensure that the progress calculation is correct after removing all key results."""
        objective = models.Objective(name="Write better tests.", progress_percentage=20)
        handler = event_handler_factory(handler_klass=ProgressHandler, input_data={})
        mocker.patch.object(handler, "objective", mocker.Mock(return_value=objective))
        actual = handler._calculate_objective_progress()
        expected = 0
        assert actual == expected

    @pytest.mark.integration
    def test_progress_point_insert_event(
        self,
        db_session,
        create_db_basic_setting,
        event_handler_factory,
        progress_point_payload,
    ):
        """
        Create a new objective and key result.
        Update the key result progress percentage.
        Verify objective & key result progress percentage.
        """
        create_db_basic_setting({"tenant_id_str": self.DEFAULT_TENANT_ID_STR})

        # Add a new objective and key result to the database.
        progress_point = models.ProgressPoint(value=20, measured_at="2021-01-01")
        key_result = models.KeyResult(
            name="Increase Coverage to 100%",
            starting_value=10,
            target_value=100,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            progress_points=[progress_point],
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
        )
        objective = models.Objective(
            name="Write better tests",
            level_depth=3,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=models.WorkItemContainer(
                external_id="123",
                external_type="leankit",
                tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            ),
            key_results=[key_result],
        )
        db_session.add(objective)
        db_session.commit()

        handler = event_handler_factory(
            handler_klass=ProgressHandler,
            input_data=progress_point_payload(
                operation="insert",
                progress_point=progress_point,
            ),
            db_session=db_session,
        )
        # Invoke the handler to write the percentages.
        handler.insert_event()

        percentages = (
            objective.progress_percentage,
            progress_point.objective_progress_percentage,
            key_result.progress_percentage,
            progress_point.key_result_progress_percentage,
        )
        assert percentages == (11, 11, 11, 11)
        new_data = handler.event_parser.new_data
        assert new_data["key_result_progress_percentage"] == 11
        assert new_data["objective_progress_percentage"] == 11

    @pytest.mark.usefixtures("init_models")
    def test_progress_point_deletion_with_no_key_result(
        self, event_handler_factory, progress_point_payload
    ):
        """
        Ensure correct calculation when a progress point is deleted.

        This ensures that an exception is not raised if bad data exists in the
        database.
        """

        handler = event_handler_factory(
            handler_klass=ProgressHandler,
            input_data=progress_point_payload(
                operation="delete",
            ),
        )
        assert handler.delete_event()

    @pytest.mark.usefixtures("init_models")
    def test_objective_with_key_results(self, mocker, event_handler_factory):
        """
        Ensure correct calculation of the objective progress percentage.

        This should be an average of all key result progress percentages.
        """
        # Setup Database
        db_session = UnifiedAlchemyMagicMock()
        key_results = [
            models.KeyResult(
                name="Increase Coverage to 100%",
                starting_value=10,
                target_value=100,
                starts_at="2021-01-01",
                ends_at="2022-01-01",
                progress_percentage=20,
                objective_id=1,
            ),
            models.KeyResult(
                name="Make 5 decisions by Tuesday",
                starting_value=1,
                target_value=5,
                starts_at="2021-01-01",
                ends_at="2022-01-01",
                progress_percentage=80,
                objective_id=1,
            ),
        ]
        objective = models.Objective(id=1, name="Do better.", key_results=key_results)
        db_session.add(objective)
        db_session.add_all(key_results)

        # Begin test
        handler = event_handler_factory(
            handler_klass=ProgressHandler, input_data={}, db_session=db_session
        )
        mocker.patch.object(handler, "objective", mocker.Mock(return_value=objective))

        actual = handler._calculate_objective_progress()
        assert actual == 50


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
        self, mocker, event_handler_factory, progress_point_payload, operation, response
    ):
        """Ensure that we send a pubnub event on objective changes."""

        handler = event_handler_factory(
            handler_klass=PubnubHandler,
            input_data=progress_point_payload(operation=operation),
        )

        mocker.patch.object(handler, "_send_pubnub_event", return_value=True)

        result = getattr(handler, f"{operation}_event")()

        assert result == response
