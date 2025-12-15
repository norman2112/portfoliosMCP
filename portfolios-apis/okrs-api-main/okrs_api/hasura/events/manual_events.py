"""Module for triggering events manually."""

from okrs_api.model_helpers.common import dictify_model
from okrs_api.model_helpers.event_handlers import deduce_module_name
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


# pylint:disable=too-many-arguments
class EventHandlerFactory:
    """
    Return an instance of an EventHandler with data populated.

    This takes in an Event Handler Class and populates it and returns it.
    At which point, the caller may call any method they like on the handler.
    This is intended to be used as a way of manually triggering events as if
    they came from Hasura.
    """

    def __init__(
        self,
        handler_cls,
        model_instance,
        db_session,
        app_settings=None,
        client_session=None,
    ):
        """
        Initialize the EventHandlerFactory.

        :param EventHandlerClass handler_cls:
        :param Model model_instance:
        :param db_session db_session:
        :param dict app_settings:
        :param session client_session:
        """
        self.handler_cls = handler_cls
        self.model_instance = model_instance
        self.db_session = db_session
        self.app_settings = app_settings or {}
        self.client_session = client_session

    def handler(self):
        """Return an instance of an Event Handler."""
        return self.handler_cls(
            event_parser=self._make_event_parser(),
            db_session=self.db_session,
            client_session=self.client_session,
            app_settings=self.app_settings,
        )

    def _make_event_parser(self):
        table_name = deduce_module_name(self.model_instance)
        data = {"new": dictify_model(model_instance=self.model_instance), "old": None}
        event_data = make_event_data(data=data, table=table_name, operation="insert")
        return EventParser(event_body=event_data)
