"""Handler for Objectives Activity Log changes."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base
from okrs_api.hasura.events.mixins.activity_log import ActivityLog


class Handler(Base, ActivityLog):
    """
    Handles KeyResultWorKItemMapping events.

    Handles the following operations:
    - Insertions
    - Deletions
    """

    def __init__(self, *args, **kwargs):
        """Initialize via the base class."""
        super().__init__(*args, **kwargs)
        # for memoization
        self._objective = None
        self._key_result = None
        self._work_item = None

    def insert_event(self):
        """Handle the insertion event."""
        return self._record_to_activity_log()

    def internal_delete_event(self):
        """Handle an internal delete event."""
        return self._record_to_activity_log()

    def objective(self):
        """Return the Objective, found through the Key Result."""
        if not self._objective:
            self._objective = self.key_result().objective

        return self._objective

    def key_result(self):
        """Return the KeyResult, found through the event data."""
        if not self._key_result:
            key_result_id = self.event_parser.find_value_for_key("key_result_id")
            self._key_result = self.db_session.query(models.KeyResult).get(
                key_result_id
            )

        return self._key_result

    def work_item(self):
        """Return the WorkItem, found through the event data."""
        if not self._work_item:
            work_item_id = self.event_parser.find_value_for_key("work_item_id")
            self._work_item = self.db_session.query(models.WorkItem).get(work_item_id)

        return self._work_item

    def _ok_to_log(self):
        """Return a boolean if it is ok to Log."""
        for check in [self.key_result, self.work_item, self.objective]:
            if not check():
                return False

        return True

    def _record_to_activity_log(self):
        """Instantiate and save a new activity log."""
        if not self._ok_to_log():
            return True

        base_attribs = self.event_parser.subset_data(
            ["key_result_id", "work_item_id"]
        ) | {"objective_id": self.key_result().objective_id}

        log = self.activity_log_factory(
            base_attribs=base_attribs,
            merge_info={
                "key_result_name": self.key_result().name,
                "work_item_name": self.work_item().title,
            },
        )
        self.db_session.add(log)
        return self._commit_db_session()
