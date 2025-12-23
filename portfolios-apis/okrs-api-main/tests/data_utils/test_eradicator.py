"""Test the Eradicator."""

from open_alchemy import models
import pytest


from okrs_api.data_utils.eradicator import Eradicator


class TestEradicator:

    TEST_TENANT_ID_STR = "LEANKIT~D555-123"

    MODELS_TO_CHECK = [
        models.Setting,
        models.WorkItemContainer,
        models.Objective,
        models.ActivityLog,
        models.ProgressPoint,
        models.WorkItem,
        models.KeyResult,
        models.KeyResultWorkItemMapping,
        models.WorkItemContainerRole,
    ]

    @pytest.fixture()
    def prep_database(
        self,
        db_session,
        setting_factory,
        progress_point_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        objective_factory,
        key_result_factory,
    ):
        setting_factory(tenant_id_str=self.TEST_TENANT_ID_STR)
        db_session.commit()
        progress_point_factory(tenant_id_str=self.TEST_TENANT_ID_STR)
        db_session.commit()
        work_item_container_factory(tenant_id_str=self.TEST_TENANT_ID_STR)
        db_session.commit()
        work_item_container_role_factory(tenant_id_str=self.TEST_TENANT_ID_STR)
        db_session.commit()
        objective_factory(tenant_id_str=self.TEST_TENANT_ID_STR)
        db_session.commit()
        key_result_factory(tenant_id_str=self.TEST_TENANT_ID_STR)
        db_session.commit()

    @pytest.mark.integration
    def test_deletion_of_tenant(self, db_session, prep_database):
        """Ensure that the tenant is deleted entirely from all relevant tables."""
        data = (
            db_session.query(models.WorkItemContainer)
            .filter(models.WorkItemContainer.tenant_id_str == self.TEST_TENANT_ID_STR)
            .all()
        )
        assert len(data) == 1

        data = (
            db_session.query(models.WorkItemContainerRole)
            .filter(
                models.WorkItemContainerRole.tenant_id_str == self.TEST_TENANT_ID_STR
            )
            .all()
        )
        assert len(data) == 1

        Eradicator.delete_tenant(db_session, tenant_id_str=self.TEST_TENANT_ID_STR)
        row_counts = [
            db_session.query(model)
            .filter_by(tenant_id_str=self.TEST_TENANT_ID_STR)
            .count()
            for model in self.MODELS_TO_CHECK
        ]

        deletion_log = (
            db_session.query(models.TenantMigrationLog)
            .filter_by(original_tenant_id_str=self.TEST_TENANT_ID_STR, message="DELETE")
            .first()
        )

        data = (
            db_session.query(models.WorkItemContainer)
            .filter(models.WorkItemContainer.tenant_id_str == self.TEST_TENANT_ID_STR)
            .all()
        )
        assert len(data) == 0

        data = (
            db_session.query(models.WorkItemContainerRole)
            .filter(
                models.WorkItemContainerRole.tenant_id_str == self.TEST_TENANT_ID_STR
            )
            .all()
        )
        assert len(data) == 0

        assert sum(row_counts) == 0
        assert deletion_log

    @pytest.mark.integration
    def test_tenants_not_deleted(self, db_session, prep_database):
        """Ensure that the tenant is deleted entirely from all relevant tables."""
        Eradicator.delete_tenant(db_session, tenant_id_str="other-tenant-id")
        row_counts = [
            db_session.query(model)
            .filter_by(tenant_id_str=self.TEST_TENANT_ID_STR)
            .count()
            for model in self.MODELS_TO_CHECK
        ]

        assert sum(row_counts)
