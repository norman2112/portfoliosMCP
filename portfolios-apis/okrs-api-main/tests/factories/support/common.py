"""Common attributes for all factories are stored here."""

import factory

from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from tests import models_loader

models_loader.initialize_models()

DEFAULT_TENANT_ID_STR = "LEANKIT~d12-123"


class BaseFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = UnifiedAlchemyMagicMock()

    tenant_id_str = DEFAULT_TENANT_ID_STR
