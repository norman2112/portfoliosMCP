"""Helpers for constructing Event payloads from Hasura. """
from okrs_api.model_helpers.common import dictify_model


class EventDataFactory:
    """
    Makes event data for INSERT and DELETE operations for a model instance.
    """

    DEFAULT_ATTRIBS = {
        "objectives": {
            "id": 1,
            "app_owned_by": None,
            "work_item_container_id": 1,
            "level_depth": 0,
            "name": "Refactor everything",
            "app_created_by": None,
            "app_last_updated_by": None,
            "progress_percentage": 0,
            "achieved_at": None,
            "ends_at": None,
            "parent_objective_id": 2,
            "description": "Everything must go!",
            "starts_at": "2025-01-01",
            "deleted_at_epoch": 0,
        },
        "key_results": {
            "id": 1,
            "objective_id": 1,
            "starting_value": 0,
            "value_type": "count",
            "name": "Increase Coverage to 100%",
            "progress_percentage": 0,
            "target_value": 100,
            "achieved_at": None,
            "ends_at": None,
            "description": None,
            "starts_at": None,
            "deleted_at_epoch": 0,
        },
        "key_result_work_item_mappings": {
            "key_result_id": 1,
            "work_item_id": 1,
        },
        "progress_points": {
            "key_result_id": 1,
            "key_result_progress_percentage": 0,
            "objective_progress_percentage": 0,
            "value": 0,
            "measured_at": "2021-01-01",
            "id": 1,
            "deleted_at_epoch": 0,
        },
        "settings": {
            "id": 1,
            "tenant_id_str": "LEANKIT~d09-123456789",
        },
        "work_items": {
            "id": 1,
            "title": "Test - Zoo Field Trip",
            "planned_start": "2021-10-10",
            "planned_finish": "2021-11-11",
            "external_type": "leankit",
            "external_id": "10101",
            "state": "in_progress",
            "work_item_container_id": 1,
            "tenant_id_str": "LEANKIT~d08-10100000101",
        },
        "work_item_containers": {
            "id": 1,
            "external_title": "Development Board",
            "external_id": "12345",
            "external_type": "leankit",
            "level_depth_default": 2,
            "tenant_id_str": "LEANKIT~d08-10100000101",
            "deleted_at_epoch": 0,
            "tenant_group_id_str": "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p",
        },
    }

    UPDATE_ATTRIBS = {
        "objectives": {
            "level_depth": 2,
            "name": "Stand down",
            "progress_percentage": 10,
            "ends_at": "2026-01-01",
            "description": "UPDATE - Everything must go!",
        },
        "key_results": {
            "starting_value": 10,
            "name": "Increase Coverage to 90%",
            "progress_percentage": 13,
            "target_value": 90,
        },
        "progress_points": {
            "value": 40,
            "measured_at": "2025-01-01",
        },
        "settings": {
            "level_config": '[{ "depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": true }]'
        },
        "work_items": {
            "title": "Test - Pizza Party",
            "planned_finish": "2021-11-11",
            "state": "finished",
        },
        "work_item_containers": {
            "level_depth_default": 4,
        },
    }

    COMMON_ATTRIBS = {
        "tenant_id_str": "LEANKIT~d08-10100000101",
        "app_created_by": "1",
        "app_last_updated_by": "2",
    }

    OPERATION_ALIASES = {"internal_delete": "delete"}

    def __init__(self, table, operation="insert", model_instance=None):
        """
        Initialize values.

        :param str table: the name of the hasura table
        :param str operation: `insert`, `update`, or `delete`
        :param model model_instance: an instance of a model

        If no model instance is given, then blank default attributes
        will be returned in the even data.
        """
        self.table = table
        self._operation = operation
        self.model_instance = model_instance

    def event(self):
        """Return the event body."""
        trigger = f"{self.table}"
        data = getattr(self, f"_data_for_{self.operation}")()
        return {
            "event": {
                "op": self.operation.upper(),
                "data": data,
            },
            "trigger": {"name": trigger},
            "table": {"name": self.table},
        }

    @property
    def operation(self):
        """Return an un-aliased, lowercase version of the operation."""
        op = self._operation.lower()
        return self.OPERATION_ALIASES.get(op, op)

    def _data_attribs(self):
        """
        Return the data attribs for the test.

        Use the attribs from the model, if available. Otherwise, use the
        default data attribs.
        """
        if self.model_instance:
            return dictify_model(self.model_instance)

        return self.COMMON_ATTRIBS | self.DEFAULT_ATTRIBS.get(self.table, {})

    def _update_data_attribs(self):
        """Return data for the 'new' key in UPDATE data."""
        updates = self.UPDATE_ATTRIBS.get(self.table) or {}
        return self._data_attribs() | updates

    def _data_for_insert(self):
        """Return the event data for an INSERT operation."""
        return {
            "new": self._data_attribs(),
            "old": None,
        }

    def _data_for_update(self):
        """Return the event data for an UPDATE operation."""
        return {
            "new": self._update_data_attribs(),
            "old": self._data_attribs(),
        }

    def _data_for_delete(self):
        """Return the event data for a DELETE operation."""
        return {
            "new": None,
            "old": self._data_attribs(),
        }


def event_payload(table, operation="insert", model_instance=None):
    """Return an event payload."""
    return EventDataFactory(table, operation, model_instance).event()


def bogus_trigger_event(new_attribs=None, old_attribs=None):
    """
    Return a Hasura payload with invalid trigger. This is used for testing events.py
    """
    if not any([new_attribs, old_attribs]):
        new_attribs = {}

    return {
        "event": {
            "op": "INSERT",
            "data": {
                "old": old_attribs,
                "new": new_attribs,
            },
        },
        "trigger": {"name": "bogus_trigger"},
        "table": {"name": "progress_points"},
    }
