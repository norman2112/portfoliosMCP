"""Used to test model creation by FactoryBot."""

from open_alchemy import models
import pytest


class TestWorkItemContainerCreation:
    def test_unit_wic_creation(
        self, add_session_to_factories, work_item_container_factory
    ):
        add_session_to_factories()
        wic = work_item_container_factory(id=1, external_id="1234")
        assert wic.external_id == "1234"
        assert "Test Board" in wic.external_title

    @pytest.mark.integration
    def test_integration_wic_creation(
        self, db_session, setting_factory, work_item_container_factory
    ):
        setting_factory()
        wic = work_item_container_factory(external_id="9999")
        db_session.commit()

        found_wic = db_session.query(models.WorkItemContainer).get(wic.id)
        assert found_wic.external_id == "9999"
        assert found_wic.id

        found_wic.objective_editing_levels = [0, 1, 2, 3]
        found_wic.level_depth_default = 3

        db_session.add(found_wic)
        db_session.commit()

        assert found_wic.objective_editing_levels == [0, 1, 2, 3]
        assert found_wic.level_depth_default == 3


class TestObjectiveCreation:
    @pytest.mark.integration
    def test_integration_objective(
        self, db_session, objective_factory, setting_factory
    ):
        setting_factory()
        objective = objective_factory(
            work_item_container__external_title="Brassy Board"
        )
        db_session.commit()

        assert "Test Objective" in objective.name
        assert objective.level_depth == 3
        assert objective.work_item_container.external_title == "Brassy Board"
        assert objective.id


class TestKeyResultCreation:
    def test_unit_key_result_creation(
        self, add_session_to_factories, key_result_factory
    ):
        add_session_to_factories()
        key_result = key_result_factory(
            name="Test Key Result", objective__name="Special Objective"
        )
        assert key_result.name == "Test Key Result"
        assert key_result.starts_at < key_result.ends_at
        assert key_result.objective.name == "Special Objective"


class TestProgressPointCreation:
    def test_unit_progress_point_creation(
        self, add_session_to_factories, progress_point_factory
    ):
        add_session_to_factories()
        pp = progress_point_factory(value=12)
        assert pp.value == 12
        assert pp.key_result

    @pytest.mark.integration
    def test_integration_progress_point_creation(
        self, db_session, progress_point_factory, setting_factory
    ):
        setting_factory()
        pp = progress_point_factory(value=12)
        db_session.commit()

        assert pp.value == 12
        assert pp.id
        assert pp.key_result
        assert pp.key_result.objective
        assert pp.key_result.objective.work_item_container


class TestSettingCreation:
    @pytest.mark.integration
    def test_integration_setting_creation(self, db_session, setting_factory):
        setting = setting_factory()
        db_session.commit()
        assert setting.level_config
