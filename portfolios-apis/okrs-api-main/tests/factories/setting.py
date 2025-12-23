"""Setting factory."""

from open_alchemy import models

from tests.factories.support.common import BaseFactory


class SettingFactory(BaseFactory):
    class Meta:
        model = models.Setting
