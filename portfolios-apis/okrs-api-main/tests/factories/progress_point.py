"""Progress Point factory."""
from datetime import date

import factory
from open_alchemy import models

from tests.factories.key_result import KeyResultFactory
from tests.factories.support.common import BaseFactory


class ProgressPointFactory(BaseFactory):
    class Meta:
        model = models.ProgressPoint

    value = 10.0
    measured_at = date.today()
    key_result = factory.SubFactory(KeyResultFactory)
