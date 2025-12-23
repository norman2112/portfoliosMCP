"""WorkItemContainerRole factory."""

import factory
from open_alchemy import models

from tests.factories.support.common import BaseFactory
from tests.factories.work_item_container import WorkItemContainerFactory


class WorkItemContainerRoleFactory(BaseFactory):
    class Meta:
        model = models.WorkItemContainerRole

    class Params:
        manage_access = factory.Trait(
            okr_role="manage",
            app_role="boardAdministrator",
        )
        edit_access = factory.Trait(
            okr_role="edit",
            app_role="boardUser",
        )
        read_access = factory.Trait(
            okr_role="read",
            app_role="boardReader",
        )
        no_access = factory.Trait(
            okr_role="none",
            app_role=None,
        )

    okr_role = "read"
    app_role = "boardReader"
    app_created_by = factory.SelfAttribute("work_item_container.app_last_updated_by")
    created_by = factory.SelfAttribute("work_item_container.last_updated_by")
    work_item_container = factory.SubFactory(WorkItemContainerFactory)
