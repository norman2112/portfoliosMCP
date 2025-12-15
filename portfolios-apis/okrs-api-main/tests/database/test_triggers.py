"""
Test the triggers we have set up in the database.

The tests here will test to ensure that triggers that we have created in our
migrations are actively working with our ORM.
"""
import datetime

from open_alchemy import models
import pytest


@pytest.fixture()
def build_work_item_container():
    """Construct a WorkItemContainer with specified level_depth_default."""

    def _build_work_item_container(tenant_id_str, level_depth_default=None):
        return models.WorkItemContainer(
            external_type="leankit",
            external_id="11111111",
            level_depth_default=level_depth_default,
            tenant_id_str=tenant_id_str,
        )

    return _build_work_item_container


@pytest.fixture()
def build_work_item_container_role():
    """Construct a WorkItemContainerRole with specified WIC, user, and okr_role."""

    def _build_work_item_container(
        tenant_id_str, work_item_container, user_id, okr_role="edit"
    ):
        return models.WorkItemContainerRole(
            work_item_container=work_item_container,
            app_created_by=user_id,
            okr_role=okr_role,
            tenant_id_str=tenant_id_str,
        )

    return _build_work_item_container


@pytest.fixture()
def build_child_objective_and_parent(build_work_item_container):
    """Construct a child Objective and a related Parent Objective."""

    def _build_child_objective_and_parent(
        tenant_id_str, child_depth, parent_depth, wic=None
    ):
        if not wic:
            wic = build_work_item_container(
                tenant_id_str=tenant_id_str, level_depth_default=0
            )

        return models.Objective(
            name="Child Objective",
            level_depth=child_depth,
            work_item_container=wic,
            tenant_id_str=tenant_id_str,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            parent_objective=models.Objective(
                name="Parent Objective",
                level_depth=parent_depth,
                tenant_id_str=tenant_id_str,
                starts_at="2021-01-01",
                ends_at="2022-01-01",
                work_item_container=wic,
            ),
        )

    return _build_child_objective_and_parent


class TestObjectiveTriggers:
    """Test the database constraints and ensure errors if violations occur."""

    DEFAULT_TENANT_ID_STR = "LEANKIT~d12-10100000101"
    DEFAULT_USER_ID = "123456789"

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_valid_parent_objective_levels(
        self, db_session, create_work_item_container, build_child_objective_and_parent
    ):
        """Ensure a valid depth works properly."""
        wic = create_work_item_container(
            attribs={
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
                "level_depth_default": 0,
            }
        )

        child_objective = build_child_objective_and_parent(
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            child_depth=1,
            parent_depth=0,
            wic=wic,
        )
        db_session.add(child_objective)
        db_session.commit()
        parent_objective = child_objective.parent_objective
        assert child_objective.id
        assert child_objective.parent_objective_id == parent_objective.id

    @pytest.mark.parametrize(
        "child_depth, parent_depth",
        [
            pytest.param(0, 1, id="child-above-parent"),
            pytest.param(1, 1, id="child-equal-to-parent"),
        ],
    )
    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_invalid_parent_objective_levels(
        self,
        db_session,
        create_db_basic_setting,
        build_child_objective_and_parent,
        child_depth,
        parent_depth,
    ):
        """Ensure a depth violation raises an error."""
        create_db_basic_setting({"tenant_id_str": self.DEFAULT_TENANT_ID_STR})
        child_objective = build_child_objective_and_parent(
            self.DEFAULT_TENANT_ID_STR, child_depth, parent_depth
        )
        db_session.add(child_objective)
        with pytest.raises(Exception) as e:
            db_session.commit()

    @pytest.mark.parametrize(
        "level_depth",
        [
            pytest.param(0, id="highest-level"),
            pytest.param(3, id="lowest-level"),
        ],
    )
    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_valid_objective_levels(
        self,
        db_session,
        build_work_item_container,
        create_work_item_container,
        level_depth,
    ):
        """Ensure a valid depth works properly."""
        wic = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        objective = models.Objective(
            name="Objective",
            level_depth=level_depth,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=wic,
        )
        db_session.add(objective)
        db_session.commit()
        assert objective.id
        assert objective.level_depth == level_depth

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_invalid_objective_levels(self, db_session, create_work_item_container):
        """Ensure a depth violation raises an error."""
        wic = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        objective = models.Objective(
            name="Objective",
            level_depth=4,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=wic,
        )
        db_session.add(objective)
        with pytest.raises(Exception) as e:
            db_session.commit()

        assert "level_depth is invalid" in str(e.value)

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_valid_wic_level_depth_default_auto_applied(
        self,
        db_session,
        create_work_item_container,
    ):
        """
        Ensure a valid level_depth_default works properly.

        When a WIC is created, it should automatically set the
        level_depth_detault and the `objective_editing_levels` based on
        the default level in the Settings.
        """
        wic = create_work_item_container({"tenant_id_str": self.DEFAULT_TENANT_ID_STR})
        setting = (
            db_session.query(models.Setting)
            .filter_by(tenant_id_str=self.DEFAULT_TENANT_ID_STR)
            .first()
        )
        assert setting.level_config[3]["is_default"]
        assert wic.id
        assert wic.level_depth_default == 3
        assert wic.objective_editing_levels == [3]

    @pytest.mark.integration
    def test_invalid_wic_level_depth_default(
        self, db_session, create_work_item_container
    ):
        """
        Ensure an invalid level_depth_default raises an error.

        If we attempt to set the `level_depth_default` to a number bigger than
        the number of levels in the `level_config`, there should be a
        violation.
        """
        with pytest.raises(Exception) as e:
            create_work_item_container(
                {"tenant_id_str": self.DEFAULT_TENANT_ID_STR, "level_depth_default": 4}
            )

        assert "level_depth_default is invalid" in str(e.value)

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_valid_parent_objective_level_change(
        self,
        db_session,
        create_work_item_container,
        build_child_objective_and_parent,
    ):
        """Ensure changing level_depth of parent objective is valid."""
        wic = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        child_objective = build_child_objective_and_parent(
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            child_depth=3,
            parent_depth=0,
            wic=wic,
        )
        db_session.add(child_objective)
        db_session.commit()
        parent_objective = child_objective.parent_objective
        parent_objective.level_depth = 2
        db_session.add(parent_objective)
        db_session.commit()
        assert child_objective.level_depth > parent_objective.level_depth

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_invalid_parent_objective_level_change(
        self,
        db_session,
        create_work_item_container,
        build_child_objective_and_parent,
    ):
        """Ensure invalid level depth change raises an error."""
        wic = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        child_objective = build_child_objective_and_parent(
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            child_depth=2,
            parent_depth=1,
            wic=wic,
        )
        db_session.add(child_objective)
        db_session.commit()
        parent_objective = child_objective.parent_objective
        parent_objective.level_depth = 2
        db_session.add(parent_objective)
        with pytest.raises(Exception) as e:
            db_session.commit()

        # str(e.value) truncates the full error message, so we can only match on
        # the beginning of the error message. The error message follows the
        # format of:
        # Changing Objective (id: 39, level_depth: 1) to (level_depth: 2)
        # is not allowed as at least one child objective would have an equal
        # or lower level_depth
        assert "Changing Objective" in str(e.value)

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_setting_parent_objective_to_self(
        self,
        db_session,
        create_work_item_container,
        build_work_item_container,
    ):
        """Ensure setting parent_objective_id to self raises an error."""
        wic = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        objective = models.Objective(
            name="Objective",
            level_depth=3,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=wic,
        )
        db_session.add(objective)
        db_session.commit()
        # TODO: this seems to be erroring out and crashing the debugger.
        # I want to make sure that the new triggers we have are not
        # causing some kind of infinite loop for this test case.
        #
        objective.parent_objective_id = objective.id
        db_session.add(objective)
        with pytest.raises(Exception) as e:
            db_session.commit()

        # There are currently 2 triggers that will trap for this error.
        # One checks that the parent objective explicitly cannot be self.
        # The other checks that a parent must have lower level depth than child.
        # Either one works just fine for this purpose.
        assert "parent_objective_id cannot be current objective id" in str(
            e
        ) or "must have lower level depth" in str(e.value)

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_parent_objective_insert_access(
        self,
        db_session,
        build_level_config,
        create_work_item_container,
        build_work_item_container_role,
    ):
        """
        Ensure user has access to parent objective's WIC before allowing parent_objective_id to be set during insert.

        Setup:
        Create 2 work_item_containers.
        The first should have a work_item_container_role for which the default user has no access.
        Create an objective and attach it to the first work_item_container with the above role.
        """
        wic1 = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        wic2 = create_work_item_container(
            {
                "tenant_id_str": self.DEFAULT_TENANT_ID_STR,
                "external_id": "11111112",
                "objective_editing_levels": [0, 1, 2, 3],
            }
        )
        wic1_role = build_work_item_container_role(
            self.DEFAULT_TENANT_ID_STR, wic1, self.DEFAULT_USER_ID, okr_role="none"
        )
        parent_objective = models.Objective(
            name="Parent Objective",
            level_depth=0,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=wic1,
        )
        db_session.add_all([wic1_role, parent_objective])
        db_session.commit()
        child_objective = models.Objective(
            name="Child Objective",
            level_depth=3,
            tenant_id_str=self.DEFAULT_TENANT_ID_STR,
            starts_at="2021-01-01",
            ends_at="2022-01-01",
            work_item_container=wic2,
            parent_objective=parent_objective,
            app_created_by=self.DEFAULT_USER_ID,
        )
        db_session.add(child_objective)
        with pytest.raises(Exception) as e:
            db_session.commit()

        assert "No access to parent objective work_item_container" in str(e.value)

    @pytest.mark.integration
    def test_parent_objective_update_access(
        self,
        db_session,
        setting_factory,
        work_item_container_role_factory,
        objective_factory,
    ):
        """
        Ensure user has access to parent objective's WIC before allowing parent_objective_id to be set during update.

        Setup:
        Create 2 work_item_containers.
        The first should have a work_item_container_role for which the default user has no access.
        Create a first objective and attach it to the first work_item_container with the above role.
        Create a second objective and attach it to the second work_item_container.
        """
        setting_factory()
        wic_role1 = work_item_container_role_factory(no_access=True)
        wic_role2 = work_item_container_role_factory()
        parent_objective = objective_factory(
            level_depth=0, work_item_container=wic_role1.work_item_container
        )
        child_objective = objective_factory(
            work_item_container=wic_role2.work_item_container
        )
        db_session.commit()

        # begin test
        child_objective.parent_objective = parent_objective
        db_session.add(child_objective)
        with pytest.raises(Exception) as e:
            db_session.commit()

        assert "No access to parent objective work_item_container" in str(e.value)


class TestWorkItemContainerTriggers:
    @pytest.mark.parametrize(
        "default_level_depth",
        [
            pytest.param(0, id="default-top-level"),
            pytest.param(3, id="default-bottom-level"),
        ],
    )
    @pytest.mark.integration
    def test_wic_defaults_set_properly(
        self,
        db_session,
        build_level_config,
        setting_factory,
        work_item_container_factory,
        default_level_depth,
    ):
        """Ensure level_depth_default and objective_editing_levels set to default level."""
        level_config = build_level_config(default_level_depth=default_level_depth)
        setting_factory(level_config=level_config)
        # NOTE: to get past the wic_container_factory safeguards, we must
        # build and commit our wic.
        wic = work_item_container_factory.build()
        db_session.add(wic)
        db_session.commit()

        assert wic.level_depth_default == default_level_depth
        assert wic.objective_editing_levels == [default_level_depth]

    @pytest.mark.integration
    def test_wic_defaults_set_properly_1(
        self,
        db_session,
        build_level_config,
        setting_factory,
        work_item_container_factory,
    ):
        """Ensure level_depth_default and objective_editing_levels set to default level (3) when no settings."""
        # NOTE: to get past the wic_container_factory safeguards, we must
        # build and commit our wic.
        wic = work_item_container_factory.build()
        db_session.add(wic)
        db_session.commit()

        assert wic.level_depth_default == 3
        assert wic.objective_editing_levels == [3]

    @pytest.mark.parametrize(
        "wic_params",
        [
            pytest.param({"level_depth_default": 0}, id="level-depth_default-supplied"),
            pytest.param(
                {"objective_editing_levels": [3]},
                id="objective-editing-levels-supplied",
            ),
        ],
    )
    @pytest.mark.integration
    def test_exception_on_values_in_forbidden_columns_on_insert(
        self, db_session, setting_factory, wic_params
    ):
        """
        Ensure that providing non-null values on essential columns raises.

        A WorkItemContainer must have null values for both `level_depth_default`
        and `objective_editing_levels`. Otherwise, the database should raise an
        exception.
        """

        setting = setting_factory()
        # NOTE: To get past the wic factory safeguards,
        # we must build our wic from scratch.
        wic_params = wic_params | {
            "tenant_id_str": setting.tenant_id_str,
            "external_type": "leankit",
            "external_id": "1234",
        }
        wic = models.WorkItemContainer(**wic_params)
        db_session.add(wic)

        with pytest.raises(Exception) as e:
            db_session.commit()

        assert "must both be null on insert" in str(e.value)


class TestTimestampTriggers:
    """Ensure that the timestamp generated by triggers works."""

    @pytest.mark.integration
    def test_no_trigger_overwrite(self, db_session, setting_factory):
        """Test created_at and updated_at timestamps."""
        # Database setup
        setting = setting_factory.build()
        db_session.add(setting)
        db_session.commit()

        assert setting.created_at
        assert setting.updated_at
        assert setting.created_at == setting.updated_at

        # When we attempt to change the `updated_at` timestamp, we are
        # unsuccessful. The model's timestamp value is fetched from the
        # database; the model is then updated with the fetched timestamp values.
        setting.updated_at = "2030-01-01"
        db_session.add(setting)
        db_session.commit()

        assert setting.updated_at == setting.created_at


class TestKeyResultDateTriggers:
    """Ensure the dates for the key result are validated by triggers."""

    @pytest.mark.parametrize(
        "starts_at, ends_at, error",
        [
            pytest.param(
                "2000-01-01",
                datetime.datetime.now(),
                "Key result cannot start before related objective",
                id="early-key-result",
            ),
            pytest.param(
                datetime.datetime.now(),
                "2090-01-01",
                "Key result cannot end after related objective",
                id="late-key-result",
            ),
            pytest.param(
                datetime.datetime.now() + datetime.timedelta(2),
                datetime.datetime.now(),
                "key_result starts_at must be before ends_at",
                id="ends-before-starts",
            ),
        ],
    )
    @pytest.mark.integration
    def test_invalid_key_result_dates(
        self, db_session, setting_factory, key_result_factory, starts_at, ends_at, error
    ):
        setting_factory()
        db_session.commit()

        key_result_factory(starts_at=starts_at, ends_at=ends_at)
        with pytest.raises(Exception) as e:
            db_session.commit()

        assert error in str(e.value)


class TestObjectiveDateTriggers:
    """Ensure the dates for the key result are validated by triggers."""

    @pytest.mark.parametrize(
        "starts_at, ends_at",
        [
            pytest.param(
                "2090-01-01",
                "2090-02-01",
                id="objective-after-kr",
            )
        ],
    )
    @pytest.mark.integration
    def test_invalid_objective_dates_for_deleted_krs(
        self, db_session, setting_factory, key_result_factory, starts_at, ends_at
    ):
        # db setup
        setting_factory()
        kr = key_result_factory()
        kr.deleted_at_epoch = 123456789
        db_session.commit()

        objective = kr.objective
        oid = objective.id
        objective.starts_at = starts_at
        objective.ends_at = ends_at
        db_session.add(objective)
        db_session.commit()
        obj = db_session.query(models.Objective).get(oid)
        assert obj.starts_at.year == 2090
        assert obj.ends_at.year == 2090
