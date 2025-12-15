"""
The dispatcher and dispatching help utilities for all Hasura events.

This dispatcher dispatches the requests and params, via an EventParser,
to the proper operation in the the proper handler class.
"""
# pylint: disable=W0611
# flake8: noqa: F401

import importlib

from okrs_api.hasura.events.event_parser import EventParser

# The sequence of handlers to engage when the event occurs.
HANDLER_MODULES_BY_TRIGGER = {
    "key_results": ["progress_percentage", "activity_log", "pubnub"],
    "key_result_work_item_mappings": ["activity_log", "orphans", "pubnub"],
    "objectives": ["activity_log", "roll_up_progress", "pubnub"],
    "progress_points": ["activity_log", "pubnub"],
    "settings": ["pubnub", "activity_log"],
    "work_items": ["pubnub"],
    "work_item_containers": ["level_config", "pubnub"],
    "custom_attributes_configs": ["pubnub"],
    "custom_attributes_values": ["activity_log", "pubnub"],
    "targets": ["activity_log", "pubnub"],
    "user_settings": ["activity_log"],
}

BASE_HANDLERS_IMPORT_PATH = "okrs_api.hasura.events.handlers"


class Dispatcher:
    """
    Dispatch Hasura events to the proper operation.

    The Dispatcher will:
    - import the proper module(s) containing the handler(s)
    - instantiate the proper `Handler` class(es)
    - call the `handle_event` function on the `Handler`.
    """

    def __init__(self, request, body, db_session):
        """
        Take in values supplied by AIOHTTP.

        :param dict request: request object from AIOHTTP
        :param dict body: body object from AIOHTTP
        :param SQASession db_session: database session from SQAlchemy
        """
        self.request = request
        self.body = body
        self.db_session = db_session
        self.dispatch_ok = False
        self.errors = []

    def handler(self, module_name, previous_event_parser=None):
        """
        Get handler instance that will handle the event request from Hasura.

        This is always a class called `Handler`.
        :param str module_name: the module name of the Handler class
        :param EventParser previous_event_parser: the event parser from the
        previously called handler.
        """
        cls = handler_cls(module_name=module_name)
        return cls(
            event_parser=previous_event_parser or self.event_parser,
            db_session=self.db_session,
            client_session=self.request.app["client_session"],
            app_settings=self.request.config_dict["settings"],
        )

    async def dispatch(self):
        """
        Call `handle_event` for each relevant Handler.

        Store the success boolean in the `dispatch_ok` attribute.
        Also passes along the event parser from one handler to the next.
        We pass the event parser to the next handler so that the next handler
        can be aware of any changes to the data that have occurred.
        Return True or False. Set errors if False.
        """
        trigger = self.event_parser.trigger_name()
        base_module_names = HANDLER_MODULES_BY_TRIGGER[trigger]
        previous_event_parser = None
        for module_name in base_module_names:
            handler = self.handler(
                module_name=f"{trigger}.{module_name}",
                previous_event_parser=previous_event_parser,
            )
            self.dispatch_ok = await handler.handle_event()
            previous_event_parser = handler.event_parser
            if not self.dispatch_ok:
                break

        return self.dispatch_ok

    @property
    def event_parser(self):
        """Return the event parser."""
        return EventParser(self.body)


def handler_cls(module_name):
    """Return the handler class or an error."""
    full_module_path = f"{BASE_HANDLERS_IMPORT_PATH}.{module_name}"
    module = importlib.import_module(full_module_path)
    # From the imported module specified by the trigger, return the
    # `Handler` class in that module.
    return getattr(module, "Handler")
