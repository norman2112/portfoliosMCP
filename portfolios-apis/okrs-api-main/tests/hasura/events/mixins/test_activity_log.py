"""Tests for the mixin for the activity log related handlers."""

import pytest

from okrs_api.hasura.events.mixins.activity_log import ActivityLog, InfoDataPrepper
from okrs_api.hasura.events.event_parser import EventParser
from tests.hasura.events.payloads import EventDataFactory


def build_event_parser(table="key_results", operation="INSERT"):
    event_body = EventDataFactory(
        table=table,
        operation=operation,
    ).event()
    return EventParser(event_body)


class TestActivityLogMixin:
    """Ensure the ActivityLog Mixin works as expected."""

    class BaseTestClass(ActivityLog):
        """Dummy class for testing only."""

        def __init__(self, event_parser):
            """Initialize with an Event Parser."""
            self.event_parser = event_parser

    @pytest.mark.parametrize(
        "event_parser, expected",
        [
            pytest.param(
                build_event_parser(operation="insert"),
                {
                    "info": {"key_result_name": "Increase Coverage to 100%"},
                    "app_created_by": "1",
                    "app_last_updated_by": None,
                },
                id="insert-key-result",
            ),
            pytest.param(
                build_event_parser(operation="update"),
                {
                    "info": {"new": {"key_result_name": "Increase Coverage to 90%"}},
                    "app_created_by": None,
                    "app_last_updated_by": "2",
                },
                id="update-key-result",
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_activity_log_factory(self, event_parser, expected):
        """Ensure that an ActivityLog is built correctly."""
        log = self.BaseTestClass(event_parser).activity_log_factory()

        assert log.app_created_by == expected["app_created_by"]
        assert log.app_last_updated_by == expected["app_last_updated_by"]
        expected_info = expected["info"].get("new", expected["info"])
        log_info = log.info.get("new", log.info)
        for key in expected_info:
            assert log_info[key] == expected_info[key]


class TestInfoDataPrepper:
    """Ensure the InfoDataPrepper preps data appropriately."""

    TEST_DATA = {
        "id": 1,
        "objective_id": 2,
        "starting_value": 0,
        "value_type": "count",
        "name": "Increase Coverage to 100%",
        "progress_percentage": 0,
        "target_value": 100,
        "achieved_at": None,
        "ends_at": "2030-01-01",
        "description": None,
        "starts_at": "2025-01-01",
    }

    def test_prepped_data(self):
        prepper = InfoDataPrepper(
            data=self.TEST_DATA,
            table_name="key_results",
        )
        prepped_data = prepper.prepped_data()

        prepped_keys = list(prepped_data.keys())
        prepped_keys.sort()
        expected_keys = [
            "app_owned_by",
            "description",
            "ends_at",
            "key_result_name",
            "key_result_progress_percentage",
            "objective_id",
            "starting_value",
            "starts_at",
            "target_value",
        ]

        assert prepped_data["key_result_name"] == "Increase Coverage to 100%"
        assert prepped_data["key_result_progress_percentage"] == 0
        assert prepped_keys == expected_keys
