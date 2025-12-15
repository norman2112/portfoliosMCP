"""KeyResultWorkItemMappings orphan handling."""

from open_alchemy import models

from okrs_api.hasura.events.handlers.base import Base


class Handler(Base):
    """
    Handle KeyResultWorKItemMapping DELETE events.

    Used to delete orphaned WorkItem.
    An orphaned WorkItem is a WorkItem that no longer has any
    KeyResultWorkItemMappings.

    Handles the following operations:
    - Deletions
    """

    def delete_event(self):
        """Handle the delete event."""
        self._find_and_delete_orphaned_work_items()
        return True

    def work_item(self):
        """Return the WorkItem, found through the event data."""
        work_item_id = self.event_parser.find_value_for_key("work_item_id")
        return self.db_session.query(models.WorkItem).get(work_item_id)

    def _find_and_delete_orphaned_work_items(self):
        """Find and delete all orphaned work items."""
        wi = self.work_item()
        if not wi:
            return

        mapping_exists = (
            self.db_session.query(models.KeyResultWorkItemMapping.id)
            .filter_by(work_item_id=wi.id)
            .first()
            is not None
        )
        if not mapping_exists:
            self.db_session.delete(wi)
            self._commit_db_session()
