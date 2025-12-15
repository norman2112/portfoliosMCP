"""Activity log creation helpers."""

from okrs_api.model_helpers.common import dictify_model
from okrs_api.model_helpers.event_handlers import deduce_module_name, handler_cls
from okrs_api.hasura.events.event_parser import EventParser


def make_event_data(data, table, operation="insert", trigger=None):
    """Make Event Data as if from Hasura."""
    return {
        "event": {
            "op": operation.upper(),
            "data": data,
        },
        "trigger": {"name": trigger or table},
        "table": {"name": table},
    }


class DeletionLogger:
    """Mock a Hasura deletion event to the appropriate delete event Handler."""

    def __init__(self, instance, db_session, user_id, planview_user_id=None):
        """
        Initialize the DeletionLogger.

        :param model instance: a model instance
        :param db_session db_session:
        :param str user_id: the application user id
        """
        self.instance = instance
        self.db_session = db_session
        self.user_id = user_id
        self.planview_user_id = planview_user_id

    def create_log(self):
        """Execute the delete_event using the event handler."""
        # Execute the handler function
        self._deletion_handler().internal_delete_event()

    def _make_event_parser(self):
        table_name = deduce_module_name(self.instance)
        self.instance.app_last_updated_by = self.user_id
        self.instance.last_updated_by = self.planview_user_id
        data = {"new": None, "old": dictify_model(model_instance=self.instance)}
        event_data = make_event_data(data=data, table=table_name, operation="delete")
        return EventParser(event_body=event_data)

    def _deletion_handler(self):
        module_name = deduce_module_name(self.instance)
        activity_log_module = f"{module_name}.activity_log"
        cls = handler_cls(module_name=activity_log_module)
        return cls(
            event_parser=self._make_event_parser(),
            db_session=self.db_session,
        )
