"""Tests for WorKItemContainerRole helpers."""

from open_alchemy import models
from mock_alchemy.mocking import UnifiedAlchemyMagicMock
import pytest

from okrs_api.model_helpers.work_item_container_roles import (
    WorkItemContainerRoleBuilder,
)


class TestWorkItemContainerRoleBuilder:
    """WorkItemContainerRole Factory returns WicRoles."""

    USER_ID = "999"
    ADAPTED_ROLE_DATA = [
        {
            "context_id": "test-wic-external-id-123",
            "okr_role": "manage",
            "app_role": "boardManager",
        }
    ]

    @pytest.mark.integration
    def test_build_roles(self, db_session, work_item_container_factory):
        """Ensure that roles are built properly."""
        wic = work_item_container_factory(
            tenant_group_id_str="1231231234", external_id="test-wic-external-id-123"
        )
        db_session.commit()
        wic_dict = wic.to_dict()
        wic_role_factory = WorkItemContainerRoleBuilder(
            db_session=db_session,
            adapted_role_data=self.ADAPTED_ROLE_DATA,
            user_id=self.USER_ID,
            org_id=wic.tenant_id_str,
            available_work_item_containers=[wic_dict],
            tenant_group_id="1234",
            created_by="4321",
            app_name="leankit",
        )

        wic_roles = wic_role_factory.build_roles()
        first_role = wic_roles[0]
        assert len(wic_roles) == 1
        assert first_role.app_created_by == "999"
        assert first_role.tenant_id_str == wic.tenant_id_str

    @pytest.mark.integration
    def test_no_role_duplication(self, db_session, work_item_container_role_factory):
        """
        Ensure role duplication is not attempted.

        If a wic role already exists in the database, the `build_roles` function
        will not return a new role to be created, and instead, will return the
        existing wic role.
        """
        #  Setup DB
        existing_wic_role = work_item_container_role_factory(
            work_item_container__tenant_group_id_str="1231231234",
            work_item_container__external_id="112233",
        )
        wic = existing_wic_role.work_item_container
        db_session.commit()
        existing_wic_role_id = existing_wic_role.id
        wic_dict = wic.to_dict()
        # start test
        adapted_role_data = [
            {
                "context_id": "112233",
                "okr_role": "manage",
                "app_role": "boardManager",
            }
        ]

        wic_role_builder = WorkItemContainerRoleBuilder(
            db_session=db_session,
            adapted_role_data=adapted_role_data,
            user_id=existing_wic_role.app_created_by,
            org_id=existing_wic_role.tenant_id_str,
            available_work_item_containers=[wic_dict],
            tenant_group_id="1234",
            created_by="4321",
            app_name="leankit",
        )

        roles = wic_role_builder.build_roles()
        first_role = roles[0]

        assert len(roles) == 1
        assert first_role.id == existing_wic_role_id

        db_session.add_all(roles)
        #  Ensure no exception is raised
        db_session.commit()

    @pytest.mark.integration
    def test_pvid_user_id_update(self, db_session, work_item_container_role_factory):
        """Ensure role is updated if the pvadmin user id has changed."""

        #  Setup DB
        existing_wic_role = work_item_container_role_factory(
            work_item_container__tenant_group_id_str="1231231234",
            work_item_container__external_id="112233",
        )
        wic = existing_wic_role.work_item_container
        db_session.commit()
        existing_wic_role_id = existing_wic_role.id
        wic_dict = wic.to_dict()
        # start test
        adapted_role_data = [
            {
                "context_id": "112233",
                "okr_role": "manage",
                "app_role": "boardManager",
            }
        ]

        wic_role_builder = WorkItemContainerRoleBuilder(
            db_session=db_session,
            adapted_role_data=adapted_role_data,
            user_id=existing_wic_role.app_created_by,
            org_id=existing_wic_role.tenant_id_str,
            available_work_item_containers=[wic_dict],
            tenant_group_id="1234",
            created_by="new_created_by",
            app_name="leankit",
        )

        roles = wic_role_builder.build_roles()
        first_role = roles[0]

        assert len(roles) == 1
        assert first_role.id == existing_wic_role_id
        assert first_role.created_by == "new_created_by"

        db_session.add_all(roles)
        #  Ensure no exception is raised
        db_session.commit()

        # Query and assert the DB is updated correctly
        wic_role = (
            db_session.query(models.WorkItemContainerRole)
            .filter_by(id=existing_wic_role_id)
            .first()
        )
        assert wic_role.created_by == "new_created_by"
        assert wic_role.pv_created_by == "new_created_by"
