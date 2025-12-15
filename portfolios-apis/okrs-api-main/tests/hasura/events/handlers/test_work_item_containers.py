"""Test the Handler for WorkItemContainer updates, inserts, and deletions."""

from open_alchemy import models
import pytest

from okrs_api.hasura.events.handlers.work_item_containers.level_config import Handler
from okrs_api.hasura.events.handlers.work_item_containers.pubnub import (
    Handler as PubnubHandler,
)
from tests.hasura.events.payloads import event_payload


class TestWorkItemContainersHandler:
    """Ensure that operations for the WorkItemContainers handler work as expected."""

    DEFAULT_TENANT_ID_STR = "LEANKIT~d08-10100000101"
    DEFAULT_TENANT_GROUP_ID_STR = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_new_settings(self, db_session, event_handler_factory):
        """Ensure that a new settings record is created."""
        handler = event_handler_factory(
            handler_klass=Handler,
            input_data=event_payload("work_item_containers", "insert"),
            db_session=db_session,
        )
        result = handler.insert_event()

        setting = (
            db_session.query(models.Setting)
            .filter_by(tenant_id_str=self.DEFAULT_TENANT_ID_STR)
            .first()
        )
        config_count = (
            db_session.query(models.Setting)
            .filter_by(tenant_id_str=self.DEFAULT_TENANT_ID_STR)
            .count()
        )
        assert result
        assert setting and setting.level_config
        assert config_count == 1

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_only_one_level_config(
        self, db_session, create_db_basic_setting, event_handler_factory
    ):
        """Ensure that a new level config is created."""
        # Create an existing level config for the tenant_id_str.
        create_db_basic_setting({"tenant_id_str": self.DEFAULT_TENANT_ID_STR})
        handler = event_handler_factory(
            handler_klass=Handler,
            input_data=event_payload("work_item_containers", "insert"),
            db_session=db_session,
        )
        result = handler.insert_event()

        config_count = (
            db_session.query(models.Setting)
            .filter_by(tenant_id_str=self.DEFAULT_TENANT_ID_STR)
            .count()
        )
        assert result
        assert config_count == 1

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_only_one_level_config_with_group_id(
        self, db_session, create_db_basic_setting, event_handler_factory
    ):
        """Ensure that no new level config is created."""
        # Create an existing level config for the tenant_id_str.
        create_db_basic_setting(
            {
                "tenant_group_id_str": self.DEFAULT_TENANT_GROUP_ID_STR,
                "tenant_id_str": "somethingelse",
            }
        )
        handler = event_handler_factory(
            handler_klass=Handler,
            input_data=event_payload("work_item_containers", "insert"),
            db_session=db_session,
        )
        result = handler.insert_event()

        config_count = (
            db_session.query(models.Setting)
            .filter_by(tenant_group_id_str=self.DEFAULT_TENANT_GROUP_ID_STR)
            .count()
        )
        assert result
        assert config_count == 1

        config_count_new = (
            db_session.query(models.Setting)
            .filter_by(tenant_id_str=self.DEFAULT_TENANT_ID_STR)
            .count()
        )
        assert config_count_new == 0


class TestPubnubHandler:
    """Test the pubnub handlers for objectives."""

    @pytest.mark.parametrize(
        "operation, response",
        [pytest.param("insert", True), pytest.param("update", True)],
    )
    @pytest.mark.usefixtures("init_models")
    def test_objective_changes(
        self, mocker, event_handler_factory, operation, response
    ):
        """Ensure that we send a pubnub event on objective changes."""

        handler = event_handler_factory(
            handler_klass=PubnubHandler,
            input_data=event_payload("work_item_containers", operation),
        )

        mocker.patch.object(handler, "_send_pubnub_event", return_value=True)

        result = getattr(handler, f"{operation}_event")()

        assert result == response
