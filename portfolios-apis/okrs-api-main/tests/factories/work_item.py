"""KeyResultWorkItemMapping factory."""

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory
from tests.factories.work_item_container import WorkItemContainerFactory


class WorkItemFactory(BaseFactory):
    class Meta:
        model = models.WorkItem

    work_item_container = factory.SubFactory(WorkItemContainerFactory)
    external_type = "leankit"
    container_type = "lk_board"
    app_name = "leankit"
    external_id = factory.Sequence(lambda n: f"wi-{n}")
