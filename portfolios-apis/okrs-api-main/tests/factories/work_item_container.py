"""KeyResult factory."""

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory

# NOTE: due to triggers, a setting must be set before this can be
# created without error in the database.
class WorkItemContainerFactory(BaseFactory):
    class Meta:
        model = models.WorkItemContainer
        exclude = ("level_depth_default", "objective_editing_levels")

    external_id = factory.Sequence(lambda n: f"test-{n}")
    external_type = "leankit"
    app_name = "leankit"
    container_type = "lk_board"
    external_title = factory.Sequence(lambda n: f"Test Board {n}")
    app_last_updated_by = "123456789"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        db_session = cls._meta.sqlalchemy_session
        db_session.add(obj)
        db_session.commit()
        obj.objective_editing_levels = [0, 1, 2, 3]
        db_session.add(obj)
        return obj
