"""KeyResult factory."""

import datetime

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory
from tests.factories.objective import ObjectiveFactory


class ActivityLogFactory(BaseFactory):
    class Meta:
        model = models.ActivityLog

    objective_id = 100
    action = "insert.objectives"
    info = {
        "objective_name": "Refactor our old user management module",
        "starts_at": "2020-10-07 11:11:34.732822+00:00",
        "ends_at": "2022-10-07 11:11:34.732839+00:00",
        "parent_objective_id": 9,
        "parent_objective_name": "Increase recurring revenues",
    }
    app_created_by = factory.sequence(lambda n: int(f"123{n}"))
