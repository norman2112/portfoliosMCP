"""Test the Handler for Objective updates, inserts, and deletions."""

import pytest

from open_alchemy import models

import okrs_api.pubnub.utils

from okrs_api.hasura.events.handlers.objectives.activity_log import (
    Handler as ActivityLogHandler,
)

from okrs_api.hasura.events.handlers.objectives.pubnub import Handler as PubnubHandler

from tests.hasura.events.payloads import EventDataFactory


@pytest.fixture
def objective_payload():
    """Return a function for generating event data for objectives."""

    def _objective_payload(operation="insert", objective=None):
        factory = EventDataFactory(
            table="objectives",
            operation=operation,
            model_instance=objective,
        )
        return factory.event()

    return _objective_payload


class TestObjectiveActivityLog:
    """Tests for the activity log for an objective."""

    @pytest.mark.usefixtures("init_models")
    def test_update(self, event_handler_factory, objective_payload):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=objective_payload(operation="update"),
        )
        handler.update_event()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == "update.objectives"
        assert info["new"]["objective_name"] == "Stand down"

    @pytest.mark.parametrize(
        "operation, action",
        [
            pytest.param("insert", "insert.objectives", id="insert-event"),
            pytest.param(
                "internal_delete", "delete.objectives", id="internal-delete-event"
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_insert_and_delete(
        self, event_handler_factory, objective_payload, operation, action
    ):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=objective_payload(operation=operation),
        )
        getattr(handler, f"{operation}_event")()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == action
        assert info["objective_name"] == "Refactor everything"


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
        self, mocker, event_handler_factory, objective_payload, operation, response
    ):
        """Ensure that we send a pubnub event on objective changes."""

        handler = event_handler_factory(
            handler_klass=PubnubHandler,
            input_data=objective_payload(operation=operation),
        )

        mocker.patch.object(handler, "_send_pubnub_event", return_value=True)

        result = getattr(handler, f"{operation}_event")()

        assert result == response
