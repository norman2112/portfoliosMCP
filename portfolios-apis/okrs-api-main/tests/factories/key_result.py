"""KeyResult factory."""

import datetime

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory
from tests.factories.objective import ObjectiveFactory

STANDARD_DAY_VARIANCE = 30


class KeyResultFactory(BaseFactory):
    class Meta:
        model = models.KeyResult

    name = factory.sequence(lambda n: f"Test Key Result #{n}")
    starting_value = 0.0
    target_value = 100.0
    objective = factory.SubFactory(ObjectiveFactory)

    @factory.lazy_attribute
    def starts_at(self):
        return datetime.datetime.now() - datetime.timedelta(days=STANDARD_DAY_VARIANCE)

    @factory.lazy_attribute
    def ends_at(self):
        return datetime.datetime.now() + datetime.timedelta(days=STANDARD_DAY_VARIANCE)
