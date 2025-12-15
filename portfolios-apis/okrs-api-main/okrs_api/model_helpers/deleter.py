"""The module with methods and classes for soft deletion."""


class Deleter:
    """
    Responsible for deleting records in the database through the ORM.

    If an item can be soft-deleted, then it is soft-deleted as well as its
    dependent objects, which are specified in the `CASCADE_MAP`.

    If it cannot be soft-deleted, it is actually deleted.

    It is important to note that db_session changes are not committed here,
    and should be committed outside by the caller.
    """

    CASCADE_MAP = {
        "WorkItemContainer": ["objectives"],
        "Objective": ["key_results"],
        "KeyResult": ["progress_points", "key_result_work_item_mappings", "targets"],
        "KeyResultWorkItemMapping": None,
        "ProgressPoint": None,
        "targets": None,
    }

    def __init__(self, db_session, model_instance):
        """
        Initialize the deleter.

        :param db_session db_session: the database session
        :param model_instance model_instance: the model instance
        """
        self.db_session = db_session
        self.model_instance = model_instance

    def delete(self):
        """
        Set the `deleted_at_epoch` attribute to the current time.

        Do this if the the object has a `deleted_at_epoch` attribute. If it does not,
        then delete it for real.
        """

        if not self.can_be_soft_deleted:
            self.db_session.delete(self.model_instance)
            return

        self.model_instance.soft_delete()
        self.db_session.add(self.model_instance)
        self._delete_children()

    @property
    def can_be_soft_deleted(self):
        """Return a boolean if the model instance has a `deleted_at` attr."""
        if hasattr(self.model_instance, "deleted_at_epoch"):
            return True
        if hasattr(self.model_instance, "is_deleted"):
            return True
        return False

    @property
    def _model_class(self):
        return type(self.model_instance).__name__

    @property
    def _cascade_relationships(self):
        return self.CASCADE_MAP.get(self._model_class)

    def _delete_children(self):
        """
        Delete children of the model instance.

        Children of the object are determined by the relationships in the
        `CASCADE_MAP`.
        """
        if not self._cascade_relationships:
            return

        for relationship in self._cascade_relationships:
            children = getattr(self.model_instance, relationship)
            for child in children:
                deleter = Deleter(db_session=self.db_session, model_instance=child)
                deleter.delete()
