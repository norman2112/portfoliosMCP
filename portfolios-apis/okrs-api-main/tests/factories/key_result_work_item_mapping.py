"""KeyResultWorkItemMapping factory."""

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory
from tests.factories.key_result import KeyResultFactory
from tests.factories.work_item import WorkItemFactory


class KeyResultWorkItemMappingFactory(BaseFactory):
    class Meta:
        model = models.KeyResultWorkItemMapping

    key_result = factory.SubFactory(KeyResultFactory)
    work_item = factory.SubFactory(WorkItemFactory)
