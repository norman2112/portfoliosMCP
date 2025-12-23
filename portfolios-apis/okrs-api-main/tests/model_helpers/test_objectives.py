from open_alchemy import models
import pytest
from http import HTTPStatus

from okrs_api.model_helpers.objectives import (
    decrement_objective_level_depths,
    validate_app_owned_by,
)


class TestLevelDecrementing:
    @pytest.mark.parametrize(
        "objective_depth, deleted_level_depth, expected_new_depth",
        [
            pytest.param(3, 4, 3, id="no-change"),
            pytest.param(3, 1, 2, id="move-up-one-level"),
        ],
    )
    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_decrementing_levels(
        self,
        db_session,
        create_db_basic_setting,
        build_okr,
        objective_depth,
        deleted_level_depth,
        expected_new_depth,
    ):
        """Ensure that the objective level depths are decremented properly."""
        tenant_id_str = "LEANKIT~d11-123"

        # setup database
        create_db_basic_setting({"tenant_id_str": tenant_id_str})
        okr = build_okr(tenant_id_str=tenant_id_str)
        objective = okr["objective"]
        objective.level_depth = objective_depth
        db_session.add(objective)
        db_session.commit()

        # run test
        decrement_objective_level_depths(
            db_session=db_session,
            tenant_id_str=tenant_id_str,
            tenant_group_id_str=None,
            deleted_level_depth=deleted_level_depth,
        )

        found_objective = db_session.query(models.Objective).get(objective.id)
        assert found_objective.level_depth == expected_new_depth


@pytest.fixture()
def test_validate_app_owned_by(mocker):
    """
    tests for validating app_owned_by and owned_by requirements in input_data
    """
    data = {"tenant_group_id_original": "abcd1234"}
    input_prepper = mocker.Mock(**data)
    assert (
        validate_app_owned_by({"app_owned_by": "1234", "owned_by": "12"}, input_prepper)
        is None
    )
    assert (
        validate_app_owned_by({"app_owned_by": None, "owned_by": None}, input_prepper)
        is None
    )
    assert validate_app_owned_by({}, input_prepper) is None
    assert (
        validate_app_owned_by({"app_owned_by": "1234"}, input_prepper)[0]["extensions"][
            "code"
        ]
        == HTTPStatus.BAD_REQUEST
    )
    assert (
        validate_app_owned_by(
            {"app_owned_by": "1234", "owned_by": None}, input_prepper
        )[0]["extensions"]["code"]
        == HTTPStatus.BAD_REQUEST
    )
    assert (
        validate_app_owned_by({"app_owned_by": None, "owned_by": "123"}, input_prepper)[
            0
        ]["extensions"]["code"]
        == HTTPStatus.BAD_REQUEST
    )
    data = {"tenant_group_id_original": None}
    input_prepper = mocker.Mock(**data)
    assert (
        validate_app_owned_by({"app_owned_by": "1234", "owned_by": "12"}, input_prepper)
        is None
    )
    assert (
        validate_app_owned_by({"app_owned_by": None, "owned_by": None}, input_prepper)
        is None
    )
    assert validate_app_owned_by({}, input_prepper) is None
    assert (
        validate_app_owned_by({"app_owned_by": "1234"}, input_prepper)[0]["extensions"][
            "code"
        ]
        is None
    )
    assert (
        validate_app_owned_by(
            {"app_owned_by": "1234", "owned_by": None}, input_prepper
        )[0]["extensions"]["code"]
        is None
    )
    assert (
        validate_app_owned_by({"app_owned_by": None, "owned_by": "123"}, input_prepper)[
            0
        ]["extensions"]["code"]
        is None
    )
