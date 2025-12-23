"""WorkItemContainerRole helpers."""
from open_alchemy import models

# pylint:disable=too-many-arguments
from sqlalchemy import and_
from sqlalchemy import or_


class WorkItemContainerRoleBuilder:
    """
    Build WorkItemContainerRoles from the role data.

    Role data comes from the current_user endpoint, already adapted.
    """

    def __init__(
        self,
        db_session,
        adapted_role_data,
        user_id,
        org_id,
        tenant_group_id,
        created_by,
        available_work_item_containers,
        app_name,
        token_org_id=None,
        token_user_id=None,
    ):
        """
        Initialize the WorkItemContainerRoleBuilder.

        :param db_session db_session:
        :param list adapted_role_data: a list of  Roles
        :param str user_id: the user id of the requesting user
        :param str org_id: the org id of the requesting user
        :param str tenant_group_id: the org group id of the requesting user
        :param str created_by: the planview user id of the requesting user
        :param list available_work_item_container: [WorkItemContainer]

        """
        self.db_session = db_session
        self.adapted_role_data = adapted_role_data or []
        self.user_id = user_id
        self.org_id = org_id
        self.tenant_group_id = tenant_group_id
        self.created_by = created_by
        self.app_name = app_name
        self.available_work_item_containers = available_work_item_containers or []
        self.memo = {}
        self.token_org_id = token_org_id
        self.token_user_id = token_user_id

    def build_roles(self):
        """
        Build the WIC roles.

        Use the adapted roles and save them to the database.
        """
        if not self.adapted_role_data:
            return []
        wic_roles = []
        for adapted_role in self.adapted_role_data:
            wic = self._find_wic_by_context_id(context_id=adapted_role["context_id"])
            if wic:
                wic_role = self._find_or_build_role(
                    work_item_container=wic,
                    adapted_role=adapted_role,
                )
                wic_roles.append(wic_role)
        return wic_roles

    def _find_or_build_role(self, work_item_container, adapted_role):
        """
        Find or build a WIC Role.

        If the role is found in the list of `existing_wic_roles`, update it
        and return it. Otherwise, build a new WIC role.
        """
        wic_role = next(
            (
                role
                for role in self._user_wic_roles()
                if role.work_item_container_id == work_item_container["id"]
                and str(role.app_created_by) == str(self.user_id)
                and (
                    role.tenant_id_str == self.org_id
                    or role.tenant_group_id_str == self.tenant_group_id
                )
                and work_item_container["app_name"] == self.app_name
            ),
            None,
        )
        if not wic_role:
            wic_role = models.WorkItemContainerRole(
                work_item_container_id=work_item_container["id"],
                app_created_by=self.user_id,
                tenant_id_str=self.org_id,
                tenant_group_id_str=self.tenant_group_id,
                created_by=self.created_by,
            )

        wic_role.okr_role = adapted_role["okr_role"]
        wic_role.app_role = adapted_role["app_role"]
        wic_role.tenant_id_str = work_item_container["tenant_id_str"]
        wic_role.tenant_group_id_str = work_item_container.get("tenant_group_id_str")
        wic_role.created_by = self.created_by
        return wic_role

    def _find_wic_by_context_id(self, context_id):
        """Find a wic by context id in the available wics."""
        for wic in self.available_work_item_containers:
            if wic["external_id"] == context_id:
                return wic

        return None

    def _role_context_ids(self):
        return [role_data["context_id"] for role_data in self.adapted_role_data]

    def _user_wic_roles(self):
        """
        Return all wic roles for this User/Org.

        Memoize the result.
        """
        if self.memo.get("user_wic_roles"):
            return self.memo["user_wic_roles"]
        self.memo["user_wic_roles"] = (
            self.db_session.query(models.WorkItemContainerRole)
            .filter(
                or_(
                    models.WorkItemContainerRole.created_by == self.created_by,
                    models.WorkItemContainerRole.app_created_by == self.user_id,
                )
            )
            .filter(
                or_(
                    and_(
                        models.WorkItemContainerRole.tenant_id_str == self.org_id,
                        models.WorkItemContainerRole.tenant_id_str != "",
                    ),
                    models.WorkItemContainerRole.tenant_group_id_str
                    == self.tenant_group_id,
                )
            )
            .all()
        )
        return self.memo["user_wic_roles"]

    def _get_all_wics_from_context_ids(self):
        context_ids = self._role_context_ids()
        return [
            wic
            for wic in self.available_work_item_containers
            if wic["external_id"] in context_ids
        ]
