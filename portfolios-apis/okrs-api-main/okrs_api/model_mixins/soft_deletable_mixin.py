"""Mixin for soft-deletable models."""
from time import time_ns


# pylint:disable=W0201
class Deletable:
    """Helper methods for soft deletable models."""

    def is_deleted(self):
        """Mark this instance as soft-deleted."""
        return

    def soft_delete(self):
        """Mark this instance as soft-deleted."""
        return


class SoftDeletable(Deletable):
    """Helper methods for soft deletable models."""

    def is_deleted(self):
        """Return a boolen if this has been [soft] deleted."""
        return self.deleted_at_epoch > 0

    def soft_delete(self):
        """Mark this instance as soft-deleted by setting deleted_at_epoch time."""
        self.deleted_at_epoch = time_ns()


class SoftDeletableBoolean(Deletable):
    """Helper methods for soft deletable models with is_deleted column."""

    def is_deleted(self):
        """Return a boolen if this has been [soft] deleted."""
        return self.is_deleted is True

    def soft_delete(self):
        """Mark this instance as soft-deleted by setting is_deleted to True."""
        self.is_deleted = True
