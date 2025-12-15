from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from open_alchemy import models
import pytest

from okrs_api.validators.level_config import (
    LevelConfigValidator,
    LevelConfigDeletionValidator,
)


class TestLevelConfigValidator:
    """Validate the level configs."""

    GOOD_LEVEL_CONFIG = [
        {"depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": False},
        {"depth": 1, "name": "Portfolio", "color": "#f87b55", "is_default": False},
        {"depth": 2, "name": "Program", "color": "#8ab98e", "is_default": False},
        {"depth": 3, "name": "Team", "color": "#608eb6", "is_default": True},
        {"depth": 4, "name": "Individual", "color": "#998eb6", "is_default": False},
    ]

    BAD_LEVEL_CONFIG = [
        {"depth": 0, "name": "Enterprise", "color": "#333", "is_default": False},
        {"depth": 3, "name": "Enterprise", "color": "#f87b55", "is_default": False},
        {"depth": 2, "name": "Program", "color": "#333", "is_default": True},
        {"depth": 3, "name": "Team", "color": "#608eb6", "is_default": True},
    ]

    @pytest.mark.parametrize(
        "data, expected",
        [
            pytest.param(GOOD_LEVEL_CONFIG, True, id="good-data"),
            pytest.param(BAD_LEVEL_CONFIG, False, id="bad-data"),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_validations_for_add_edit(self, mocker, mock_input_prepper, data, expected):
        """Ensure validations will trigger and produce an error message."""
        input_prepper = mock_input_prepper(data={"level_config": data})
        # begin

        validator = LevelConfigValidator(
            input_prepper=input_prepper,
            action_type="add_or_edit",
        )
        mocker.patch.object(
            validator, "_find_wic_max_default_level_depth", return_value=0
        )
        assert validator.validate() == expected

        joined_errors = " ".join(validator.full_error_messages())

        if not expected:
            assert len(validator.errors) == 3
            assert "must have exactly one default" in joined_errors
            assert "Every name must be unique" in joined_errors
            assert "Levels do not have sequential depths" in joined_errors

    @pytest.mark.parametrize(
        "level_names, action_type, valid_result",
        [
            pytest.param(
                ["Top Brass", "Mary is Better"],
                "add_or_edit",
                True,
                id="equal-is-valid",
            ),
            pytest.param(
                ["Top Brass", "Mary is Better", "Mary's Assistant"],
                "add_or_edit",
                True,
                id="add-is-valid",
            ),
            pytest.param(
                ["Top Brass"], "add_or_edit", False, id="level-removed-invalid"
            ),
            pytest.param(
                ["Top Brass"], None, False, id="level-removed-invalid-by-default"
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_level_removal_validation_for_add_edit(
        self,
        mocker,
        mock_input_prepper,
        build_level_config,
        level_names,
        action_type,
        valid_result,
    ):
        """Ensure add_or_edit ensures no level removal.."""
        org_id = "TEST-123"
        db_session = UnifiedAlchemyMagicMock()
        # # Setup
        existing_level_names = [
            "Top Brass",
            "Just Doug",
        ]
        db_session.add(
            models.Setting(
                level_config=build_level_config(names=existing_level_names),
                tenant_id_str=org_id,
            )
        )
        db_session.commit()

        # begin
        input_prepper = mock_input_prepper(
            org_id=org_id,
            db_session=db_session,
            data={"level_config": build_level_config(names=level_names)},
        )
        validator = LevelConfigValidator(
            input_prepper=input_prepper,
            action_type=action_type,
        )
        mocker.patch.object(
            validator, "_find_wic_max_default_level_depth", return_value=0
        )

        assert validator.validate() == valid_result

        joined_errors = " ".join(validator.full_error_messages())

        if not valid_result:
            assert len(validator.errors) == 1
            assert "You may not remove a level with this action." in joined_errors


class TestLevelConfigDeletionValidator:
    """Ensure that levels may be deleted safely."""

    EXISTING_LEVEL_NAMES = ["Portfolio", "Team", "Just Doug"]

    @pytest.mark.parametrize(
        "level_depth, with_objective, expected_error",
        [
            pytest.param(0, False, None, id="valid-deletion"),
            pytest.param(0, True, "Please move 1 objective", id="with-objective"),
            pytest.param(9, False, "Level depth is out of range", id="out-of-bounds"),
            pytest.param(
                2,
                False,
                "Please save changes to the default level before deleting another level.",
                id="deletion-of-default",
            ),
        ],
    )
    @pytest.mark.usefixtures("init_models")
    def test_deletion(
        self,
        mock_input_prepper,
        build_level_config,
        level_depth,
        with_objective,
        expected_error,
    ):
        org_id = "TEST~123"
        db_session = UnifiedAlchemyMagicMock()

        if with_objective:
            db_session.add(
                models.Objective(name="Test Objective", tenant_id_str=org_id)
            )
            db_session.commit()

        existing_level_config = build_level_config(
            names=self.EXISTING_LEVEL_NAMES,
            default_level_depth=2,
        )

        input_prepper = mock_input_prepper(
            org_id=org_id,
            db_session=db_session,
            data={"level_depth": level_depth},
        )
        validator = LevelConfigDeletionValidator(
            input_prepper=input_prepper,
            existing_level_config=existing_level_config,
        )
        valid = not bool(expected_error)
        assert validator.validate() == valid

        joined_errors = " ".join(validator.full_error_messages())
        if expected_error:
            assert expected_error in joined_errors

    @pytest.mark.integration
    def test_delete_validation_accross_tenant_group_id(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        setting_factory,
        objective_factory,
        work_item_container_factory,
    ):

        org_id_lk = "LK~1234"
        org_id_prm = "E1-PRM~4321"
        tenant_group_id = "343412321321312"

        setting = setting_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=0
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        objective_prm = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_prm, level_depth=2
        )
        wic_prm = work_item_container_factory(
            tenant_group_id_str=tenant_group_id,
            tenant_id_str=org_id_prm,
            app_name="e1_prm",
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        objective_prm.work_item_container_id = wic_prm.id
        wic_lk.level_depth_default = 2
        wic_prm.level_depth_default = 2

        input_prepper = mock_input_prepper(
            org_id=org_id_lk,
            tenant_group_id=tenant_group_id,
            db_session=db_session,
            app_name="leankit",
            data={"level_depth": 2},
        )
        validator = LevelConfigDeletionValidator(
            input_prepper=input_prepper,
            existing_level_config=setting.level_config,
        )

        assert validator.validate() == False
