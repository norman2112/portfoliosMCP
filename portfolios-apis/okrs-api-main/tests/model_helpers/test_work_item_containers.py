from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from open_alchemy import models
import pytest

from okrs_api.model_helpers.work_item_containers import (
    decrement_level_depth_defaults,
    decrement_objective_editing_levels,
)


class TestDefaultLevelDecrementing:
    """Test the decrementing of levels for WICs."""

    @pytest.mark.parametrize(
        "level_depth, expected_level_depth_default",
        [
            pytest.param(1, 2, id="higher-than-default"),
            pytest.param(4, 3, id="lower-than-default"),
            pytest.param(3, 3, id="same-as-default"),
        ],
    )
    @pytest.mark.integration
    def test_decrement_level_depth_defaults(
        self,
        db_session,
        setting_factory,
        work_item_container_factory,
        level_depth,
        expected_level_depth_default,
    ):
        """Ensure that the WIC level defaults are re-leveled properly."""
        # Setup database
        setting = setting_factory()
        wic = work_item_container_factory()

        # decrement the default level depth on the wic
        decrement_level_depth_defaults(
            db_session,
            tenant_id_str=wic.tenant_id_str,
            deleted_level_depth=level_depth,
            tenant_group_id_str=None,
            level_config=setting.level_config,
        )
        """Ensure that the level_depth_default is decremented properly."""

        found_wic = (
            db_session.query(models.WorkItemContainer)
            .filter_by(tenant_id_str=wic.tenant_id_str)
            .first()
        )
        assert found_wic.level_depth_default == expected_level_depth_default

    @pytest.mark.parametrize(
        "deleted_level_depth, current_levels, expected_editing_levels",
        [
            pytest.param(1, [0, 1, 3, 4], [0, 2, 3], id="delete-and-change-some"),
            pytest.param(1, [0, 1, 2], [0, 1], id="delete-and-reindex-back"),
            pytest.param(4, [0, 1, 3, 4], [0, 1, 3], id="delete-level-only"),
            pytest.param(4, [0, 3], [0, 3], id="no-change"),
            pytest.param(0, [], [], id="no-change-blank"),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_decrement_objective_editing_levels(
        self,
        deleted_level_depth,
        current_levels,
        expected_editing_levels,
    ):
        """Ensure the objective_editing_levels are re-leveled properly."""
        # Setup database
        db_session = UnifiedAlchemyMagicMock()
        tenant_id_str = "LEANKIT~d12-123"
        # NOTE: setting the objective_editing_levels directly on insert is
        # only possible here since we are using a mock db_session, that is
        # unaware of triggers.
        wic = models.WorkItemContainer(
            tenant_id_str=tenant_id_str,
            external_id="123",
            external_type="leankit",
            objective_editing_levels=current_levels,
        )
        db_session.add(wic)
        db_session.commit()

        # decrement the default level depth on the wic
        modified_wics = decrement_objective_editing_levels(
            db_session,
            tenant_id_str=tenant_id_str,
            deleted_level_depth=deleted_level_depth,
            tenant_group_id_str=None,
        )

        db_session.add_all(modified_wics)
        db_session.commit()

        found_wic = db_session.query(models.WorkItemContainer).first()
        assert found_wic.objective_editing_levels == expected_editing_levels
