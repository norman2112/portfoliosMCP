"""Setting factory."""

from open_alchemy import models

from tests.factories.support.common import BaseFactory, DEFAULT_TENANT_ID_STR


class UserSettingsFactory(BaseFactory):
    class Meta:
        model = models.UserSettings

    pv_tenant_id = DEFAULT_TENANT_ID_STR
    pv_created_by = "10135757568"
    pv_last_updated_by = "10135757568"
