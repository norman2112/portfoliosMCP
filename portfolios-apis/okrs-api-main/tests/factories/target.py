"""Target factory."""

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory, DEFAULT_TENANT_ID_STR
from tests.factories.key_result import KeyResultFactory


class TargetFactory(BaseFactory):
    class Meta:
        model = models.Target

    value = factory.SelfAttribute("key_result.target_value")
    starts_at = factory.SelfAttribute("key_result.starts_at")
    ends_at = factory.SelfAttribute("key_result.ends_at")

    pv_tenant_id = DEFAULT_TENANT_ID_STR
    pv_created_by = "10135757568"
    pv_last_updated_by = "10135757568"

    key_result = factory.SubFactory(KeyResultFactory)
