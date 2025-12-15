"""Test the Handler for KeyResultWorkItemMappings inserts and deletions."""

import pytest

from open_alchemy import models

from okrs_api.hasura.events.handlers.key_result_work_item_mappings.activity_log import (
    Handler as ActivityLogHandler,
)
from okrs_api.hasura.events.handlers.key_result_work_item_mappings.orphans import (
    Handler as OrphanHandler,
)
from okrs_api.hasura.events.handlers.key_result_work_item_mappings.pubnub import (
    Handler as PubnubHandler,
)
from tests.hasura.events.payloads import EventDataFactory


@pytest.fixture
def mapping_payload():
    """Return a function for generating event data for mappings."""

    def _mapping_payload(operation="insert", mapping=None):
        factory = EventDataFactory(
            table="key_result_work_item_mappings",
            operation=operation,
            model_instance=mapping,
        )
        return factory.event()

    return _mapping_payload


class TestMappingActivityLog:
    """Tests for the activity log for a key_result_work_item_mapping."""

    @pytest.mark.parametrize(
        "operation, action",
        [
            pytest.param(
                "insert", "insert.key_result_work_item_mappings", id="insert-event"
            ),
            pytest.param(
                "internal_delete",
                "delete.key_result_work_item_mappings",
                id="internal-delete-event",
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_insert_and_delete(
        self, mocker, event_handler_factory, mapping_payload, operation, action
    ):
        """Ensure that the activity log produced is correct."""
        objective = models.Objective(name="Test Objective")
        key_result = models.KeyResult(name="Test Key Result", objective=objective)
        work_item = models.WorkItem(title="Test Work Item")
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=mapping_payload(operation=operation),
        )

        mocker.patch.object(handler, "key_result", return_value=key_result)
        mocker.patch.object(handler, "work_item", return_value=work_item)
        getattr(handler, f"{operation}_event")()
        log = handler.db_session.query(models.ActivityLog).first()
        info = log.info

        assert log.action == action
        assert info["key_result_name"] == "Test Key Result"

    @pytest.mark.usefixtures("init_models")
    def test_missing_key_result(self, mocker, event_handler_factory, mapping_payload):
        """Ensure that the activity log produced is correct."""
        handler = event_handler_factory(
            handler_klass=ActivityLogHandler,
            input_data=mapping_payload(operation="insert"),
        )
        result = handler.insert_event()
        log = handler.db_session.query(models.ActivityLog).first()
        assert result
        assert not log


class TestOrphans:
    """Ensure that orphaned WorkItems are deleted."""

    def setup_test(self, db_session, create_db_basic_setting, make_mapping=True):
        """Setup the database for testing."""
        tenant_id_str = "LEANKIT~d09-10113280894"
        create_db_basic_setting({"tenant_id_str": tenant_id_str})
        # first, setup the database.
        wic = models.WorkItemContainer(
            external_title="Test WIC",
            external_id="wic-123",
            external_type="leankit",
            tenant_id_str=tenant_id_str,
        )
        wi = models.WorkItem(
            external_type="leankit",
            external_id="abc123",
            title="Test Work Item Deletion",
            work_item_container=wic,
            tenant_id_str=tenant_id_str,
        )
        if not make_mapping:
            db_session.add(wi)
            db_session.commit()
            return wi

        kr = models.KeyResult(
            name="Test KR",
            starting_value=10,
            target_value=200,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            objective=models.Objective(
                name="Test Objective",
                work_item_container=wic,
                starts_at="2021-01-01",
                ends_at="2022-01-01",
                level_depth=3,
                tenant_id_str=tenant_id_str,
            ),
            tenant_id_str=tenant_id_str,
        )
        mapping = models.KeyResultWorkItemMapping(
            key_result=kr,
            work_item=wi,
            tenant_id_str=tenant_id_str,
        )
        db_session.add(mapping)
        db_session.commit()
        return mapping

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_no_deletion_with_mappings(
        self,
        db_session,
        create_db_basic_setting,
        mapping_payload,
        event_handler_factory,
    ):
        """Ensure that WorkItem orphans are deleted."""
        mapping = self.setup_test(db_session, create_db_basic_setting)
        key_result_id = mapping.key_result_id
        work_item_id = mapping.work_item_id

        handler = event_handler_factory(
            handler_klass=OrphanHandler,
            input_data=mapping_payload(operation="delete", mapping=mapping),
            db_session=db_session,
        )
        # Handle the event as if the mapping was deleted
        # (the mapping hasn't actually been deleted for this test case)
        handler.delete_event()

        # retrieve the key_result and work item
        key_result = db_session.query(models.KeyResult).get(key_result_id)
        work_item = db_session.query(models.WorkItem).get(work_item_id)

        # Neither the key result not work item should have been deleted.
        assert key_result
        assert work_item

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_deletion_with_no_mappings(
        self,
        db_session,
        create_db_basic_setting,
        mapping_payload,
        event_handler_factory,
    ):
        """Ensure that WorkItem orphans are deleted."""
        wi = self.setup_test(db_session, create_db_basic_setting, make_mapping=False)
        work_item_id = wi.id

        deleted_mapping = models.KeyResultWorkItemMapping(
            work_item_id=work_item_id, key_result_id=1
        )
        handler = event_handler_factory(
            handler_klass=OrphanHandler,
            input_data=mapping_payload(operation="delete", mapping=deleted_mapping),
            db_session=db_session,
        )
        handler.delete_event()

        # retrieve the work item
        work_item = db_session.query(models.WorkItem).get(work_item_id)

        # The work Item should not exist
        assert not work_item

    @pytest.mark.usefixtures("init_models")
    def test_noop_when_no_work_item_found(self, event_handler_factory, mapping_payload):
        """
        Ensure that nothing happens when work item is missing.

        No errors should be raised and the delete event should return True.
        """
        handler = event_handler_factory(
            handler_klass=OrphanHandler,
            input_data=mapping_payload(operation="delete"),
        )
        assert handler.delete_event()


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
        self, mocker, event_handler_factory, mapping_payload, operation, response
    ):
        """Ensure that we send a pubnub event on objective changes."""

        handler = event_handler_factory(
            handler_klass=PubnubHandler,
            input_data=mapping_payload(operation=operation),
        )

        mocker.patch.object(handler, "_send_pubnub_event", return_value=True)

        result = getattr(handler, f"{operation}_event")()

        assert result == response
