# pylint:disable=too-few-public-methods
"""The Base for all Event Handlers."""

import inspect


class Base:
    """
    The base class for all event handlers.

    `UPDATE_KEYS` is set in this class and should be overwritten in child
    classes where there is an `update_event` function.
    """

    UPDATE_KEYS = []

    def __init__(
        self, event_parser, db_session, client_session=None, app_settings=None
    ):
        """
        Initialize the class.

        :param EventParser event_parser: the parser for Event data
        :param Session db_session: an SqlAlchemy database session
        """
        self.event_parser = event_parser
        self.db_session = db_session
        self.client_session = client_session
        self.app_settings = app_settings
        self.errors = []

    async def handle_event(self):
        """
        Handle the event.

        This will choose the operation function to call, based on the
        operation in the event data. Operation functions are either
        `insert_event`, `update_event`, or `delete_event`.

        This will return the value from the chosen operation function.
        """
        op_func = self._get_operation_function()
        if not op_func:
            return True

        if inspect.iscoroutinefunction(op_func):
            return await op_func()

        return op_func()

    def _get_operation_function(self):
        """
        Return the operation function, if applicable.

        In the event of an UPDATE operation, will check that the Handler has
        an `UPDATE_KEYS` attribute. If it does, will check against that list of
        keys to determine if the function is applicable.
        """
        operation = self.event_parser.operation
        op_func = getattr(self, f"{operation}_event", None)
        if not op_func:
            return None

        if self.event_parser.event_is_update:
            if not self.UPDATE_KEYS:
                raise LookupError("UPDATE_KEYS must be set for an update operation.")

            if not self.event_parser.in_changed_keys(self.UPDATE_KEYS):
                return None

        return op_func

    def _commit_db_session(self):
        try:
            self.db_session.commit()
            return True
        except Exception as e:
            self.db_session.rollback()
            raise e
