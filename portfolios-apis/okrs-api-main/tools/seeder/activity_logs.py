"""Seeding collaborators for Activity Logs."""

import importlib

from inflection import underscore, pluralize
from open_alchemy import models

from okrs_api.hasura.events.event_parser import EventParser
from tests.hasura.events.payloads import EventDataFactory

BASE_HANDLERS_IMPORT_PATH = "okrs_api.hasura.events.handlers"


def seed(db_session):
    """
    Seed all activity logs.

    Find the last objective and it's related model instances.
    Then use that data to create hasura event data.
    Pass the Hasura event data to the `activity_log` handlers that are already
    responsible for making the activity logs.
    """
    # Get instances for activity log reporting.
    objective = (
        db_session.query(models.Objective).order_by(models.Objective.id.desc()).first()
    )
    key_result = objective.key_results[0]
    progress_point = key_result.progress_points[-1]
    key_result_work_item_mapping = (
        db_session.query(models.KeyResultWorkItemMapping)
        .filter_by(key_result_id=key_result.id)
        .first()
    )

    instances = [objective, key_result, progress_point, key_result_work_item_mapping]
    for instance in instances:
        module_name = _deduce_module_name(instance)
        cls = _handler_cls(f"{module_name}.activity_log")

        for operation in ["insert", "update", "internal_delete"]:
            event_parser = _make_event_parser(
                table_name=module_name,
                operation=operation,
                instance=instance,
            )
            handler = cls(
                event_parser=event_parser,
                db_session=db_session,
            )

            # Execute the handler function
            handler_func_name = f"{operation}_event"
            if hasattr(handler, handler_func_name):
                getattr(handler, handler_func_name)()


def _handler_cls(module_name):
    """Return the handler class or an error."""
    full_module_path = f"{BASE_HANDLERS_IMPORT_PATH}.{module_name}"
    module = importlib.import_module(full_module_path)
    # From the imported module specified by the trigger, return the
    # `Handler` class in that module.
    return getattr(module, "Handler")


def _deduce_module_name(instance):
    """
    Return the module name for this instance.

    This should be the same as the table name.
    """
    cls_name = type(instance).__name__
    underscore_name = underscore(cls_name)
    return pluralize(underscore_name)


def _make_event_parser(table_name, operation="insert", instance=None):
    """Make the event data and the EventParser."""
    factory = EventDataFactory(
        table=table_name, operation=operation, model_instance=instance
    )
    data = factory.event()
    return EventParser(event_body=data)
