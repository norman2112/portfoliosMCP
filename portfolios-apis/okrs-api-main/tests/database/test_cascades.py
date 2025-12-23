"""Test issues concerned with delete cascades from the database."""
from sqlalchemy import inspect
import pytest

from open_alchemy import models

DEFAULT_TENANT_ID_STR = "LEANKIT~d09-10113280894"


class TestCascades:
    @pytest.fixture
    def create_full_okr(self, db_session, build_okr, create_work_item_container):
        """Create a full okr with all necessary objects in the database."""
        DEFAULT_TENANT_ID_STR = "LEANKIT~d12-123"

        def _create_full_okr(tenant_id_str=None):
            tenant_id_str = tenant_id_str or DEFAULT_TENANT_ID_STR
            wic = create_work_item_container(
                {
                    "tenant_id_str": tenant_id_str,
                    "objective_editing_levels": [0, 1, 2, 3],
                }
            )
            data = build_okr(tenant_id_str=tenant_id_str, wic=wic)
            objective = data["objective"]
            db_session.add(objective)
            db_session.commit()
            return objective

        return _create_full_okr

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_delete_work_item_container_cascade(self, db_session, create_full_okr):
        """
        Ensure that the DDL delete cascade does not interfere with the ORM.

        The ORM and the DDL do not play nice when it comes to cascading deletes.
        We must ensure that the ORM does not attempt to update/nullify the
        foreign keys on records that are being deleted by the DDL.
        https://docs.sqlalchemy.org/en/14/orm/cascades.html#using-foreign-key-on-delete-cascade-with-orm-relationships
        """

        #  Setup the OKR.
        objective = create_full_okr()
        objective_id = objective.id

        # Add a work item container role
        wic_role = models.WorkItemContainerRole(
            okr_role="read",
            app_created_by="1",
            work_item_container=objective.work_item_container,
        )
        db_session.add(wic_role)
        db_session.commit()
        wic_role_id = wic_role.id

        # Begin test deletion of objective.
        # We must delete without the aid of the ORM, as the passive-deletes
        # function doesn't seem to work properly.

        db_session.query(models.WorkItemContainer).filter_by(
            id=objective.work_item_container_id
        ).delete()
        db_session.commit()

        found_objectives = (
            db_session.query(models.Objective).filter_by(id=objective_id).all()
        )
        found_key_results = (
            db_session.query(models.KeyResult)
            .filter_by(objective_id=objective_id)
            .all()
        )

        found_wic_role = db_session.query(models.WorkItemContainerRole).get(wic_role_id)

        # Assert deletion of objectives, key result and wic roles
        assert not found_objectives
        assert not found_key_results
        assert wic_role_id
        assert not found_wic_role

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_delete_objective_cascade(self, db_session, create_full_okr):
        """
        Ensure that the DDL delete cascade does not interfere with the ORM.

        The ORM and the DDL do not play nice when it comes to cascading deletes.
        We must ensure that the ORM does not attempt to update/nullify the
        foreign keys on records that are being deleted by the DDL.
        https://docs.sqlalchemy.org/en/14/orm/cascades.html#using-foreign-key-on-delete-cascade-with-orm-relationships
        """

        #  Setup the OKR.
        objective = create_full_okr()
        objective_id = objective.id

        # Begin test deletion of objective.
        # We must delete without the aid of the ORM, as the passive-deletes
        # function doesn't seem to work properly.

        db_session.query(models.Objective).filter_by(id=objective_id).delete()
        db_session.commit()

        found_objectives = (
            db_session.query(models.Objective).filter_by(id=objective_id).all()
        )
        found_key_results = (
            db_session.query(models.KeyResult)
            .filter_by(objective_id=objective_id)
            .all()
        )

        assert not found_objectives
        assert not found_key_results

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_delete_key_result_cascade(self, db_session, create_full_okr):
        """
        Ensure that the DDL delete cascade does not interfere with the ORM.

        The ORM and the DDL do not play nice when it comes to cascading deletes.
        We must ensure that the ORM does not attempt to update/nullify the
        foreign keys on records that are being deleted by the DDL.
        https://docs.sqlalchemy.org/en/14/orm/cascades.html#using-foreign-key-on-delete-cascade-with-orm-relationships
        """

        objective = create_full_okr()
        key_result = objective.key_results[0]
        progress_point = key_result.progress_points[0]

        progress_point_id = progress_point.id
        key_result_id = key_result.id
        kr_inspection_data = inspect(key_result)

        assert kr_inspection_data.persistent
        assert objective.id
        assert key_result.objective_id == objective.id
        assert key_result.id

        # Now, delete the key result row directly without instantiating the ORM.
        # We do this because the backref we have between key result and object
        # will cause the ORM to attempt to first nullify the foreign key,
        # which is patently illegal to the DDL. So instead, we decide to
        # just delete the record directly, and let the DDL maintain data
        # integrity.
        db_session.query(models.KeyResult).filter_by(id=key_result_id).delete()
        db_session.commit()

        progress_points_for_key_result = (
            db_session.query(models.ProgressPoint)
            .filter_by(key_result_id=key_result_id)
            .all()
        )
        found_kr = db_session.query(models.KeyResult).get(key_result_id)
        found_pp = db_session.query(models.ProgressPoint).get(progress_point_id)

        assert not found_kr
        assert not progress_points_for_key_result
        assert not found_pp

    @pytest.mark.usefixtures("init_models")
    @pytest.mark.integration
    def test_nullify_for_parent_objective(self, db_session, create_work_item_container):
        """Ensure that a parent objective is nullified in the child objective."""
        wic = create_work_item_container(
            {
                "tenant_id_str": DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        objective = models.Objective(
            name="Child Objective",
            level_depth=3,
            tenant_id_str=DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2025-01-01",
            work_item_container=wic,
            parent_objective=models.Objective(
                name="Parent Objective",
                level_depth=0,
                tenant_id_str=DEFAULT_TENANT_ID_STR,
                starts_at="2021-01-01",
                ends_at="2025-01-01",
                work_item_container=wic,
            ),
        )
        db_session.add(objective)
        db_session.commit()

        objective_id = objective.id
        parent_objective = objective.parent_objective
        parent_objective_id = parent_objective.id

        assert parent_objective.id
        assert objective.parent_objective.name == "Parent Objective"

        # Test deletion. Delete the row entirely. Let the DDL handle the
        # nullification.
        db_session.query(models.Objective).filter_by(id=parent_objective_id).delete()
        db_session.commit()

        objective = db_session.query(models.Objective).get(objective_id)
        parent_objective = db_session.query(models.Objective).get(parent_objective_id)

        assert not parent_objective
        assert not objective.parent_objective_id
