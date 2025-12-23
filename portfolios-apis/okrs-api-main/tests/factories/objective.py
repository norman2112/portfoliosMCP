"""Objectives factory."""
import datetime

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory
from tests.factories.work_item_container import WorkItemContainerFactory

STANDARD_DAY_VARIANCE = 60


class ObjectiveFactory(BaseFactory):
    class Meta:
        model = models.Objective

    name = factory.Sequence(lambda n: f"Test Objective {n}")
    level_depth = 3
    app_last_updated_by = factory.SelfAttribute(
        "work_item_container.app_last_updated_by"
    )

    @factory.lazy_attribute
    def starts_at(self):
        return datetime.datetime.now() - datetime.timedelta(days=STANDARD_DAY_VARIANCE)

    @factory.lazy_attribute
    def ends_at(self):
        return datetime.datetime.now() + datetime.timedelta(days=STANDARD_DAY_VARIANCE)

    work_item_container = factory.SubFactory(WorkItemContainerFactory)
