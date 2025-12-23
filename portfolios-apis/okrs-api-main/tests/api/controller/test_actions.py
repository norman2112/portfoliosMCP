"""Test the actions controllers module."""
# pylint: disable=no-member
from datetime import date, datetime, timedelta, timezone
from http import HTTPStatus
import json
import pytest

from open_alchemy import models

from okrs_api.model_helpers.ca_configs import ca_config_response_adapter
from tests.external_apis.leankit import response_payloads
from okrs_api.api.controller import actions
from okrs_api.hasura.actions.service_wranglers import ServiceWrangler
from tests.hasura.actions import action_payloads
from okrs_api.model_helpers.ca_values import MAX_TEXT_LENGTH


def body_for_delete(instance_id):
    """Make the request body, using the id from the model instance."""
    return {"input": {"id": instance_id}}


class TestDeleteAndLogEndpoints:
    """Test all custom delete endpoints."""

    @pytest.mark.integration
    async def test_delete_objective(
        self,
        db_session,
        setting_factory,
        objective_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        request_with_jwt,
    ):
        """Ensure that the Objective is deleted and logged."""
        # Database setup
        setting_factory()
        objective = objective_factory()
        wic = work_item_container_factory()
        db_session.commit()
        objective.work_item_container_id = wic.id
        objective_id = objective.id
        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="10145734719"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        request_with_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.delete_objective_and_log(
            request_with_jwt, body_for_delete(objective_id)
        )

        activity_log = (
            db_session.query(models.ActivityLog)
            .filter_by(objective_id=objective_id)
            .first()
        )

        # Objective should have been deleted
        found_objective = db_session.query(models.Objective).get(objective_id)

        assert found_objective.is_deleted
        assert response_status == HTTPStatus.OK
        assert response_data == {"id": objective_id}
        assert activity_log.info

    @pytest.mark.integration
    async def test_delete_objective_with_children(
        self,
        db_session,
        setting_factory,
        objective_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        request_with_jwt,
    ):
        """Ensure that the Objective is deleted and logged but child objectives are not."""
        # Database setup
        setting_factory()
        objective = objective_factory()
        objective.level_depth = 0
        wic = work_item_container_factory()
        wic2 = work_item_container_factory()
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="10145734719"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        objective.work_item_container_id = wic.id
        objective_id = objective.id
        child_objective_1 = objective_factory()
        child_objective_2 = objective_factory()
        child_objective_1.parent_objective_id = objective_id
        child_objective_2.parent_objective_id = objective_id
        child_objective_1.work_item_container_id = wic.id  # same board as parent
        child_objective_2.work_item_container_id = wic2.id  # different board as parent
        child_objective_id_1 = child_objective_1.id
        child_objective_id_2 = child_objective_2.id

        assert child_objective_1.parent_objective_id == objective_id
        assert child_objective_2.parent_objective_id == objective_id

        request_with_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.delete_objective_and_log(
            request_with_jwt, body_for_delete(objective_id)
        )

        activity_log = (
            db_session.query(models.ActivityLog)
            .filter_by(objective_id=objective_id)
            .first()
        )

        # Objective should have been deleted but the children should be not be
        found_objective = db_session.query(models.Objective).get(objective_id)
        found_child_objective_1 = db_session.query(models.Objective).get(
            child_objective_id_1
        )
        found_child_objective_2 = db_session.query(models.Objective).get(
            child_objective_id_2
        )

        assert found_objective.is_deleted
        assert found_child_objective_1.deleted_at_epoch == 0
        assert found_child_objective_2.deleted_at_epoch == 0
        assert found_child_objective_1.parent_objective_id is None
        assert found_child_objective_2.parent_objective_id is None
        assert response_status == HTTPStatus.OK
        assert response_data == {"id": objective_id}
        assert activity_log.info

    @pytest.mark.integration
    async def test_delete_key_result(
        self, db_session, setting_factory, key_result_factory, request_with_jwt
    ):
        """Ensure that the KeyResult is deleted and logged."""
        setting_factory()
        key_result = key_result_factory()
        db_session.commit()
        key_result_id = key_result.id

        # Begin test
        request_with_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.delete_key_result_and_log(
            request=request_with_jwt, body=body_for_delete(key_result_id)
        )
        activity_log = (
            db_session.query(models.ActivityLog)
            .filter_by(key_result_id=key_result_id)
            .first()
        )

        # Key Result should have been deleted
        found_key_result = db_session.query(models.KeyResult).get(key_result_id)

        assert found_key_result.is_deleted
        assert response_status == HTTPStatus.OK
        assert response_data == {"id": key_result_id}
        assert activity_log.info

    @pytest.mark.integration
    async def test_delete_progress_point(
        self, db_session, setting_factory, progress_point_factory, request_with_jwt
    ):
        """Ensure that the ProgressPoint is deleted and logged."""
        setting_factory()
        progress_point = progress_point_factory()
        db_session.commit()
        progress_point_id = progress_point.id

        # Begin test
        request_with_jwt.app = {"db_session": db_session}
        response_data, response_status = await actions.delete_progress_point_and_log(
            request_with_jwt, body_for_delete(progress_point_id)
        )
        activity_log = (
            db_session.query(models.ActivityLog)
            .filter_by(progress_point_id=progress_point_id)
            .first()
        )

        # Progress Point should have been deleted
        found_progress_point = db_session.query(models.ProgressPoint).get(
            progress_point_id
        )

        assert found_progress_point.is_deleted
        assert response_status == HTTPStatus.OK
        assert response_data == {"id": progress_point_id}
        assert activity_log.info

    @pytest.mark.integration
    async def test_delete_key_result_mapping(
        self,
        db_session,
        setting_factory,
        key_result_work_item_mapping_factory,
        request_with_jwt,
    ):
        """Ensure that the KeyResult Mapping is deleted and logged."""
        # Setup db
        setting_factory()
        mapping = key_result_work_item_mapping_factory()
        db_session.commit()
        mapping_id = mapping.id
        work_item_id = mapping.work_item_id

        # Begin test
        request_with_jwt.app["db_session"] = db_session
        (
            response_data,
            response_status,
        ) = await actions.delete_key_result_work_item_mapping_and_log(
            request_with_jwt, body_for_delete(mapping_id)
        )
        activity_log = (
            db_session.query(models.ActivityLog)
            .filter_by(work_item_id=work_item_id)
            .first()
        )

        found_mapping = db_session.query(models.KeyResultWorkItemMapping).get(
            mapping_id
        )

        assert not found_mapping
        assert response_status == HTTPStatus.OK
        assert response_data == {"id": mapping_id}
        assert activity_log.info


class TestSearchActivityContainer:
    """Ensure all actions can be addressed properly."""

    @pytest.mark.vcr()
    async def test_search_unauthorized(self, connexion_client, request_with_jwt):
        """Ensure that we get the same status code from the external api."""
        response_data, response_status = await actions.search_activity_containers(
            request_with_jwt, action_payloads.search_leankit_activities_containers()
        )

        all_error_messages = ", ".join(response_data["errors"])
        assert "Failure from external api" in all_error_messages
        assert response_status == HTTPStatus.UNAUTHORIZED


class TestCreateActivity:
    """
    Ensures create_activity returns correct response.
    """

    @pytest.mark.vcr
    @pytest.mark.integration
    async def test_create_success(
        self, db_session, request_with_pts_jwt, key_result_factory
    ):
        """
        Tests that the create_activity returns a HTTPStatus OK.
        """
        # Begin payload
        key_result = key_result_factory()
        db_session.commit()
        request_with_pts_jwt.app["db_session"] = db_session

        # Begin test
        response_data, response_status = await actions.create_activity(
            request_with_pts_jwt, action_payloads.create_leankit_activity(key_result)
        )
        assert response_status == HTTPStatus.OK
        assert response_data["id"]
        assert response_data["state"] == "not_started"
        assert response_data["external_id"]

    async def test_create_error_case(self, request_with_jwt, mocker):
        """
        Tests that the create_activity returns an error when the wrangler.action_was_successful
        returns a False
        """
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=({"errors": ["Bad Data"]}, HTTPStatus.UNPROCESSABLE_ENTITY),
        )
        response_data, response_status = await actions.create_activity(
            request_with_jwt, action_payloads.create_leankit_activity()
        )
        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_data["errors"] == ["Bad Data"]


class TestConnectActivity:
    """Ensure connect_activities returns a correct response."""

    @pytest.mark.integration
    async def test_connect_activities_success(
        self,
        setting_factory,
        work_item_factory,
        key_result_factory,
        request_with_db_session,
    ):
        """
        Tests that the connect_activities returns a HTTPStatus OK when
        a key result work item mapping is created successfully, using a new
        set of work item attributes.
        """
        db_session = request_with_db_session.app["db_session"]
        setting_factory()
        key_result = key_result_factory()
        db_session.commit()
        key_result_id = key_result.id

        # request_with_jwt.app["db_session"] = db_session
        new_work_item = work_item_factory.build()

        response_data, response_status = await actions.connect_activities(
            request_with_db_session,
            action_payloads.connect_leankit_activities(key_result, new_work_item),
        )
        first_connection = response_data[0]
        assert response_status == HTTPStatus.OK
        assert first_connection["id"]
        assert first_connection["key_result_id"] == key_result_id
        assert first_connection["work_item_id"]

    class TestCurrentUser:
        """Ensure that the current_user endpoint functions properly."""

        CURRENT_USER_ADAPTED_RESPONSE = {
            "id": "1234567890",
            "first_name": "Test",
            "last_name": "User",
            "email_address": "test@example.com",
            "work_item_container_roles": [
                {
                    "context_id": "test-board-1234",
                    "okr_role": "none",
                    "app_role": "noAccess",
                }
            ],
        }

        REQUEST_BODY = {
            "input": {"product_type": "leankit"},
            "action": {"name": "current_user"},
        }

        @pytest.mark.integration
        async def test_current_user(
            self, db_session, mocker, request_with_jwt, work_item_container_factory
        ):
            request_with_jwt.app["db_session"] = db_session
            # setup database
            mockWic = work_item_container_factory(external_id="test-board-1234")
            db_session.commit()
            wic_id = mockWic.id

            # setup mocks
            mocker.patch.object(
                ServiceWrangler,
                "call_service",
                return_value=(self.CURRENT_USER_ADAPTED_RESPONSE, HTTPStatus.OK),
            )

            # execute test
            response_data, response_status = await actions.current_user(
                request_with_jwt,
                self.REQUEST_BODY,
            )

            found_wic_role = (
                db_session.query(models.WorkItemContainerRole)
                .filter_by(work_item_container_id=wic_id)
                .first()
            )
            assert response_status == HTTPStatus.OK
            assert found_wic_role.okr_role == "none"
            assert found_wic_role.app_role == "noAccess"

    CURRENT_USER_ADAPTED_RESPONSE = {
        "id": "1234567890",
        "first_name": "Test",
        "last_name": "User",
        "email_address": "test@example.com",
        "work_item_container_roles": [
            {
                "context_id": "test-board-1234",
                "okr_role": "none",
                "app_role": "noAccess",
            }
        ],
    }

    REQUEST_BODY = {
        "input": {"product_type": "leankit"},
        "action": {"name": "current_user"},
    }

    @pytest.mark.integration
    async def test_current_user(
        self, db_session, mocker, request_with_jwt, work_item_container_factory
    ):
        request_with_jwt.app["db_session"] = db_session
        # setup database
        mockWic = work_item_container_factory(
            tenant_group_id_str="1231231234", external_id="test-board-1234"
        )
        db_session.commit()
        wic_id = mockWic.id
        # setup mocks
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=(self.CURRENT_USER_ADAPTED_RESPONSE, HTTPStatus.OK),
        )

        # execute test
        response_data, response_status = await actions.current_user(
            request_with_jwt,
            self.REQUEST_BODY,
        )

        found_wic_role = (
            db_session.query(models.WorkItemContainerRole)
            .filter_by(work_item_container_id=wic_id)
            .first()
        )
        assert response_status == HTTPStatus.OK
        assert found_wic_role.okr_role == "none"
        assert found_wic_role.app_role == "noAccess"

    @pytest.mark.integration
    async def test_current_user_existing_wic_role(
        self,
        db_session,
        mocker,
        request_with_jwt,
        setting_factory,
        work_item_container_role_factory,
    ):
        """
        Do not duplicate a WorkItemContainerRole if it exists.

        Will not error out. Instead, will put in the role.
        """
        # setup database
        setting_factory()
        external_id = "test-board-1234"
        user_id = "123"
        tenant_group_id_str = "1231231234"
        #  Make a read-access wic role.
        wic_role = work_item_container_role_factory(
            work_item_container__tenant_group_id_str=tenant_group_id_str,
            work_item_container__external_id=external_id,
            work_item_container__app_created_by=user_id,
            app_created_by=user_id,
            read_access=True,
        )
        db_session.commit()
        work_item_container_id = wic_role.work_item_container_id

        # setup mocks
        # Mock the service wrangler to return a mock response from the leankit api
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=(self.CURRENT_USER_ADAPTED_RESPONSE, HTTPStatus.OK),
        )
        # Mock the user id in our JWT to match that of the user id in this test
        mocker.patch("okrs_api.hasura.actions.auth.JWTParser.user_id", user_id)

        # execute test
        request_with_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.current_user(
            request_with_jwt,
            self.REQUEST_BODY,
        )

        found_wic_role = (
            db_session.query(models.WorkItemContainerRole)
            .filter_by(
                app_created_by=user_id, work_item_container_id=work_item_container_id
            )
            .first()
        )
        assert response_status == HTTPStatus.OK
        assert found_wic_role.okr_role == "none"
        assert found_wic_role.app_role == "noAccess"


class TestSearchActivity:
    """Ensure search_activities returns a correct response."""

    @pytest.mark.vcr
    async def test_search_activities_success(self, request_with_pts_jwt):
        """Tests that the search_activities returns a HTTPStatus OK."""
        response_data, response_status = await actions.search_activities(
            request_with_pts_jwt,
            action_payloads.search_leankit_activities(),
        )
        first_activity = response_data[0]
        assert response_status == HTTPStatus.OK
        assert {"title", "external_type", "state", "item_type"}.issubset(
            list(first_activity.keys())
        )

    async def test_search_activities_error_case(self, mocker, request_with_jwt):
        """
        Tests that the search_activities returns an error when the wrangler.action_was_successful
        returns a False
        """
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=({"errors": ["Bad Search"]}, HTTPStatus.UNPROCESSABLE_ENTITY),
        )
        response_data, response_status = await actions.search_activities(
            request_with_jwt,
            action_payloads.search_leankit_activities(),
        )
        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestSearchActivityContainerFromActions:
    """Ensure search_activity_containers returns a correct response."""

    async def test_search_activity_container_success(self, mocker, request_with_jwt):
        """
        Tests that the search_activity_containers returns a HTTPStatus OK when
        SearchActivityContainersServiceWrangler.search is a success
        """
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=(
                response_payloads.leankit_search_activity_containers_response(),
                HTTPStatus.OK,
            ),
        )
        response_data, response_status = await actions.search_activity_containers(
            request_with_jwt,
            action_payloads.search_leankit_activities_containers(),
        )
        assert response_status == HTTPStatus.OK
        assert response_data["board_name"] == "Test"

    async def test_search_activity_container_error_case(self, mocker, request_with_jwt):
        """
        Tests that the search_activity_containers returns an error.
        """
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=({"errors": ["bad search"]}, HTTPStatus.UNPROCESSABLE_ENTITY),
        )
        response_data, response_status = await actions.search_activity_containers(
            request_with_jwt,
            action_payloads.search_leankit_activities_containers(),
        )
        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestListActivity:
    """Ensure list_activity_types returns a correct response."""

    async def test_list_activity_types_success(self, mocker, request_with_jwt):
        """Tests that the list_activity_types returns a HTTPStatus OK."""
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=(
                response_payloads.leankit_list_activity_types_response(),
                HTTPStatus.OK,
            ),
        )
        response_data, response_status = await actions.list_activity_types(
            request_with_jwt,
            action_payloads.search_leankit_activities_containers(),
        )
        assert response_status == HTTPStatus.OK
        assert response_data["activity_type"] == "defect"

    async def test_list_activity_types_error_case(self, mocker, request_with_jwt):
        """Test that the list_activity_types returns an error."""
        mocker.patch.object(
            ServiceWrangler,
            "call_service",
            return_value=({"errors": ["bad query"]}, HTTPStatus.UNPROCESSABLE_ENTITY),
        )
        response_data, response_status = await actions.list_activity_types(
            request_with_jwt,
            action_payloads.search_leankit_activities_containers(),
        )
        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY


class TestUpdateLevelConfig:
    """Ensure update_level_config returns the correct response."""

    BAD_LEVEL_CONFIG = [
        {
            "depth": 1,
            "name": "Bogus",
            "color": "#ba8aa4",
            "is_default": False,
        }
    ]

    @pytest.fixture
    def mock_setting(self, init_models):
        """Return a Setting to test with."""
        return models.Setting(
            level_config=[{"name": "Portfolio", "depth": 0, "is_default": True}],
            tenant_id_str="TEST-ORG",
        )

    @pytest.fixture
    def mock_settings_manager(self, mocker, mock_setting):
        manager = mocker.Mock(find_or_build=mocker.Mock(return_value=mock_setting))
        mocker.patch("okrs_api.api.controller.actions.SettingsManager", manager)

    @pytest.mark.usefixtures("mock_settings_manager")
    async def test_update_success(self, request_with_jwt, mock_input_prepper):
        """Ensure update happens successfully."""
        response_data, response_status = await actions.update_level_config(
            request_with_jwt,
            action_payloads.update_level_config_request(),
        )
        assert response_status == HTTPStatus.OK
        assert response_data.get("errors") == []

    @pytest.mark.integration
    async def test_update_with_blank_tenant_id_in_jwt_success(
        self, db_session, request_with_pvadmin_settings_jwt, build_level_config
    ):
        """Ensure that update finds the right level."""
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Create two rows with different tenant group id and blank tenant id
        db_session.add(
            models.Setting(
                level_config=build_level_config(
                    names=["Program", "Team", "Support", "Devs", "QA"],
                    default_level_depth=0,
                ),
                tenant_id_str="",
                tenant_group_id_str="some other tenant group id - 1",
            )
        )
        db_session.add(
            models.Setting(
                level_config=build_level_config(
                    names=["Portfolio"], default_level_depth=0
                ),
                tenant_id_str="",
                tenant_group_id_str="some other tenant group id - 2",
            )
        )
        db_session.commit()

        updated_config = build_level_config(
            names=["Enterprise Portfolio", "Team", "Support Level 1"],
            default_level_depth=2,
        )

        # begin test
        response_data, response_status = await actions.update_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_config": updated_config},
                "action": {"name": "update_level_config"},
            },
        )

        # Blank tenant ids should not match - it should create a new default one for this update
        assert response_status != HTTPStatus.UNPROCESSABLE_ENTITY

    @pytest.mark.usefixtures("mock_settings_manager")
    async def test_update_failure(self, request_with_jwt, mock_input_prepper):
        """Ensure update produces appropriate errors for bad level config."""
        response_data, response_status = await actions.update_level_config(
            request_with_jwt,
            {"input": {"level_config": self.BAD_LEVEL_CONFIG}},
        )
        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_data.get("errors")[0]["code"] == "depth_sequence"


class TestInsertLevelConfig:
    """Ensure insert_level_config returns the correct response."""

    @pytest.mark.integration
    async def test_insert_at_penultimate_success(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_middle_request(),
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 4
        assert not response_level_config[2]["is_default"]
        assert response_level_config[3]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names
        assert response_level_names[2] == "Team 0"
        assert "Team" in response_level_names

    @pytest.mark.integration
    async def test_insert_at_beginning_success(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=0
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_beginning_request(),
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 4
        assert not response_level_config[0]["is_default"]
        assert response_level_config[1]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names
        assert response_level_names[0] == "Super Enterprise"
        assert "Team" in response_level_names

    @pytest.mark.integration
    async def test_insert_at_middle_success(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_middle_request2(),
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 4
        assert not response_level_config[2]["is_default"]
        assert response_level_config[3]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names
        assert response_level_names[1] == "Minimum Support"
        assert "Team" in response_level_names

    @pytest.mark.integration
    async def test_insert_at_last_success(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_last_request(),
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 4
        assert response_level_config[2]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names
        assert response_level_names[3] == "QA"
        assert "Team" in response_level_names

    @pytest.mark.integration
    async def test_insert_at_invalid_fail_1(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_invalid_request1(),
        )

        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_data["errors"] != []

    @pytest.mark.integration
    async def test_insert_at_invalid_fail_2(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_invalid_request2(),
        )

        assert response_status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response_data["errors"] != []

    async def test_not_found_setting_response(self, request_with_jwt):
        """Ensure proper errors and status when setting is not found."""
        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_middle_request(),
        )

        joined_errors = " ".join(error["message"] for error in response_data["errors"])

        assert "Could not find the Setting for this org" in joined_errors
        assert response_status == HTTPStatus.NOT_FOUND

    @pytest.mark.integration
    async def test_insert_at_middle_with_objective_success(
        self,
        db_session,
        request_with_jwt,
        build_level_config,
        objective_factory,
        key_result_factory,
    ):
        """Ensure that a level may be inserted properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        obj = objective_factory(name="Test", level_depth=2)
        kr = key_result_factory(objective=obj)
        db_session.add(obj)
        db_session.add(kr)
        db_session.commit()
        objective_id = obj.id
        kr_id = kr.id

        found_objective = db_session.query(models.Objective).get(objective_id)
        assert found_objective.level_depth == 2

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_jwt,
            body=action_payloads.insert_level_config_middle_request(),
        )

        found_objective = db_session.query(models.Objective).get(objective_id)
        found_kr = db_session.query(models.KeyResult).get(kr_id)

        response_level_config = response_data["level_config"]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 4
        assert not response_level_config[2]["is_default"]
        assert response_level_config[3]["is_default"]
        assert found_objective.level_depth == 3
        assert found_kr.objective.level_depth == 3

    @pytest.mark.integration
    async def test_insert_with_pvadmin_token_success(
        self, db_session, request_with_pvadmin_settings_jwt, build_level_config
    ):
        """Ensure that a level may be inserted properly."""
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        tenant_group_id = "1231231234"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str=org_id,
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_pvadmin_settings_jwt,
            body=action_payloads.insert_level_config_middle_request(),
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 4
        assert not response_level_config[2]["is_default"]
        assert response_level_config[3]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names
        assert response_level_names[2] == "Team 0"
        assert "Team" in response_level_names

    @pytest.mark.integration
    async def test_insert_with_blank_tenant_id_in_jwt_not_found(
        self, db_session, request_with_pvadmin_settings_jwt, build_level_config
    ):
        """Ensure that we find the right config level or a proper error is thrown."""
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        db_session.add(
            models.Setting(
                level_config=build_level_config(
                    names=["Portfolio"], default_level_depth=0
                ),
                tenant_id_str="",
                tenant_group_id_str="some other tenant group id",
            )
        )
        db_session.commit()

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 1},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        assert response_status == HTTPStatus.NOT_FOUND

    @pytest.mark.integration
    async def test_relevel_after_insert(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        org_id_prm = "E1-PRM~4321"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=3
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        objective_prm = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_prm
        )
        wic_prm = work_item_container_factory(
            tenant_group_id_str=tenant_group_id,
            tenant_id_str=org_id_prm,
            app_name="e1_prm",
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        objective_prm.work_item_container_id = wic_prm.id
        wic_lk.level_depth_default = 4
        wic_prm.level_depth_default = 4
        objective_prm.level_depth = 4
        db_session.commit()

        obj_lk_id = objective_lk.id
        obj_prm_id = objective_prm.id

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {
                    "new_level": {
                        "depth": 2,
                        "name": "Company",
                        "color": "#ba8aa3",
                        "is_default": False,
                    }
                },
                "action": {"name": "insert_level_config"},
            },
        )

        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 4
        assert obj_lk.work_item_container.level_depth_default == 5
        obj_prm = db_session.query(models.Objective).filter_by(id=obj_prm_id).first()
        assert obj_prm.level_depth == 5
        assert obj_prm.work_item_container.level_depth_default == 5

    @pytest.mark.integration
    async def test_relevel_after_insert_from_one_app(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LEANKIT~d12-123"
        org_id_prm = "E1-PRM~4321"
        tenant_group_id = "1231231234"
        request_with_pvadmin_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=3
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        objective_prm = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_prm
        )
        wic_prm = work_item_container_factory(
            tenant_group_id_str=tenant_group_id,
            tenant_id_str=org_id_prm,
            app_name="e1_prm",
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        objective_prm.work_item_container_id = wic_prm.id
        wic_lk.level_depth_default = 4
        wic_prm.level_depth_default = 4
        objective_prm.level_depth = 4
        db_session.commit()

        obj_lk_id = objective_lk.id
        obj_prm_id = objective_prm.id

        # begin test
        response_data, response_status = await actions.insert_level_config(
            request=request_with_pvadmin_jwt,
            body={
                "input": {
                    "new_level": {
                        "depth": 2,
                        "name": "Company",
                        "color": "#ba8aa3",
                        "is_default": False,
                    }
                },
                "action": {"name": "insert_level_config"},
            },
        )

        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 4
        assert obj_lk.work_item_container.level_depth_default == 5
        obj_prm = db_session.query(models.Objective).filter_by(id=obj_prm_id).first()
        assert obj_prm.level_depth == 5
        assert obj_prm.work_item_container.level_depth_default == 5


class TestDeleteLevelFromLevelConfig:
    """Ensure deleting a level from level_config returns the correct response."""

    @pytest.mark.integration
    async def test_delete_success(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_jwt.app["db_session"] = db_session
        org_id = "LEANKIT~d12-123"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(models.Setting(level_config=level_config, tenant_id_str=org_id))
        db_session.commit()

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_jwt,
            body={
                "input": {"level_depth": 1},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 2
        assert not response_level_config[0]["is_default"]
        assert response_level_config[1]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names

    @pytest.mark.integration
    async def test_relevel_after_delete_first_level_with_editable_levels(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=0
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        wic_lk.level_depth_default = 0
        objective_lk.level_depth = 1
        objective_lk.work_item_container.objective_editing_levels = [0, 2, 3]
        db_session.commit()

        obj_lk_id = objective_lk.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 0},
                "action": {"name": "delete_level_from_level_config"},
            },
        )
        setting = (
            db_session.query(models.Setting)
            .filter(models.Setting.tenant_group_id_str == tenant_group_id)
            .first()
        )
        # raise NameError(setting.level_config)
        assert len(setting.level_config) == 5
        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 0
        assert obj_lk.work_item_container.level_depth_default == 0
        assert obj_lk.work_item_container.objective_editing_levels == [1, 2]

    @pytest.mark.integration
    async def test_relevel_after_delete_first_level_with_no_editable_levels(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=0
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        wic_lk.level_depth_default = 0
        objective_lk.level_depth = 1
        objective_lk.work_item_container.objective_editing_levels = []
        db_session.commit()

        obj_lk_id = objective_lk.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 0},
                "action": {"name": "delete_level_from_level_config"},
            },
        )
        setting = (
            db_session.query(models.Setting)
            .filter(models.Setting.tenant_group_id_str == tenant_group_id)
            .first()
        )
        # raise NameError(setting.level_config)
        assert len(setting.level_config) == 5
        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 0
        assert obj_lk.work_item_container.level_depth_default == 0
        assert obj_lk.work_item_container.objective_editing_levels == []

    @pytest.mark.integration
    async def test_relevel_after_delete_first_level_with_editable_levels(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=0
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        wic_lk.level_depth_default = 0
        objective_lk.level_depth = 1
        objective_lk.work_item_container.objective_editing_levels = [0, 2, 4]
        db_session.commit()

        obj_lk_id = objective_lk.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 0},
                "action": {"name": "delete_level_from_level_config"},
            },
        )
        setting = (
            db_session.query(models.Setting)
            .filter(models.Setting.tenant_group_id_str == tenant_group_id)
            .first()
        )
        # raise NameError(setting.level_config)
        assert len(setting.level_config) == 5
        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 0
        assert obj_lk.work_item_container.level_depth_default == 0
        assert obj_lk.work_item_container.objective_editing_levels == [1, 3]

    @pytest.mark.integration
    async def test_relevel_after_delete_last_level_with_no_editable_levels(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=0
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        wic_lk.level_depth_default = 5
        objective_lk.level_depth = 0
        objective_lk.work_item_container.objective_editing_levels = [5]
        db_session.commit()

        obj_lk_id = objective_lk.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 5},
                "action": {"name": "delete_level_from_level_config"},
            },
        )
        setting = (
            db_session.query(models.Setting)
            .filter(models.Setting.tenant_group_id_str == tenant_group_id)
            .first()
        )
        # raise NameError(setting.level_config)
        assert len(setting.level_config) == 5
        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 0
        assert obj_lk.work_item_container.level_depth_default == 3
        assert obj_lk.work_item_container.objective_editing_levels == []

    @pytest.mark.integration
    async def test_relevel_after_delete_last_level_with_editable_levels(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=0
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        wic_lk.level_depth_default = 5
        objective_lk.level_depth = 0
        objective_lk.work_item_container.objective_editing_levels = [0, 2, 4, 5]
        db_session.commit()

        obj_lk_id = objective_lk.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 5},
                "action": {"name": "delete_level_from_level_config"},
            },
        )
        setting = (
            db_session.query(models.Setting)
            .filter(models.Setting.tenant_group_id_str == tenant_group_id)
            .first()
        )
        assert len(setting.level_config) == 5
        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 0
        assert obj_lk.work_item_container.level_depth_default == 3
        assert obj_lk.work_item_container.objective_editing_levels == [0, 2, 4]

    @pytest.mark.integration
    async def test_delete_with_blank_tenant_id_success(
        self, db_session, request_with_pvadmin_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly with only matching group id."""
        request_with_pvadmin_jwt.app["db_session"] = db_session
        org_id = ""
        tenant_group_id = "1231231234"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str=org_id,
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_jwt,
            body={
                "input": {"level_depth": 1},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 2
        assert not response_level_config[0]["is_default"]
        assert response_level_config[1]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names

    @pytest.mark.integration
    async def test_delete_with_blank_tenant_id_in_jwt_not_found(
        self, db_session, request_with_pvadmin_settings_jwt, build_level_config
    ):
        """Ensure that we find the right config level or a proper error is thrown."""
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        db_session.add(
            models.Setting(
                level_config=build_level_config(
                    names=["Portfolio"], default_level_depth=0
                ),
                tenant_id_str="",
                tenant_group_id_str="some other tenant group id",
            )
        )
        db_session.commit()

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 1},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        assert response_status == HTTPStatus.NOT_FOUND

    @pytest.mark.integration
    async def test_delete_with_blank_tenant_id_in_jwt_success(
        self, db_session, request_with_pvadmin_settings_jwt, build_level_config
    ):
        """Ensure that a level may be removed properly."""
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session
        org_id = ""
        tenant_group_id = "1231231234"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=build_level_config(
                    names=["Program"], default_level_depth=0
                ),
                tenant_id_str="",
                tenant_group_id_str="some another tenant group id",
            )
        )
        db_session.add(
            models.Setting(
                level_config=build_level_config(
                    names=["Portfolio"], default_level_depth=0
                ),
                tenant_id_str="",
                tenant_group_id_str="some other tenant group id",
            )
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str=org_id,
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 1},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        response_level_config = response_data["level_config"]
        response_level_names = [level["name"] for level in response_level_config]
        assert response_status == HTTPStatus.OK
        assert response_data["errors"] == []
        assert len(response_level_config) == 2
        assert not response_level_config[0]["is_default"]
        assert response_level_config[1]["is_default"]
        assert "Portfolio" in response_level_names
        assert "Support" in response_level_names

    async def test_not_found_setting_response(self, request_with_jwt):
        """Ensure proper errors and status when setting is not found."""
        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_jwt,
            body={
                "input": {"level_depth": 1},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        joined_errors = " ".join(error["message"] for error in response_data["errors"])

        assert "Could not find the Setting for this org" in joined_errors
        assert response_status == HTTPStatus.NOT_FOUND

    @pytest.mark.integration
    async def test_relevel_after_delete(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_settings_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LK~1234"
        org_id_prm = "E1-PRM~4321"
        tenant_group_id = "1231231234"
        request_with_pvadmin_settings_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=3
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        objective_prm = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_prm
        )
        wic_prm = work_item_container_factory(
            tenant_group_id_str=tenant_group_id,
            tenant_id_str=org_id_prm,
            app_name="e1_prm",
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        objective_prm.work_item_container_id = wic_prm.id
        wic_lk.level_depth_default = 4
        wic_prm.level_depth_default = 4
        objective_prm.level_depth = 4
        db_session.commit()

        obj_lk_id = objective_lk.id
        obj_prm_id = objective_prm.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_settings_jwt,
            body={
                "input": {"level_depth": 2},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 2
        assert obj_lk.work_item_container.level_depth_default == 3
        obj_prm = db_session.query(models.Objective).filter_by(id=obj_prm_id).first()
        assert obj_prm.level_depth == 3
        assert obj_prm.work_item_container.level_depth_default == 3

    @pytest.mark.integration
    async def test_relevel_after_delete_from_one_app(
        self,
        db_session,
        mock_input_prepper,
        build_level_config,
        request_with_pvadmin_jwt,
        objective_factory,
        work_item_container_factory,
    ):
        org_id_lk = "LEANKIT~d12-123"
        org_id_prm = "E1-PRM~4321"
        tenant_group_id = "1231231234"
        request_with_pvadmin_jwt.app["db_session"] = db_session

        # Set up levels config
        level_config = build_level_config(
            names=["Enterprise", "Portfolio", "Program", "Team", "Support", "Closure"],
            default_level_depth=3,
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_id_str="",
                tenant_group_id_str=tenant_group_id,
            )
        )
        db_session.commit()

        objective_lk = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk, level_depth=3
        )
        wic_lk = work_item_container_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_lk
        )
        objective_prm = objective_factory(
            tenant_group_id_str=tenant_group_id, tenant_id_str=org_id_prm
        )
        wic_prm = work_item_container_factory(
            tenant_group_id_str=tenant_group_id,
            tenant_id_str=org_id_prm,
            app_name="e1_prm",
        )
        db_session.commit()
        objective_lk.work_item_container_id = wic_lk.id
        objective_prm.work_item_container_id = wic_prm.id
        wic_lk.level_depth_default = 4
        wic_prm.level_depth_default = 4
        objective_prm.level_depth = 4
        db_session.commit()

        obj_lk_id = objective_lk.id
        obj_prm_id = objective_prm.id

        # begin test
        response_data, response_status = await actions.delete_level_from_level_config(
            request=request_with_pvadmin_jwt,
            body={
                "input": {"level_depth": 2},
                "action": {"name": "delete_level_from_level_config"},
            },
        )

        assert response_status == HTTPStatus.OK
        obj_lk = db_session.query(models.Objective).filter_by(id=obj_lk_id).first()
        assert obj_lk.level_depth == 2
        assert obj_lk.work_item_container.level_depth_default == 3
        obj_prm = db_session.query(models.Objective).filter_by(id=obj_prm_id).first()
        assert obj_prm.level_depth == 3
        assert obj_prm.work_item_container.level_depth_default == 3


class TestCustomAttrConfigRead:
    """Ensure when we read the configurations, we get the right data."""

    @pytest.fixture
    async def patch_adapter(self, mocker):
        """Patch the response adapter to not sort."""
        mocker.patch(
            "okrs_api.api.controller.actions.ca_configs_response_adapter",
            lambda ca_configs: [ca_config_response_adapter(x) for x in ca_configs],
        )

    @pytest.mark.integration
    async def test_default_configs(
        self, db_session, request_with_real_pvadmin_settings_jwt, patch_adapter
    ):
        """A read from any tenant group id will always create the default fields."""
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

    @pytest.mark.integration
    async def test_default_configs_with_non_pvadmin(
        self, db_session, request_with_jwt, patch_adapter
    ):
        """A read from any tenant group id will always create the default fields."""
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_jwt,
            body={
                "input": {},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST
        errors = json.loads(response_data["message"])
        assert errors[0]["error_code"] == "NO_PVADMIN_CUSTOMER"

    @pytest.mark.integration
    async def test_default_configs_multiple_calls(
        self, db_session, request_with_real_pvadmin_settings_jwt, patch_adapter
    ):
        """A read from any tenant group id multiple times will not create duplicates."""

        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

        # Call again
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

    @pytest.mark.integration
    async def test_default_configs_multiple_calls_with_params(
        self, db_session, request_with_real_pvadmin_settings_jwt, patch_adapter
    ):
        """A read from any tenant group id multiple times will not, passing options, create duplicates."""

        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_archived": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK

        # Call again
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

    @pytest.mark.integration
    async def test_default_configs_with_non_manager_role(
        self, db_session, request_with_real_edit_jwt, patch_adapter
    ):
        """A read from any tenant group id multiple times will not, passing options, create duplicates."""

        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_edit_jwt,
            body={
                "input": {"is_archived": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK

        # Call again
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_edit_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"


class TestCustomAttrConfigInsert:
    """Ensure when we insert configurations, we get the right data."""

    @pytest.fixture
    async def patch_adapter(self, mocker):
        """Patch the response adapter to not sort."""
        mocker.patch(
            "okrs_api.api.controller.actions.ca_configs_response_adapter",
            lambda ca_configs: [ca_config_response_adapter(x) for x in ca_configs],
        )

    @pytest.mark.integration
    async def test_text_field(
        self, db_session, request_with_real_pvadmin_settings_jwt, patch_adapter
    ):
        """A read from any tenant group id will always create the default fields."""
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

        (
            response_data,
            response_status,
        ) = await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "text",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert response_data
        assert response_data["label"] == "Simple text field"
        assert response_data["is_objective"] is True
        assert response_data["is_keyresult"] is False
        assert response_data["is_mandatory_keyresult"] is True

    @pytest.mark.integration
    async def test_numeric_field(
        self, db_session, request_with_real_pvadmin_settings_jwt, patch_adapter
    ):
        """A read from any tenant group id will always create the default fields."""
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

        (
            response_data,
            response_status,
        ) = await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "numeric",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert response_data
        assert response_data["label"] == "Simple text field"
        assert response_data["is_objective"] is True
        assert response_data["is_keyresult"] is False
        assert response_data["is_mandatory_keyresult"] is True
        assert response_data["ca_config_type"] == "numeric"

    @pytest.mark.integration
    async def test_numeric_field_with_non_manage(
        self, db_session, request_with_real_edit_jwt, patch_adapter
    ):
        """A read from any tenant group id will always create the default fields."""
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_edit_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"

        (
            response_data,
            response_status,
        ) = await actions.insert_custom_attributes_configuration(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "numeric",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.FORBIDDEN
        errors = json.loads(response_data["message"])
        assert errors[0]["error_code"] == "NOT_MANAGE_ROLE"


class TestCustomAttrConfigUpdate:
    """Ensure when we update configurations, we get the right data."""

    @pytest.mark.integration
    async def test_field_update_default(
        self, db_session, request_with_real_pvadmin_settings_jwt
    ):
        """Update a default field."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"
        config_id = response_data[0]["id"]

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "id": config_id,
                    "tooltip": "Type of OKR Tooltip",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert response_data
        assert response_data["label"] == "Type of OKR"
        assert response_data["is_objective"] is True
        assert response_data["is_keyresult"] is False
        assert response_data["is_mandatory_keyresult"] is True

    @pytest.mark.integration
    async def test_field_cannot_update_default_label(
        self, db_session, request_with_real_pvadmin_settings_jwt
    ):
        """Cannot update label or tooltip for default fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"
        config_id = response_data[0]["id"]

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "label": "Hahaha"},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert response_data
        assert response_data["label"] != "Hahaha"
        assert response_data["label"] == "Type of OKR"

    @pytest.mark.integration
    async def test_field_cannot_update_default_tooltip(
        self, db_session, request_with_real_pvadmin_settings_jwt
    ):
        """Cannot update label or tooltip for default fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert len(response_data) == 2
        assert response_data[0]["label"] == "Type of OKR"
        assert response_data[1]["label"] == "Status"
        config_id = response_data[0]["id"]

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "tooltip": "Hahaha"},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert response_data
        assert response_data["tooltip"] == "Hahaha"
        assert response_data["tooltip"] != "Defines the goal nature of your OKR"

    @pytest.fixture
    async def preset_columns(self, db_session, request_with_real_pvadmin_settings_jwt):
        """A fixture to create default set of fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "text",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple date field",
                    "ca_config_type": "date",
                    "tooltip": "A very simple date field",
                    "is_objective": False,
                    "is_keyresult": True,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple multiselect field",
                    "ca_config_type": "multiselect",
                    "tooltip": "A very simple multiselect field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                    "value": [
                        dict(value="Ini"),
                        dict(value="Mini"),
                        dict(value="Myni"),
                        dict(value="Mo"),
                    ],
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        response_data, _ = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )

        return response_data

    @pytest.mark.integration
    async def test_field_update_fields(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Can update label and tooltip for non default fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "id": preset_columns[2]["id"],
                    "label": "Text field label changed",
                    "tooltip": "Text field tooltip changed",
                },
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )
        assert response_status == HTTPStatus.OK
        assert response_data
        assert response_data["label"] == "Text field label changed"
        assert response_data["tooltip"] == "Text field tooltip changed"

    @pytest.mark.integration
    async def test_field_cannot_update_type(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Cannot update ca_config_type."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "id": preset_columns[2]["id"],
                    "ca_config_type": "multiselect",
                },
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )
        assert response_data["ca_config_type"] != "multiselect"  # did not update it

    @pytest.mark.integration
    async def test_field_update_multiselect(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Update multiselect adds proper ids to options."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        config_id = None
        options = None

        for config in preset_columns:
            if config["ca_config_type"] == "multiselect":
                config_id = config["id"]
                options = config["value"]
                break

        options.append(dict(value="Mu"))

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "value": options},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert len(response_data["value"]) == 5
        ids = [opt["id"] for opt in response_data["value"]]
        assert len(ids) == 5

    @pytest.mark.integration
    async def test_field_update_multiselect_update_existing_option(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Update multiselect adds proper ids to options."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        config_id = None
        options = None

        for config in preset_columns:
            if config["ca_config_type"] == "multiselect":
                config_id = config["id"]
                options = config["value"]
                break

        options[0]["value"] = "Updated Ini"

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "value": options},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert len(response_data["value"]) == 4
        assert response_data["value"][0]["value"] == "Updated Ini"

    @pytest.mark.integration
    async def test_field_update_multiselect_remove_option(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Update multiselect can remove option."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        config_id = None
        options = None

        for config in preset_columns:
            if config["ca_config_type"] == "multiselect":
                config_id = config["id"]
                options = config["value"]
                break

        new_options = options[0:-1]

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "value": new_options},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert len(response_data["value"]) == 3
        assert response_data["value"][0]["value"] == "Ini"

    @pytest.mark.integration
    async def test_field_update_multiselect_cannot_have_zero_options(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Cannot set zero number of options."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        config_id = None
        options = []

        for config in preset_columns:
            if config["ca_config_type"] == "multiselect":
                config_id = config["id"]
                break

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "value": options},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_field_update_multiselect_only_unique_options(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Only unique options are allowed."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        config_id = None
        options = []

        for config in preset_columns:
            if config["ca_config_type"] == "multiselect":
                config_id = config["id"]
                options = config["value"]
                break

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "value": options + [dict(value="Ini")]},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST
        error = json.loads(response_data["message"])
        assert "DUPLICATE" in error[0]["error_code"]

    @pytest.mark.integration
    async def test_field_update_cannot_archive_default(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Trying to archive a default has no effect."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": preset_columns[0]["id"], "is_archived": True},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_archived"] is False

    @pytest.mark.integration
    async def test_field_update_archive_of_non_default_fields(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Trying to archive a non-default works."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": preset_columns[2]["id"], "is_archived": True},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_archived"] is True

    @pytest.mark.integration
    async def test_field_update_unarchive_of_non_default_fields(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns
    ):
        """Trying to un-archive a non-default works."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": preset_columns[2]["id"], "is_archived": True},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_archived"] is True
        config_id = response_data["id"]

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "is_archived": False},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_archived"] is False

    @pytest.mark.integration
    async def test_field_update_cannot_archive_when_max(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns, mocker
    ):
        """Trying to unarchive when we have max active fields will not work."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": preset_columns[2]["id"], "is_archived": True},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_archived"] is True
        config_id = response_data["id"]

        # Set max active field count 4 for the test
        mocker.patch(
            "okrs_api.api.controller.actions.MAX_ACTIVE_CA_FIELD",
            4,
        )

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id, "is_archived": False},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST
        errors = json.loads(response_data["message"])
        assert errors[0]["error_code"] == "MAX_CUSTOM_CONFIGS_REACHED"


class TestCustomAttrConfigDelete:
    """Ensure when we delete configurations, we get the right data in DB."""

    @pytest.fixture
    async def preset_columns(self, db_session, request_with_real_pvadmin_settings_jwt):
        """A fixture to create default set of fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "text",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple date field",
                    "ca_config_type": "date",
                    "tooltip": "A very simple date field",
                    "is_objective": False,
                    "is_keyresult": True,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple multiselect field",
                    "ca_config_type": "multiselect",
                    "tooltip": "A very simple multiselect field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                    "value": [
                        dict(value="Ini"),
                        dict(value="Mini"),
                        dict(value="Myni"),
                        dict(value="Mo"),
                    ],
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        response_data, _ = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )

        return response_data

    @pytest.mark.integration
    async def test_delete_field_with_non_manage(
        self, db_session, request_with_real_edit_jwt, preset_columns
    ):
        """Cannot delete with non manage role."""
        request_with_real_edit_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.delete_custom_attributes_configuration(
            request=request_with_real_edit_jwt,
            body={
                "input": {"id": preset_columns[0]["id"]},
                "action": {"name": "delete_attributes_configuration"},
            },
        )
        assert response_status == HTTPStatus.FORBIDDEN

    @pytest.mark.integration
    async def test_field_delete_cannot_delete_active_field(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns, mocker
    ):
        """Trying to delete active fields will not work."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.delete_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": preset_columns[2]["id"]},
                "action": {"name": "delete_custom_attributes_configuration"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST
        errors = json.loads(response_data["message"])
        assert errors[0]["error_code"] == "CANNOT_DELETE_UNARCHIVED_CONFIG"

    @pytest.mark.integration
    async def test_field_delete_can_delete_archived_field(
        self, db_session, request_with_real_pvadmin_settings_jwt, preset_columns, mocker
    ):
        """Trying to delete archived fields will work."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        (
            response_data,
            response_status,
        ) = await actions.update_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": preset_columns[2]["id"], "is_archived": True},
                "action": {"name": "update_custom_attributes_configurations"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_archived"] is True
        config_id = response_data["id"]

        (
            response_data,
            response_status,
        ) = await actions.delete_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"id": config_id},
                "action": {"name": "delete_custom_attributes_configuration"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data["is_deleted"] is True


class TestCustomAttributesValues:
    """Ensure when we associate a custom field value to objective or key result, we get back right data."""

    @pytest.fixture
    async def preset_column_configs(
        self, db_session, request_with_real_pvadmin_settings_jwt
    ):
        """A fixture to create default set of fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "text",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple date field",
                    "ca_config_type": "date",
                    "tooltip": "A very simple date field",
                    "is_objective": False,
                    "is_keyresult": True,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple multiselect field",
                    "ca_config_type": "multiselect",
                    "tooltip": "A very simple multiselect field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                    "value": [
                        dict(value="Ini"),
                        dict(value="Mini"),
                        dict(value="Myni"),
                        dict(value="Mo"),
                    ],
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        response_data, _ = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )

        return response_data

    @pytest.mark.integration
    async def test_getting_values(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):

        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        wic_role = work_item_container_role_factory(
            okr_role="read", created_by="13128f97-d58a-4ab5-90b5-5c9697aaf417"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        text_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        value_text = models.CustomAttributesValue(
            object_id=obj.id,
            ca_config_id=text_config["id"],
            object_type="objective",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value="hello world",
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": obj.id, "object_type": "objective"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert len(response_data) == 1
        assert response_data[0]["value"] == "hello world"

    @pytest.mark.integration
    async def test_getting_values_boolen(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):

        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        wic_role = work_item_container_role_factory(
            okr_role="read", created_by="13128f97-d58a-4ab5-90b5-5c9697aaf417"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        text_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        value_text = models.CustomAttributesValue(
            object_id=obj.id,
            ca_config_id=text_config["id"],
            object_type="objective",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value="true",
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": obj.id, "object_type": "objective"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert len(response_data) == 1
        assert response_data[0]["value"] == "true"

    @pytest.mark.integration
    async def test_getting_values_kr(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        key_result_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        wic_role = work_item_container_role_factory(
            okr_role="edit", created_by="13128f97-d58a-4ab5-90b5-5c9697aaf417"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        kr.objective_id = obj.id
        db_session.commit()
        current_config = None
        kr_id = kr.id
        for config in preset_column_configs:
            if config["ca_config_type"] == "singleselect":
                current_config = config

        value_text = models.CustomAttributesValue(
            object_id=kr_id,
            ca_config_id=current_config["id"],
            object_type="keyresult",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value=json.dumps(dict(id=current_config["value"][0]["id"])),
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": kr_id, "object_type": "keyresult"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert len(response_data) == 0

    @pytest.mark.integration
    async def test_getting_values_obj_none_role(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):

        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        wic_role = work_item_container_role_factory(
            okr_role="none", created_by="13128f97-d58a-4ab5-90b5-5c9697aaf417"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        text_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        value_text = models.CustomAttributesValue(
            object_id=obj.id,
            ca_config_id=text_config["id"],
            object_type="objective",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value="hello world",
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": obj.id, "object_type": "objective"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.UNAUTHORIZED

    @pytest.mark.integration
    async def test_getting_values_kr_no_role_in_db(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        key_result_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        kr.objective_id = obj.id
        db_session.commit()
        current_config = None
        kr_id = kr.id
        for config in preset_column_configs:
            if config["ca_config_type"] == "singleselect":
                current_config = config

        value_text = models.CustomAttributesValue(
            object_id=kr_id,
            ca_config_id=current_config["id"],
            object_type="keyresult",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value=json.dumps(dict(id=current_config["value"][0]["id"])),
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": kr_id, "object_type": "keyresult"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.UNAUTHORIZED

    @pytest.mark.integration
    async def test_getting_values_objective_deleted(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        key_result_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        db_session.commit()

        obj.soft_delete()
        db_session.commit()

        current_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "singleselect":
                current_config = config

        value_text = models.CustomAttributesValue(
            object_id=obj.id,
            ca_config_id=current_config["id"],
            object_type="keyresult",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value=json.dumps(dict(id=current_config["value"][0]["id"])),
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": obj.id, "object_type": "keyresult"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.UNAUTHORIZED

    @pytest.mark.integration
    async def test_getting_values_kr_deleted(
        self,
        db_session,
        preset_column_configs,
        request_with_real_pvadmin_settings_jwt,
        objective_factory,
        key_result_factory,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        db_session.commit()
        obj = objective_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory(
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        )
        kr.objective_id = obj.id
        db_session.commit()

        kr.soft_delete()
        db_session.commit()

        current_config = None
        kr_id = kr.id
        for config in preset_column_configs:
            if config["ca_config_type"] == "singleselect":
                current_config = config

        value_text = models.CustomAttributesValue(
            object_id=kr_id,
            ca_config_id=current_config["id"],
            object_type="keyresult",
            tenant_group_id_str="7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb",
            value=json.dumps(dict(id=current_config["value"][0]["id"])),
        )

        db_session.add(value_text)
        db_session.commit()

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"object_id": kr_id, "object_type": "keyresult"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.UNAUTHORIZED


class TestObjectiveActions:
    """Ensure insert and update actions work correctly on the objectives."""

    @pytest.mark.integration
    async def test_objective_insert_without_valid_wic(
        self, db_session, request_with_real_edit_jwt
    ):
        """Insert action without a proper WIC id should fail."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": "1234",
                    "external_type": "leankit",
                    "external_title": "Test",
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_without_valid_wic_role(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
    ):
        """Insert action with a proper WIC but without a role should fail."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_without_none_wic_role(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Insert action with a proper WIC but without a role should fail."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="none", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.parametrize(
        "starts_at",
        ["2023-08-0144T00:00:00+00:00", "2023-08-29T00:00:00+00:00"],
    )
    @pytest.mark.integration
    async def test_objective_insert_with_invalid_date(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        starts_at,
    ):
        """Insert action without a proper WIC id should fail."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 112",
                    "level_depth": 3,
                    "starts_at": starts_at,
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.fixture
    async def preset_column_configs(
        self, db_session, request_with_real_pvadmin_settings_jwt_p
    ):
        """A fixture to create default set of fields."""
        request_with_real_pvadmin_settings_jwt_p.app["db_session"] = db_session

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt_p,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "text",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt_p,
            body={
                "input": {
                    "label": "Simple numeric field",
                    "ca_config_type": "numeric",
                    "tooltip": "A very simple numeric field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt_p,
            body={
                "input": {
                    "label": "Simple date field",
                    "ca_config_type": "date",
                    "tooltip": "A very simple date field",
                    "is_objective": False,
                    "is_keyresult": True,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt_p,
            body={
                "input": {
                    "label": "Simple multiselect field",
                    "ca_config_type": "multiselect",
                    "tooltip": "A very simple multiselect field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                    "value": [
                        dict(value="Ini"),
                        dict(value="Mini"),
                        dict(value="Myni"),
                        dict(value="Mo"),
                    ],
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        response_data, _ = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt_p,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )

        return response_data

    @pytest.mark.integration
    async def test_objective_insert_with_ok_role(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Insert action with a proper WIC and WIC role should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 112",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data

        obj = db_session.query(models.Objective).get(response_data["id"])
        assert obj.name == "Obj 112"
        assert obj.starts_at

    @pytest.mark.integration
    async def test_objective_insert_with_cf_values(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data

        obj = db_session.query(models.Objective).get(response_data["id"])
        assert obj.name == "Obj 113"
        assert obj.starts_at

        response_data, response_status = await actions.custom_attributes(
            request=request_with_real_edit_jwt,
            body={
                "input": {"object_id": obj.id, "object_type": "objective"},
                "action": {"name": "custom_attributes"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert len(response_data) == 1
        assert response_data[0]["value"] == "Hello world"

    @pytest.mark.integration
    async def test_objective_insert_with_invalid_ca_config_id(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Cannot insert a CA value if the config ID is invalid."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({102323: "Hello world"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_text_invalid(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps(
                        {text_config["id"]: "X" * (MAX_TEXT_LENGTH + 1)}
                    ),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_text_valid(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "X" * 30}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_invalid_1(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "abcd&&*1222"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_invalid_2(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: ""}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_invalid_3(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: {"abc": 123}}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_valid_1(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "30.89"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_valid_2(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: 0}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_valid_3(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "0"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_valid_4(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: 0.01221}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_numeric_valid_5(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "numeric":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: 123}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_text_valid_2(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "Neo"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_date_valid_1(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "date":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "2023-01-01"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_date_valid_2(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "date":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "2023-01-01"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_objective_insert_with_invalid_external_id_and_type(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "date":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": "123",
                    "external_type": "lleenkit",
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "2023-13-01"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_date_invalid_1(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "date":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: "2023-13-01"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_insert_with_date_invalid_2(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        ca_config = None
        for config in preset_column_configs:
            if config["ca_config_type"] == "date":
                ca_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-0144T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({ca_config["id"]: ""}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_update_with_cf_values_invlid_objective_id(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data
        obj = db_session.query(models.Objective).get(response_data["id"])
        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "id": obj.id + 1,
                    "name": "Obj 114",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "update_objective"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_update_with_invalid_date(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data
        obj = db_session.query(models.Objective).get(response_data["id"])
        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "id": obj.id,
                    "name": "Obj 114",
                    "level_depth": 3,
                    "starts_at": "2023-08-01",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "update_objective"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_objective_update_with_cf_values(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        preset_column_configs,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        request_with_real_edit_jwt_2.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.commit()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="edit",
            created_by="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_created_by="10135757550",
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        wic_role2 = work_item_container_role_factory(
            okr_role="edit",
            created_by="35b4fbf6-5b65-4e69-9a46-2c281e944d3b",
            app_created_by="10135757568",
        )
        wic_role2.work_item_container_id = wic.id
        db_session.commit()

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 113",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "last_updated_by": "13128f97-d58a-4ab5-90b5-5c9697aaf417",
                    "app_last_updated_by": "12121323",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data
        obj_id = response_data.get("id")
        obj = db_session.query(models.Objective).get(obj_id)

        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt_2,
            body={
                "input": {
                    "id": obj.id,
                    "name": "Obj 114",
                    "description": "desc",
                    "level_depth": 3,
                    "app_owned_by": "10135757538",
                    "owned_by": "00189ed3-7de6-4b35-b13f-e9e313a247f6",
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello worlds"}),
                },
                "action": {"name": "update_objective"},
            },
        )
        obj_id = response_data.get("id")
        obj = db_session.query(models.Objective).get(obj_id)
        assert obj.name == "Obj 114"
        assert obj.last_updated_by == "35b4fbf6-5b65-4e69-9a46-2c281e944d3b"
        assert obj.app_last_updated_by == "10135757568"
        assert obj.app_created_by == "10135757550"
        assert obj.created_by == "1e8c7640-1ed9-437d-a981-7e64f405136f"
        ca_values = (
            db_session.query(models.CustomAttributesValue)
            .filter_by(object_id=obj_id)
            .filter_by(deleted_at_epoch=0)
            .all()
        )
        assert ca_values[0].last_updated_by == "35b4fbf6-5b65-4e69-9a46-2c281e944d3b"
        assert ca_values[0].app_last_updated_by == "10135757568"
        assert ca_values[0].created_by == "1e8c7640-1ed9-437d-a981-7e64f405136f"

    date_range_test_data = [
        (
            "2023-08-01T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-02T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-02T00:00:00+00:00",
            "2023-08-31T00:00:00+00:00",
            "2023-08-02T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-01T00:00:00+00:00",
            "2023-08-31T00:00:00+00:00",
            "2023-08-02T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-04T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-02T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
            "2023-08-02T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-05T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-05T00:00:00+00:00",
            "2023-08-30T00:00:00+00:00",
            "2023-08-05T00:00:00+00:00",
            "2023-08-27T00:00:00+00:00",
        ),
        (
            "2023-08-02T00:00:00+00:00",
            "2023-08-26T00:00:00+00:00",
            "2023-08-02T00:00:00+00:00",
            "2023-08-26T00:00:00+00:00",
            "2023-08-04T00:00:00+00:00",
            "2023-08-26T00:00:00+00:00",
        ),
        (
            "2023-08-05T00:00:00+00:00",
            "2023-08-26T00:00:00+00:00",
            "2023-08-05T00:00:00+00:00",
            "2023-08-26T00:00:00+00:00",
            "2023-08-05T00:00:00+00:00",
            "2023-08-26T00:00:00+00:00",
        ),
        (
            "2023-07-01T00:00:00+00:00",
            "2023-07-05T00:00:00+00:00",
            "2023-07-01T00:00:00+00:00",
            "2023-07-05T00:00:00+00:00",
            "2023-07-01T00:00:00+00:00",
            "2023-07-05T00:00:00+00:00",
        ),
        (
            "2023-09-25T00:00:00+00:00",
            "2023-09-27T00:00:00+00:00",
            "2023-09-25T00:00:00+00:00",
            "2023-09-27T00:00:00+00:00",
            "2023-09-25T00:00:00+00:00",
            "2023-09-27T00:00:00+00:00",
        ),
    ]

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "starts_at, ends_at, kr1_starts_at, kr1_ends_at, kr2_starts_at, kr2_ends_at",
        date_range_test_data,
    )
    async def test_objective_date_range_update(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        objective_factory,
        key_result_factory,
        work_item_container_role_factory,
        starts_at,
        ends_at,
        kr1_starts_at,
        kr1_ends_at,
        kr2_starts_at,
        kr2_ends_at,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        objective = objective_factory(
            starts_at="2023-08-02T00:00:00+00:00", ends_at="2023-08-30T00:00:00+00:00"
        )
        kr1 = key_result_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            objective=objective,
        )
        kr2 = key_result_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            objective=objective,
        )
        db_session.commit()
        objective_id = objective.id
        wic = objective.work_item_container

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "id": objective.id,
                    "name": objective.name,
                    "level_depth": objective.level_depth,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                },
                "action": {"name": "update_objective"},
            },
        )
        assert response_status == HTTPStatus.OK
        key_results = (
            db_session.query(models.KeyResult)
            .filter_by(objective_id=objective_id, deleted_at_epoch=0)
            .order_by(models.KeyResult.id)
            .all()
        )
        assert len(key_results) == 2
        objective_obj = key_results[0].objective
        assert objective_obj.starts_at == datetime.fromisoformat(starts_at)
        assert objective_obj.ends_at == datetime.fromisoformat(ends_at)
        assert key_results[0].starts_at == datetime.fromisoformat(kr1_starts_at)
        assert key_results[0].ends_at == datetime.fromisoformat(kr1_ends_at)
        assert key_results[1].starts_at == datetime.fromisoformat(kr2_starts_at)
        assert key_results[1].ends_at == datetime.fromisoformat(kr2_ends_at)

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "starts_at, ends_at, kr1_starts_at, kr1_ends_at, kr2_starts_at, kr2_ends_at",
        date_range_test_data,
    )
    async def test_objective_date_range_update_with_single_target(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        objective_factory,
        key_result_factory,
        target_factory,
        work_item_container_role_factory,
        starts_at,
        ends_at,
        kr1_starts_at,
        kr1_ends_at,
        kr2_starts_at,
        kr2_ends_at,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        objective = objective_factory(
            starts_at="2023-08-02T00:00:00+00:00", ends_at="2023-08-30T00:00:00+00:00"
        )
        kr1 = key_result_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            objective=objective,
        )
        kr2 = key_result_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            objective=objective,
        )
        t1 = target_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            key_result=kr1,
        )
        t2 = target_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            key_result=kr2,
        )
        db_session.commit()
        objective_id = objective.id
        wic = objective.work_item_container

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "id": objective.id,
                    "name": objective.name,
                    "level_depth": objective.level_depth,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                },
                "action": {"name": "update_objective"},
            },
        )
        assert response_status == HTTPStatus.OK

        key_result_targets = (
            db_session.query(models.KeyResult, models.Target)
            .outerjoin(
                models.Target,
                (models.KeyResult.id == models.Target.key_result_id)
                & (models.Target.is_deleted == False),
            )
            .filter(models.KeyResult.objective_id == objective_id)
            .filter(models.KeyResult.deleted_at_epoch == 0)
            .order_by(models.KeyResult.id)
            .all()
        )
        assert len(key_result_targets) == 2
        objective_obj = key_result_targets[0][0].objective
        assert objective_obj.starts_at == datetime.fromisoformat(starts_at)
        assert objective_obj.ends_at == datetime.fromisoformat(ends_at)
        assert key_result_targets[0][0].starts_at == datetime.fromisoformat(
            kr1_starts_at
        )
        assert key_result_targets[0][1].starts_at == datetime.fromisoformat(
            kr1_starts_at
        )
        assert key_result_targets[0][0].ends_at == datetime.fromisoformat(kr1_ends_at)
        assert key_result_targets[0][1].ends_at == datetime.fromisoformat(kr1_ends_at)
        assert key_result_targets[1][0].starts_at == datetime.fromisoformat(
            kr2_starts_at
        )
        assert key_result_targets[1][1].starts_at == datetime.fromisoformat(
            kr2_starts_at
        )
        assert key_result_targets[1][0].ends_at == datetime.fromisoformat(kr2_ends_at)
        assert key_result_targets[1][1].ends_at == datetime.fromisoformat(kr2_ends_at)

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "starts_at, ends_at, kr1_starts_at, kr1_ends_at, kr2_starts_at, kr2_ends_at",
        date_range_test_data,
    )
    async def test_objective_date_range_update_with_multi_targets(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        objective_factory,
        key_result_factory,
        target_factory,
        work_item_container_role_factory,
        starts_at,
        ends_at,
        kr1_starts_at,
        kr1_ends_at,
        kr2_starts_at,
        kr2_ends_at,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        objective = objective_factory(
            starts_at="2023-08-02T00:00:00+00:00", ends_at="2023-08-30T00:00:00+00:00"
        )
        kr1 = key_result_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            objective=objective,
        )
        kr2 = key_result_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            objective=objective,
        )
        t11 = target_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-16T00:00:00+00:00",
            key_result=kr1,
        )
        t12 = target_factory(
            starts_at="2023-08-17T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            key_result=kr1,
        )
        t21 = target_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-19T00:00:00+00:00",
            key_result=kr2,
        )
        t22 = target_factory(
            starts_at="2023-08-20T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            key_result=kr2,
        )
        db_session.commit()
        objective_id = objective.id
        wic = objective.work_item_container

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "id": objective.id,
                    "name": objective.name,
                    "level_depth": objective.level_depth,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                },
                "action": {"name": "update_objective"},
            },
        )

        if datetime.fromisoformat(starts_at) > datetime.fromisoformat(
            "2023-08-02T00:00:00+00:00"
        ) or datetime.fromisoformat(ends_at) < datetime.fromisoformat(
            "2023-08-30T00:00:00+00:00"
        ):
            assert response_status == HTTPStatus.BAD_REQUEST
        else:
            key_result_targets = (
                db_session.query(models.KeyResult, models.Target)
                .outerjoin(
                    models.Target,
                    (models.KeyResult.id == models.Target.key_result_id)
                    & (models.Target.is_deleted == False),
                )
                .filter(models.KeyResult.objective_id == objective_id)
                .filter(models.KeyResult.deleted_at_epoch == 0)
                .order_by(models.KeyResult.id)
                .all()
            )
            assert len(key_result_targets) == 4
            objective_obj = key_result_targets[0][0].objective
            assert objective_obj.starts_at == datetime.fromisoformat(starts_at)
            assert objective_obj.ends_at == datetime.fromisoformat(ends_at)
            assert key_result_targets[0][0].starts_at == datetime.fromisoformat(
                "2023-08-02T00:00:00+00:00"
            )
            assert key_result_targets[0][1].starts_at == datetime.fromisoformat(
                "2023-08-02T00:00:00+00:00"
            )
            assert key_result_targets[0][0].ends_at == datetime.fromisoformat(
                "2023-08-30T00:00:00+00:00"
            )
            assert key_result_targets[0][1].ends_at == datetime.fromisoformat(
                "2023-08-16T00:00:00+00:00"
            )
            assert key_result_targets[2][0].starts_at == datetime.fromisoformat(
                "2023-08-04T00:00:00+00:00"
            )
            assert key_result_targets[2][1].starts_at == datetime.fromisoformat(
                "2023-08-04T00:00:00+00:00"
            )
            assert key_result_targets[2][0].ends_at == datetime.fromisoformat(
                "2023-08-27T00:00:00+00:00"
            )
            assert key_result_targets[2][1].ends_at == datetime.fromisoformat(
                "2023-08-19T00:00:00+00:00"
            )

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "starts_at, ends_at, kr1_starts_at, kr1_ends_at, kr2_starts_at, kr2_ends_at",
        date_range_test_data,
    )
    async def test_objective_date_range_update_with_mixed_multi_targets(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        objective_factory,
        key_result_factory,
        target_factory,
        work_item_container_role_factory,
        starts_at,
        ends_at,
        kr1_starts_at,
        kr1_ends_at,
        kr2_starts_at,
        kr2_ends_at,
    ):
        """Insert action with a proper WIC and WIC role and CA data should be OK."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        objective = objective_factory(
            starts_at="2023-08-02T00:00:00+00:00", ends_at="2023-08-30T00:00:00+00:00"
        )
        kr1 = key_result_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            objective=objective,
        )
        kr2 = key_result_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            objective=objective,
        )
        t11 = target_factory(
            starts_at="2023-08-02T00:00:00+00:00",
            ends_at="2023-08-16T00:00:00+00:00",
            key_result=kr1,
        )
        t12 = target_factory(
            starts_at="2023-08-17T00:00:00+00:00",
            ends_at="2023-08-30T00:00:00+00:00",
            key_result=kr1,
        )
        t21 = target_factory(
            starts_at="2023-08-04T00:00:00+00:00",
            ends_at="2023-08-27T00:00:00+00:00",
            key_result=kr2,
        )
        db_session.commit()
        objective_id = objective.id
        wic = objective.work_item_container

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.update_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "id": objective.id,
                    "name": objective.name,
                    "level_depth": objective.level_depth,
                    "starts_at": starts_at,
                    "ends_at": ends_at,
                },
                "action": {"name": "update_objective"},
            },
        )

        if datetime.fromisoformat(starts_at) > datetime.fromisoformat(
            "2023-08-02T00:00:00+00:00"
        ) or datetime.fromisoformat(ends_at) < datetime.fromisoformat(
            "2023-08-30T00:00:00+00:00"
        ):
            assert response_status == HTTPStatus.BAD_REQUEST
        else:
            key_result_targets = (
                db_session.query(models.KeyResult, models.Target)
                .outerjoin(
                    models.Target,
                    (models.KeyResult.id == models.Target.key_result_id)
                    & (models.Target.is_deleted == False),
                )
                .filter(models.KeyResult.objective_id == objective_id)
                .filter(models.KeyResult.deleted_at_epoch == 0)
                .order_by(models.KeyResult.id)
                .all()
            )
            assert len(key_result_targets) == 3
            objective_obj = key_result_targets[0][0].objective
            assert objective_obj.starts_at == datetime.fromisoformat(starts_at)
            assert objective_obj.ends_at == datetime.fromisoformat(ends_at)
            assert key_result_targets[0][0].starts_at == datetime.fromisoformat(
                "2023-08-02T00:00:00+00:00"
            )
            assert key_result_targets[0][1].starts_at == datetime.fromisoformat(
                "2023-08-02T00:00:00+00:00"
            )
            assert key_result_targets[0][0].ends_at == datetime.fromisoformat(
                "2023-08-30T00:00:00+00:00"
            )
            assert key_result_targets[0][1].ends_at == datetime.fromisoformat(
                "2023-08-16T00:00:00+00:00"
            )
            assert key_result_targets[2][0].starts_at == datetime.fromisoformat(
                "2023-08-04T00:00:00+00:00"
            )
            assert key_result_targets[2][1].starts_at == datetime.fromisoformat(
                "2023-08-04T00:00:00+00:00"
            )
            assert key_result_targets[2][0].ends_at == datetime.fromisoformat(
                "2023-08-27T00:00:00+00:00"
            )
            assert key_result_targets[2][1].ends_at == datetime.fromisoformat(
                "2023-08-27T00:00:00+00:00"
            )


class TestKeyResultActions:
    """Test key result insert or delete."""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "target_value",
        [0, 86, -98],
    )
    async def test_key_result_insert(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        target_value,
    ):
        """Test an insert of key result"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        starts_at_str = "2023-08-01T00:00:00+00:00"
        ends_at_str = "2023-08-28T00:00:00+00:00"

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )

        obj_id = response_data.get("id")

        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": target_value,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        kr = db_session.query(models.KeyResult).get(kr_id)
        assert kr.name == "Test KR"
        assert kr.description == "Test KR Description"
        assert kr.starting_value == 23
        assert kr.target_value == target_value
        assert kr.data_source == "Somewhere"
        assert kr.value_type == "constant"
        assert kr.starts_at
        assert kr.ends_at
        targets = (
            db_session.query(models.Target)
            .filter_by(key_result_id=kr_id, is_deleted=False)
            .all()
        )
        assert len(targets) == 1
        assert targets[0].starts_at == datetime.fromisoformat(starts_at_str)
        assert targets[0].ends_at == datetime.fromisoformat(ends_at_str)
        assert targets[0].value == target_value

    @pytest.mark.integration
    async def test_key_result_insert_with_invalid_date(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Test an insert of key result"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        starts_at_str = "2023-08-01T00:00:00+00:00"
        ends_at_str = "2023-08-28T00:00:00+00:00"

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )

        obj_id = response_data.get("id")

        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": "2023-08-011",
                    "ends_at": ends_at_str,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_key_result_update(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Test an insert of key result"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        request_with_real_edit_jwt_2.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.commit()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        starts_at_str = "2023-08-01T00:00:00+00:00"
        ends_at_str = "2023-08-28T00:00:00+00:00"
        updated_starts_at_str = "2023-08-03T00:00:00+00:00"
        updated_ends_at_str = "2023-08-22T00:00:00+00:00"

        wic_role = work_item_container_role_factory(
            okr_role="edit",
            created_by="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_created_by="10135757550",
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        wic_role2 = work_item_container_role_factory(
            okr_role="edit",
            created_by="35b4fbf6-5b65-4e69-9a46-2c281e944d3b",
            app_created_by="10135757568",
        )
        wic_role2.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )

        obj_id = response_data.get("id")

        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        response_data, response_status = await actions.update_keyresult(
            request=request_with_real_edit_jwt_2,
            body={
                "input": {
                    "id": kr_id,
                    "objective_id": obj_id,
                    "starts_at": updated_starts_at_str,
                    "ends_at": updated_ends_at_str,
                    "name": "Test KR 2",
                    "description": "Test KR Description 2",
                    "data_source": "Somewhere 2",
                    "starting_value": 0,
                    "target_value": 200,
                    "app_owned_by": "232343434",
                    "owned_by": "uuid1212121",
                    "value_type": "constantine",
                },
                "action": {"name": "update_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        kr = db_session.query(models.KeyResult).get(kr_id)
        assert kr.name == "Test KR 2"
        assert kr.description == "Test KR Description 2"
        assert kr.starting_value == 0
        assert kr.target_value == 200
        assert kr.data_source == "Somewhere 2"
        assert kr.value_type == "constantine"
        assert kr.starts_at == datetime.fromisoformat(updated_starts_at_str)
        assert kr.ends_at == datetime.fromisoformat(updated_ends_at_str)
        assert kr.app_owned_by == "232343434"
        assert kr.owned_by == "uuid1212121"
        assert kr.last_updated_by == "35b4fbf6-5b65-4e69-9a46-2c281e944d3b"
        assert kr.app_last_updated_by == "10135757568"
        assert kr.app_created_by == "10135757550"
        assert kr.created_by == "1e8c7640-1ed9-437d-a981-7e64f405136f"

        targets = (
            db_session.query(models.Target)
            .filter_by(key_result_id=kr_id, is_deleted=False)
            .all()
        )
        assert len(targets) == 1
        assert targets[0].starts_at == datetime.fromisoformat(updated_starts_at_str)
        assert targets[0].ends_at == datetime.fromisoformat(updated_ends_at_str)
        assert targets[0].value == 200

    @pytest.mark.integration
    async def test_key_result_update_with_invalid_date(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Test an insert of key result"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        request_with_real_edit_jwt_2.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.commit()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        starts_at_str = "2023-08-01T00:00:00+00:00"
        ends_at_str = "2023-08-28T00:00:00+00:00"

        wic_role = work_item_container_role_factory(
            okr_role="edit",
            created_by="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_created_by="10135757550",
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        wic_role2 = work_item_container_role_factory(
            okr_role="edit",
            created_by="35b4fbf6-5b65-4e69-9a46-2c281e944d3b",
            app_created_by="10135757568",
        )
        wic_role2.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )

        obj_id = response_data.get("id")

        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        response_data, response_status = await actions.update_keyresult(
            request=request_with_real_edit_jwt_2,
            body={
                "input": {
                    "id": kr_id,
                    "objective_id": obj_id,
                    "starts_at": "2023-08-011",
                    "ends_at": ends_at_str,
                    "name": "Test KR 2",
                    "description": "Test KR Description 2",
                    "data_source": "Somewhere 2",
                    "starting_value": 0,
                    "target_value": 200,
                    "app_owned_by": "232343434",
                    "owned_by": "uuid1212121",
                    "value_type": "constantine",
                },
                "action": {"name": "update_keyresult"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "input_targets",
        [
            [
                {
                    "starts_at": "2024-07-17T00:00:00+00:00",
                    "ends_at": "2024-07-21T00:00:00+00:00",
                    "value": 7,
                },
            ],
            [
                {
                    "starts_at": "2024-07-19T00:00:00+00:00",
                    "ends_at": "2024-07-21T00:00:00+00:00",
                    "value": 11,
                },
                {
                    "starts_at": "2024-07-22T00:00:00+00:00",
                    "ends_at": "2024-07-26T00:00:00+00:00",
                    "value": 94,
                },
            ],
        ],
    )
    async def test_key_result_targets_insert(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        input_targets,
    ):
        """Ensure that the ProgressPoint is created and progress percentages are calculated correctly"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        starts_at_str = "2024-07-15T00:00:00+00:00"
        ends_at_str = "2024-07-27T00:00:00+00:00"
        first_target = input_targets[0]
        last_target = input_targets[-1]

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )
        obj_id = response_data.get("id")
        kr_body = {
            "input": {
                "objective_id": obj_id,
                "name": "Test KR",
                "description": "Test KR Description",
                "data_source": "Somewhere",
                "starting_value": 23,
                "value_type": "constant",
                "targets": input_targets,
            },
            "action": {"name": "insert_keyresult"},
        }
        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body=kr_body,
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        kr = db_session.query(models.KeyResult).get(kr_id)
        assert kr.name == "Test KR"
        assert kr.description == "Test KR Description"
        assert kr.starting_value == 23
        assert kr.target_value == last_target["value"]
        assert kr.data_source == "Somewhere"
        assert kr.value_type == "constant"
        assert kr.starts_at == first_target["starts_at"]
        assert kr.ends_at == last_target["ends_at"]
        targets = (
            db_session.query(models.Target)
            .filter_by(key_result_id=kr_id, is_deleted=False)
            .order_by(models.Target.starts_at)
            .all()
        )
        assert len(targets) == len(input_targets)
        for index, target in enumerate(targets):
            assert target.starts_at == input_targets[index]["starts_at"]
            assert target.ends_at == input_targets[index]["ends_at"]
            assert target.value == input_targets[index]["value"]

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "input_targets",
        [
            [
                {
                    "starts_at": "2024-07-14T00:00:00+00:00",
                    "ends_at": "2024-07-21T00:00:00+00:00",
                    "value": 7,
                },
            ],
            [
                {
                    "starts_at": "2024-07-16T00:00:00+00:00",
                    "ends_at": "2024-07-28T00:00:00+00:00",
                    "value": 11,
                },
            ],
            [
                {
                    "starts_at": "2024-07-15T00:00:00+00:00",
                    "ends_at": "2024-07-22T00:00:00+00:00",
                    "value": 7,
                },
                {
                    "starts_at": "2024-07-22T00:00:00+00:00",
                    "ends_at": "2024-07-27T00:00:00+00:00",
                    "value": 11,
                },
            ],
            [
                {
                    "starts_at": "2024-07-15T00:00:00+00:00",
                    "ends_at": "2024-07-22T00:00:00+00:00",
                    "value": 7,
                },
                {
                    "starts_at": "2024-07-24T00:00:00+00:00",
                    "ends_at": "2024-07-27T00:00:00+00:00",
                    "value": 11,
                },
            ],
            [],
            [
                {
                    "starts_at": "2024-07-21T00:00:00+00:00",
                    "ends_at": "2024-07-14T00:00:00+00:00",
                    "value": 7,
                },
            ],
            [
                {
                    "starts_at": "2024-07-14T00:00:00+00:00",
                    "ends_at": "2024-07-21T00:00:00+00:00",
                },
            ],
            [
                {
                    "ends_at": "2024-07-21T00:00:00+00:00",
                    "value": 11,
                },
            ],
        ],
    )
    async def test_invalid_key_result_targets_insert(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        input_targets,
    ):
        """Ensure that the ProgressPoint is created and progress percentages are calculated correctly"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        starts_at_str = "2024-07-15T00:00:00+00:00"
        ends_at_str = "2024-07-27T00:00:00+00:00"

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )
        obj_id = response_data.get("id")
        kr_body = {
            "input": {
                "objective_id": obj_id,
                "name": "Test KR",
                "description": "Test KR Description",
                "data_source": "Somewhere",
                "starting_value": 23,
                "value_type": "constant",
                "targets": input_targets,
            },
            "action": {"name": "insert_keyresult"},
        }
        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body=kr_body,
        )
        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "input_targets",
        [
            [
                {
                    "starts_at": "2024-07-17T00:00:00+00:00",
                    "ends_at": "2024-07-19T00:00:00+00:00",
                    "value": 7,
                },
            ],
            [
                {
                    "starts_at": "2024-07-19T00:00:00+00:00",
                    "ends_at": "2024-07-23T00:00:00+00:00",
                    "value": 11,
                },
                {
                    "starts_at": "2024-07-24T00:00:00+00:00",
                    "ends_at": "2024-07-26T00:00:00+00:00",
                    "value": 93,
                },
            ],
        ],
    )
    async def test_key_result_targets_update(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        input_targets,
    ):
        """Test an insert of key result"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        request_with_real_edit_jwt_2.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.commit()
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        starts_at_str = "2024-07-15T00:00:00+00:00"
        ends_at_str = "2024-07-27T00:00:00+00:00"
        first_target = input_targets[0]
        last_target = input_targets[-1]

        wic_role = work_item_container_role_factory(
            okr_role="edit",
            created_by="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_created_by="10135757550",
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        wic_role2 = work_item_container_role_factory(
            okr_role="edit",
            created_by="35b4fbf6-5b65-4e69-9a46-2c281e944d3b",
            app_created_by="10135757568",
        )
        wic_role2.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": starts_at_str,
                    "ends_at": ends_at_str,
                },
                "action": {"name": "insert_objective"},
            },
        )

        obj_id = response_data.get("id")

        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "targets": [
                        {
                            "starts_at": "2024-07-15T00:00:00+00:00",
                            "ends_at": "2024-07-21T00:00:00+00:00",
                            "value": 13,
                        },
                        {
                            "starts_at": "2024-07-22T00:00:00+00:00",
                            "ends_at": "2024-07-27T00:00:00+00:00",
                            "value": 87,
                        },
                    ],
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        targets = (
            db_session.query(models.Target)
            .filter_by(key_result_id=kr_id, is_deleted=False)
            .order_by(models.Target.starts_at)
            .all()
        )
        assert len(targets) == 2
        assert targets[0].id
        first_target_id = targets[0].id
        input_targets[0]["id"] = first_target_id

        response_data, response_status = await actions.update_keyresult(
            request=request_with_real_edit_jwt_2,
            body={
                "input": {
                    "id": kr_id,
                    "objective_id": obj_id,
                    "name": "Test KR 2",
                    "description": "Test KR Description 2",
                    "data_source": "Somewhere 2",
                    "starting_value": 0,
                    "targets": input_targets,
                    "app_owned_by": "232343434",
                    "owned_by": "uuid1212121",
                    "value_type": "constantine",
                },
                "action": {"name": "update_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        kr = db_session.query(models.KeyResult).get(kr_id)
        assert kr.name == "Test KR 2"
        assert kr.description == "Test KR Description 2"
        assert kr.starting_value == 0
        assert kr.target_value == last_target["value"]
        assert kr.data_source == "Somewhere 2"
        assert kr.value_type == "constantine"
        assert kr.starts_at == first_target["starts_at"]
        assert kr.ends_at == last_target["ends_at"]
        assert kr.app_owned_by == "232343434"
        assert kr.owned_by == "uuid1212121"
        assert kr.last_updated_by == "35b4fbf6-5b65-4e69-9a46-2c281e944d3b"
        assert kr.app_last_updated_by == "10135757568"
        assert kr.app_created_by == "10135757550"
        assert kr.created_by == "1e8c7640-1ed9-437d-a981-7e64f405136f"

        targets = (
            db_session.query(models.Target)
            .filter_by(key_result_id=kr_id, is_deleted=False)
            .order_by(models.Target.starts_at)
            .all()
        )
        assert len(targets) == len(input_targets)
        for index, target in enumerate(targets):
            assert target.starts_at == input_targets[index]["starts_at"]
            assert target.ends_at == input_targets[index]["ends_at"]
            assert target.value == input_targets[index]["value"]

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "first_target_end, second_target_start, target_one_index, target_two_index",
        [
            ("2023-07-06T00:00:00+00:00", "2023-07-07T00:00:00+00:00", 1, 1),
            ("2023-07-28T00:00:00+00:00", "2023-07-29T00:00:00+00:00", 0, 0),
        ],
    )
    async def test_targets_progress_point_mapping_update(
        self,
        db_session,
        setting_factory,
        target_factory,
        progress_point_factory,
        request_with_jwt,
        first_target_end,
        second_target_start,
        target_one_index,
        target_two_index,
    ):
        """Ensure that the ProgressPoint is mapped to correct target id"""
        setting_factory()
        target_one = target_factory()
        target_two = target_factory()
        progress_point_one = progress_point_factory()
        progress_point_two = progress_point_factory()
        db_session.commit()

        objective_start_date = "2023-07-02T00:00:00+00:00"
        objective_end_date = "2023-07-31T00:00:00+00:00"
        objective = target_one.key_result.objective
        objective.starts_at = objective_start_date
        db_session.commit()

        key_result_id = target_one.key_result_id
        target_one.starts_at = objective_start_date
        target_one.ends_at = "2023-07-16T00:00:00+00:00"
        target_two.key_result_id = key_result_id
        target_two.starts_at = "2023-07-17T00:00:00+00:00"
        target_two.ends_at = objective_end_date

        key_result = target_one.key_result
        key_result.starts_at = objective_start_date
        key_result.ends_at = objective_end_date
        objective = key_result.objective
        objective.ends_at = objective_end_date

        progress_point_one.key_result_id = key_result_id
        progress_point_one.measured_at = "2023-07-10"
        progress_point_one.target_id = target_one.id
        progress_point_two.key_result_id = key_result_id
        progress_point_two.measured_at = "2023-07-28"
        progress_point_two.target_id = target_two.id
        db_session.commit()

        target_ids = [target_one.id, target_two.id]
        input_targets = [
            {
                "id": target_one.id,
                "starts_at": objective_start_date,
                "ends_at": first_target_end,
                "value": target_one.value,
            },
            {
                "id": target_two.id,
                "starts_at": second_target_start,
                "ends_at": objective_end_date,
                "value": target_two.value,
            },
        ]

        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.update_keyresult(
            request=request_with_jwt,
            body={
                "input": {
                    "id": key_result_id,
                    "objective_id": objective.id,
                    "name": "Test KR 2",
                    "description": "Test KR Description 2",
                    "data_source": "Somewhere 2",
                    "starting_value": 0,
                    "targets": input_targets,
                    "app_owned_by": "232343434",
                    "owned_by": "uuid1212121",
                    "value_type": "constantine",
                },
                "action": {"name": "update_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        progress_points = (
            db_session.query(models.ProgressPoint)
            .filter_by(key_result_id=kr_id)
            .order_by(models.ProgressPoint.measured_at)
            .all()
        )
        assert progress_points is not None
        assert len(progress_points) == 2
        assert progress_points[0].target_id == target_ids[target_one_index]
        assert progress_points[1].target_id == target_ids[target_two_index]


class TestObjectiveKeyresultHistoryActions:
    """tests for History"""

    @pytest.mark.integration
    async def test_history_with_tenant_group_id(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):

        request_with_real_edit_jwt.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.roll_up_progress = False
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 112",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data

        obj = db_session.query(models.Objective).get(response_data["id"])
        assert obj.name == "Obj 112"
        assert obj.starts_at
        params = {
            "action": "insert_objective",
            "app_created_by": 123453,
            "app_last_updated_by": 12121212,
            "tenant_group_id_str": "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p",
            "created_at": "2023-08-01T00:00:00+00:00",
            "info": {"old": {}, "new": {}},
            "key_result_id": None,
            "objective_id": response_data["id"],
            "progress_point_id": None,
            "updated_at": "2023-08-01T00:00:00+00:00",
            "work_item_id": 223,
        }
        processed_data_list = []
        record = models.ActivityLog(**params)
        processed_data_list.append(record)
        db_session.add_all(processed_data_list)
        db_session.commit()
        history_response_data, history_response_status = await actions.get_history(
            request=request_with_real_edit_jwt,
            body={
                "input": {"id": response_data["id"], "type": "objective"},
                "action": {"name": "get_history"},
            },
        )
        assert history_response_status == HTTPStatus.OK
        assert "objective_id" in history_response_data[0]
        assert history_response_data[0]["objective_id"] == response_data["id"]

    @pytest.mark.integration
    async def test_history_with_tenant_id(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):

        request_with_real_edit_jwt.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.roll_up_progress = False
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 112",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data

        obj = db_session.query(models.Objective).get(response_data["id"])
        assert obj.name == "Obj 112"
        assert obj.starts_at
        params = {
            "action": "insert_objective",
            "app_created_by": 123453,
            "app_last_updated_by": 12121212,
            "tenant_id_str": "LEANKIT~d03-10128137327",
            "created_at": "2023-08-01T00:00:00+00:00",
            "info": {"old": {}, "new": {}},
            "key_result_id": None,
            "objective_id": response_data["id"],
            "progress_point_id": None,
            "updated_at": "2023-08-01T00:00:00+00:00",
            "work_item_id": 223,
        }
        processed_data_list = []
        record = models.ActivityLog(**params)
        processed_data_list.append(record)
        db_session.add_all(processed_data_list)
        db_session.commit()
        history_response_data, history_response_status = await actions.get_history(
            request=request_with_real_edit_jwt,
            body={
                "input": {"id": response_data["id"], "type": "objective"},
                "action": {"name": "get_history"},
            },
        )
        assert history_response_status == HTTPStatus.OK
        assert "objective_id" in history_response_data[0]
        assert history_response_data[0]["objective_id"] == response_data["id"]

    @pytest.mark.integration
    async def test_history_with_tenant_id(
        self,
        db_session,
        request_with_real_edit_jwt,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):

        request_with_real_edit_jwt.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.roll_up_progress = False
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 112",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data

        obj = db_session.query(models.Objective).get(response_data["id"])
        assert obj.name == "Obj 112"
        assert obj.starts_at
        params = {
            "action": "insert_objective",
            "app_created_by": 123453,
            "app_last_updated_by": 12121212,
            "tenant_id_str": "LEANKIT~d03-10128137327",
            "created_at": "2023-08-01T00:00:00+00:00",
            "info": {"old": {}, "new": {}},
            "key_result_id": None,
            "objective_id": response_data["id"],
            "progress_point_id": None,
            "updated_at": "2023-08-01T00:00:00+00:00",
            "work_item_id": 223,
        }
        processed_data_list = []
        record = models.ActivityLog(**params)
        processed_data_list.append(record)
        db_session.add_all(processed_data_list)
        db_session.commit()
        history_response_data, history_response_status = await actions.get_history(
            request=request_with_real_edit_jwt,
            body={
                "input": {"id": response_data["id"], "type": "objective"},
                "action": {"name": "get_history"},
            },
        )
        assert history_response_status == HTTPStatus.OK
        assert "objective_id" in history_response_data[0]
        assert history_response_data[0]["objective_id"] == response_data["id"]

    @pytest.mark.integration
    async def test_history_key_result(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Test an insert of key result"""
        request_with_real_edit_jwt.app["db_session"] = db_session
        settings = setting_factory()
        settings.tenant_id_str = "LEANKIT~d03-10128137327"
        settings.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.roll_up_progress = False
        wic = work_item_container_factory()
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        db_session.commit()
        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                },
                "action": {"name": "insert_objective"},
            },
        )

        obj_id = response_data.get("id")

        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK
        kr_id = response_data.get("id")
        assert kr_id

        params = {
            "action": "insert.keyresult",
            "app_created_by": 123453,
            "app_last_updated_by": 12121212,
            "tenant_id_str": "LEANKIT~d03-10128137327",
            "created_at": "2023-08-01T00:00:00+00:00",
            "info": {"old": {}, "new": {}},
            "key_result_id": kr_id,
            "objective_id": obj_id,
            "progress_point_id": None,
            "updated_at": "2023-08-01T00:00:00+00:00",
            "work_item_id": 223,
        }
        processed_data_list = []
        record = models.ActivityLog(**params)
        processed_data_list.append(record)
        db_session.add_all(processed_data_list)
        db_session.commit()
        history_response_data, history_response_status = await actions.get_history(
            request=request_with_real_edit_jwt,
            body={
                "input": {"id": kr_id, "type": "keyresult"},
                "action": {"name": "get_history"},
            },
        )
        assert history_response_status == HTTPStatus.OK
        assert "key_result_id" in history_response_data[0]
        assert history_response_data[0]["key_result_id"] == response_data["id"]


class TestProgressPoints:
    """Test custom progress point endpoints"""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "in_value, kr_progress, o_progress",
        [
            (3, 3, 3),
            (87, 87, 87),
            (109, 109, 100),
            (-1, -1, 0),
        ],
    )
    async def test_create_progress_point_no_previous_progress_points(
        self,
        db_session,
        setting_factory,
        key_result_factory,
        request_with_jwt,
        in_value,
        kr_progress,
        o_progress,
    ):
        """Ensure that the ProgressPoint is created and progress percentages are calculated correctly"""
        setting_factory()
        key_result = key_result_factory()
        db_session.commit()
        key_result_id = key_result.id
        key_result_starts_at = key_result.starts_at.date()
        key_result_starts_at_str = str(key_result_starts_at)

        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.insert_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "key_result_id": key_result_id,
                    "measured_at": key_result_starts_at_str,
                    "value": in_value,
                    "comment": f"here is a test comment for {in_value}",
                },
                "action": {"name": "insert_progress_point"},
            },
        )

        assert response_status == HTTPStatus.OK
        progress_point_id = response_data.get("id")
        assert progress_point_id

        created_progress_point = db_session.query(models.ProgressPoint).get(
            progress_point_id
        )
        updated_key_result = created_progress_point.key_result
        updated_objective = updated_key_result.objective

        assert created_progress_point is not None
        assert updated_key_result is not None
        assert updated_objective is not None

        assert created_progress_point.value == in_value
        assert created_progress_point.measured_at == key_result_starts_at
        assert (
            created_progress_point.comment == f"here is a test comment for {in_value}"
        )
        assert created_progress_point.key_result_progress_percentage == kr_progress
        assert created_progress_point.objective_progress_percentage == o_progress
        assert updated_key_result.progress_percentage == kr_progress
        assert updated_objective.progress_percentage == o_progress

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "old_measured_at, new_measured_at, progress_percentage",
        [
            ("2024-4-1", "2024-5-1", 9),
            ("2024-4-1", "2024-3-1", 13),
        ],
    )
    async def test_create_progress_point_with_existing_progress_points(
        self,
        db_session,
        setting_factory,
        key_result_factory,
        request_with_jwt,
        old_measured_at,
        new_measured_at,
        progress_percentage,
    ):
        """Ensure that the ProgressPoint is created and progress percentages are calculated correctly"""
        setting_factory()
        key_result = key_result_factory()
        db_session.commit()
        key_result_id = key_result.id

        request_with_jwt.app = {"db_session": db_session}

        (
            old_pp_response_data,
            old_pp_response_status,
        ) = await actions.insert_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "key_result_id": key_result_id,
                    "measured_at": old_measured_at,
                    "value": 13,
                    "comment": "here is a test comment",
                },
                "action": {"name": "insert_progress_point"},
            },
        )
        assert old_pp_response_status == HTTPStatus.OK
        old_progress_point_id = old_pp_response_data.get("id")
        assert old_progress_point_id

        (
            new_pp_response_data,
            new_pp_response_status,
        ) = await actions.insert_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "key_result_id": key_result_id,
                    "measured_at": new_measured_at,
                    "value": 9,
                    "comment": "here is a test comment",
                },
                "action": {"name": "insert_progress_point"},
            },
        )
        assert new_pp_response_status == HTTPStatus.OK
        new_progress_point_id = new_pp_response_data.get("id")
        assert new_progress_point_id

        new_progress_point = db_session.query(models.ProgressPoint).get(
            new_progress_point_id
        )
        updated_key_result = new_progress_point.key_result
        updated_objective = updated_key_result.objective
        assert new_progress_point is not None
        assert updated_key_result is not None
        assert updated_objective is not None

        assert updated_key_result.progress_percentage == progress_percentage
        assert updated_objective.progress_percentage == progress_percentage

        old_measured_at_date = datetime.strptime(old_measured_at, "%Y-%m-%d").date()
        new_measured_at_date = datetime.strptime(new_measured_at, "%Y-%m-%d").date()
        if new_measured_at_date > old_measured_at_date:
            assert (
                new_progress_point.key_result_progress_percentage == progress_percentage
            )
            assert (
                new_progress_point.objective_progress_percentage == progress_percentage
            )

    @pytest.mark.integration
    async def test_create_progress_point_duplicate(
        self,
        db_session,
        setting_factory,
        progress_point_factory,
        request_with_jwt,
    ):
        """Ensure that the ProgressPoint is created and progress percentages are calculated correctly."""
        setting_factory()
        existing_progress_point = progress_point_factory()
        measured_at = str(date.today())
        existing_progress_point.measured_at = measured_at
        db_session.commit()
        key_result_id = existing_progress_point.key_result_id
        existing_progress_point_id = existing_progress_point.id
        request_with_jwt.app = {"db_session": db_session}

        new_comment = "here is a new test comment"
        new_value = 3
        response_data, response_status = await actions.insert_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "key_result_id": key_result_id,
                    "measured_at": measured_at,
                    "value": new_value,
                    "comment": new_comment,
                },
                "action": {"name": "insert_progress_point"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST
        errors = json.loads(response_data["message"])
        assert errors[0]["error_code"] == "PROGRESS_POINT_DATE_EXIST"
        assert errors[0]["progress_point"] == {
            "id": existing_progress_point_id,
            "comment": new_comment,
            "value": new_value,
        }

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "measured_at",
        ["2024-4-31", "2024-13-1", "2024-1-32"],
    )
    async def test_create_progress_point_incorrect_date(
        self,
        db_session,
        setting_factory,
        key_result_factory,
        request_with_jwt,
        measured_at,
    ):
        """Ensure that the ProgressPoint is created and progress percentages are calculated correctly."""
        setting_factory()
        key_result = key_result_factory()
        db_session.commit()
        key_result_id = key_result.id
        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.insert_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "key_result_id": key_result_id,
                    "measured_at": measured_at,
                    "value": 9,
                    "comment": "here is a test comment",
                },
                "action": {"name": "insert_progress_point"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST
        errors = json.loads(response_data["message"])
        assert errors[0]["error_code"] == "INVALID_DATE_FORMAT"

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "index, progress_percentage",
        [
            (0, 23),
            (1, 38),
        ],
    )
    async def test_update_progress_point(
        self,
        db_session,
        setting_factory,
        key_result_factory,
        progress_point_factory,
        request_with_jwt,
        index,
        progress_percentage,
    ):
        """Ensure that the ProgressPoint is updated and progress percentages are calculated correctly."""
        setting_factory()
        today = date.today()
        yesterday = today - timedelta(days=1)
        progress_points = []

        first_progress_point = progress_point_factory()
        first_progress_point.measured_at = str(yesterday)
        first_progress_point.value = 17
        first_progress_point.key_result_progress_percentage = 17
        first_progress_point.objective_progress_percentage = 17

        key_result = key_result_factory()
        key_result.progress_percentage = 17
        db_session.commit()

        first_progress_point.key_result_id = key_result.id
        key_result.objective.progress_percentage = 17
        progress_points.append(first_progress_point.id)
        db_session.commit()

        second_progress_point = progress_point_factory()
        second_progress_point.measured_at = str(today)
        second_progress_point.value = 23
        second_progress_point.key_result_progress_percentage = 23
        second_progress_point.objective_progress_percentage = 23
        db_session.commit()

        second_progress_point.key_result_id = key_result.id
        progress_points.append(second_progress_point.id)
        key_result.progress_percentage = 23
        key_result.objective.progress_percentage = 23
        db_session.commit()
        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.update_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "id": progress_points[index],
                    "value": 37 + index,
                    "comment": f"comment_version_two_of_{index}",
                },
                "action": {"name": "update_progress_point"},
            },
        )
        assert response_status == HTTPStatus.OK
        progress_point_id = response_data.get("id")
        assert progress_point_id

        progress_point = db_session.query(models.ProgressPoint).get(progress_point_id)
        updated_key_result = progress_point.key_result
        updated_objective = updated_key_result.objective
        assert progress_point is not None
        assert updated_key_result is not None
        assert updated_objective is not None

        assert progress_point.value == 37 + index
        assert progress_point.comment == f"comment_version_two_of_{index}"
        assert updated_key_result.progress_percentage == progress_percentage
        assert updated_objective.progress_percentage == progress_percentage

        if index == len(progress_points) - 1:
            assert progress_point.key_result_progress_percentage == 37 + index
            assert progress_point.objective_progress_percentage == 37 + index

    @pytest.mark.integration
    async def test_delete_progress_point(
        self,
        db_session,
        setting_factory,
        progress_point_factory,
        request_with_jwt,
    ):
        """Ensure that the ProgressPoint is soft-deleted and progress percentages are calculated correctly."""
        setting_factory()

        progress_point = progress_point_factory()
        progress_point.value = 17
        progress_point.key_result_progress_percentage = 17
        progress_point.objective_progress_percentage = 17
        db_session.commit()

        key_result = progress_point.key_result
        key_result.progress_percentage = 17
        objective = key_result.objective
        objective.progress_percentage = 17
        db_session.commit()

        request_with_jwt.app = {"db_session": db_session}

        assert progress_point.deleted_at_epoch == 0

        response_data, response_status = await actions.delete_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "id": progress_point.id,
                },
                "action": {"name": "delete_progress_point"},
            },
        )
        assert response_status == HTTPStatus.OK
        progress_point_id = response_data.get("id")
        assert progress_point_id

        progress_point = db_session.query(models.ProgressPoint).get(progress_point_id)
        updated_key_result = progress_point.key_result
        updated_objective = updated_key_result.objective

        activity_log = (
            db_session.query(models.ActivityLog)
            .filter_by(progress_point_id=progress_point_id)
            .first()
        )

        assert progress_point is not None
        assert updated_key_result is not None
        assert updated_objective is not None
        assert progress_point.deleted_at_epoch != 0
        assert updated_key_result.progress_percentage == 0
        assert updated_objective.progress_percentage == 0
        assert activity_log.info

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "index, progress_percentage",
        [
            (0, 23),
            (1, 17),
        ],
    )
    async def test_delete_progress_point_from_multiple(
        self,
        db_session,
        setting_factory,
        key_result_factory,
        progress_point_factory,
        request_with_jwt,
        index,
        progress_percentage,
    ):
        """Ensure that the ProgressPoint is soft-deleted and progress percentages are calculated correctly."""
        setting_factory()
        today = date.today()
        yesterday = today - timedelta(days=1)
        progress_points = []

        first_progress_point = progress_point_factory()
        first_progress_point.measured_at = str(yesterday)
        first_progress_point.value = 17
        first_progress_point.key_result_progress_percentage = 17
        first_progress_point.objective_progress_percentage = 17

        key_result = key_result_factory()
        key_result.progress_percentage = 17
        db_session.commit()

        first_progress_point.key_result_id = key_result.id
        key_result.objective.progress_percentage = 17
        progress_points.append(first_progress_point.id)
        db_session.commit()

        second_progress_point = progress_point_factory()
        second_progress_point.measured_at = str(today)
        second_progress_point.value = 23
        second_progress_point.key_result_progress_percentage = 23
        second_progress_point.objective_progress_percentage = 23
        db_session.commit()

        second_progress_point.key_result_id = key_result.id
        progress_points.append(second_progress_point.id)
        key_result.progress_percentage = 23
        key_result.objective.progress_percentage = 23
        db_session.commit()
        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.delete_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "id": progress_points[index],
                },
                "action": {"name": "delete_progress_point"},
            },
        )
        assert response_status == HTTPStatus.OK
        progress_point_id = response_data.get("id")
        assert progress_point_id

        progress_point = db_session.query(models.ProgressPoint).get(progress_point_id)
        updated_key_result = progress_point.key_result
        updated_objective = updated_key_result.objective
        assert progress_point is not None
        assert updated_key_result is not None
        assert updated_objective is not None

        assert progress_point.deleted_at_epoch != 0
        assert updated_key_result.progress_percentage == progress_percentage
        assert updated_objective.progress_percentage == progress_percentage

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "measured_at, target_index",
        [
            ("2023-06-05", 0),
            ("2023-08-05", 1),
            ("2023-07-05", 0),
            ("2023-07-25", 1),
        ],
    )
    async def test_targets_progress_point_creation_mapping(
        self,
        db_session,
        setting_factory,
        target_factory,
        request_with_jwt,
        measured_at,
        target_index,
    ):
        """Ensure that the ProgressPoint is mapped to correct target id"""
        setting_factory()
        target_one = target_factory()
        db_session.commit()
        key_result_id = target_one.key_result_id
        target_two = target_factory()
        db_session.commit()

        objective_start_date = "2023-07-02T00:00:00+00:00"
        objective_end_date = "2023-07-31T00:00:00+00:00"
        objective = target_one.key_result.objective
        objective.starts_at = objective_start_date
        db_session.commit()

        target_one.starts_at = objective_start_date
        target_one.ends_at = "2023-07-15T00:00:00+00:00"
        target_two.key_result_id = key_result_id
        target_two.starts_at = "2023-07-16T00:00:00+00:00"
        target_two.ends_at = objective_end_date
        key_result = target_one.key_result
        key_result.starts_at = objective_start_date
        key_result.ends_at = objective_end_date
        objective = key_result.objective
        objective.ends_at = objective_end_date
        db_session.commit()

        target_ids = [target_one.id, target_two.id]

        request_with_jwt.app = {"db_session": db_session}

        (response_data, response_status,) = await actions.insert_progress_point(
            request=request_with_jwt,
            body={
                "input": {
                    "key_result_id": key_result_id,
                    "measured_at": measured_at,
                    "value": 13,
                    "comment": "here is a test comment",
                },
                "action": {"name": "insert_progress_point"},
            },
        )
        assert response_status == HTTPStatus.OK
        progress_point_id = response_data.get("id")
        assert progress_point_id

        new_progress_point = db_session.query(models.ProgressPoint).get(
            progress_point_id
        )
        assert new_progress_point is not None
        assert new_progress_point.target_id == target_ids[target_index]


class TestUserSettings:
    """Test User settings actions"""

    @pytest.mark.integration
    async def test_user_settings(
        self,
        db_session,
        request_with_pts_jwt,
    ):
        """Add user settings happy path."""

        request_with_pts_jwt.app["db_session"] = db_session
        tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tenant_id_str = "LEANKIT~d03-10128137327"
        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "name", "column_type": "static"}
                    ],
                },
                "action": {"name": "insert_user_setting"},
            },
        )
        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_user_settings_duplicate_values(
        self,
        db_session,
        request_with_pts_jwt,
    ):
        """Test user settings with duplicate values."""

        request_with_pts_jwt.app["db_session"] = db_session
        tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tenant_id_str = "LEANKIT~d03-10128137327"

        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": json.dumps(
                        [
                            {
                                "id": 0,
                                "index": 0,
                                "name": "name",
                                "column_type": "static",
                            },
                            {
                                "id": 0,
                                "index": 0,
                                "name": "name",
                                "column_type": "static",
                            },
                            {
                                "id": 2,
                                "index": 2,
                                "name": "name",
                                "column_type": "static",
                            },
                        ]
                    ),
                },
                "action": {"name": "insert_user_setting"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "value",
        [
            [
                {"id": 0, "index": 0, "name": "name", "column_type": "static"},
                {"id": 1, "index": 1, "name": "address", "column_type": "static"},
                {"id": 2, "index": 2, "name": "percentage", "column_type": "static"},
            ],
            [
                {"id": 1, "index": 1, "name": "name", "column_type": "static"},
                {"id": 0, "index": 0, "name": "address", "column_type": "static"},
                {"id": 3, "index": 3, "name": "percentage", "column_type": "static"},
            ],
            [
                {"id": 1, "index": 0, "name": "name", "column_type": "static"},
                {"id": 2, "index": 1, "name": "address", "column_type": "static"},
                {"id": 3, "index": 2, "name": "percentage", "column_type": "static"},
            ],
        ],
    )
    async def test_user_settings_parametrized(
        self,
        db_session,
        request_with_pts_jwt,
        value,
    ):
        """Test User settings with parametarized."""

        request_with_pts_jwt.app["db_session"] = db_session
        tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tenant_id_str = "LEANKIT~d03-10128137327"
        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": value,
                },
                "action": {"name": "insert_user_setting"},
            },
        )
        assert response_status == HTTPStatus.OK

    @pytest.mark.integration
    async def test_user_settings_duplicate_insert(
        self,
        db_session,
        request_with_pts_jwt,
    ):
        """Test to restrict duplicate record again."""

        request_with_pts_jwt.app["db_session"] = db_session
        tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tenant_id_str = "LEANKIT~d03-10128137327"

        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "name", "column_type": "static"}
                    ],
                },
                "action": {"name": "insert_user_setting"},
            },
        )
        request_with_pts_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "name", "column_type": "static"}
                    ],
                },
                "action": {"name": "insert_user_setting"},
            },
        )

        assert response_status == HTTPStatus.BAD_REQUEST

    @pytest.mark.integration
    async def test_update_user_settings(
        self,
        db_session,
        request_with_pts_jwt,
    ):
        """Test to user settings."""

        request_with_pts_jwt.app["db_session"] = db_session
        tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tenant_id_str = "LEANKIT~d03-10128137327"
        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "name", "column_type": "static"}
                    ],
                },
                "action": {"name": "insert_user_setting"},
            },
        )
        request_with_pts_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.update_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "names", "column_type": "static"}
                    ],
                },
                "action": {"name": "update_user_setting"},
            },
        )
        assert response_data["value"][0]["name"] == "names"

    @pytest.mark.integration
    async def test_update_user_settings_incorrect_data(
        self,
        db_session,
        request_with_pts_jwt,
    ):
        """Test to update user settings."""

        request_with_pts_jwt.app["db_session"] = db_session
        tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tenant_id_str = "LEANKIT~d03-10128137327"
        response_data, response_status = await actions.insert_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str,
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "name", "column_type": "static"}
                    ],
                },
                "action": {"name": "insert_user_setting"},
            },
        )
        request_with_pts_jwt.app["db_session"] = db_session
        response_data, response_status = await actions.update_user_setting(
            request=request_with_pts_jwt,
            body={
                "input": {
                    "type": "listviewcolumnconfig",
                    "user_id": tenant_group_id_str + "WRONG",
                    "app_user_id": tenant_id_str,
                    "value": [
                        {"id": 0, "index": 0, "name": "names", "column_type": "static"}
                    ],
                },
                "action": {"name": "update_user_setting"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST


class TestMultiLevelOKR:
    @pytest.mark.integration
    @pytest.mark.parametrize("separator_index", [4, 1, 8])
    async def test_three_levels_okr(
        self,
        db_session,
        setting_factory,
        objective_factory,
        key_result_factory,
        work_item_container_role_factory,
        request_with_jwt,
        separator_index,
    ):
        """Ensure that the multi level okr is working as expected"""
        setting = setting_factory()
        key_results = []

        for i in range(8):
            key_result = key_result_factory()
            key_results.append(key_result)
        extra_key_result = key_result_factory()
        extra_objective = objective_factory()
        db_session.commit()

        new_level_config = setting.level_config
        setting.level_config = [
            {"depth": 4, "name": "level4", "color": "#608eb6", "is_default": False},
            {"depth": 5, "name": "level5", "color": "#608eb6", "is_default": False},
            {"depth": 6, "name": "level6", "color": "#608eb6", "is_default": False},
            {"depth": 7, "name": "level7", "color": "#608eb6", "is_default": False},
        ]
        setting.level_config.extend(new_level_config)

        wic_role1 = work_item_container_role_factory(
            work_item_container__app_created_by=10145734719,
            app_created_by=10145734719,
            read_access=True,
        )
        wic1 = wic_role1.work_item_container

        wic_role2 = work_item_container_role_factory(
            work_item_container__app_created_by=10145734719,
            app_created_by=10145734719,
            read_access=True,
        )
        wic2 = wic_role2.work_item_container

        db_session.commit()
        previous_objective_id = None
        for i in range(8):
            objective = key_results[i].objective
            objective.level_depth = i
            if i != 0:
                objective.parent_objective_id = previous_objective_id
            if i < separator_index:
                objective.work_item_container_id = wic1.id
            else:
                objective.work_item_container_id = wic2.id
            previous_objective_id = objective.id
        db_session.commit()

        first_objective_id = key_results[0].objective.id
        extra_key_result.objective_id = first_objective_id
        extra_objective.parent_objective_id = first_objective_id
        last_objective_id = key_results[7].objective.id
        db_session.commit()

        external_id_1 = wic1.external_id
        external_id_2 = wic2.external_id
        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.multi_level_okr(
            request=request_with_jwt,
            body={
                "input": {
                    "external_id": external_id_1,
                    "external_type": "leankit",
                    "from_date": "2024-01-01T00:00:00+00:01",
                    "to_date": "2030-12-31T23:59:59+00:00",
                    "level_depth": [0, 1, 2, 3, 4, 5, 6, 7],
                    "is_card_view": True,
                    "order_by": "name",
                    "order": "asc",
                },
                "action": {"name": "multi_level_okr"},
            },
        )

        assert response_status == HTTPStatus.OK

        work_item_containers = response_data.get("work_item_containers")
        assert work_item_containers
        objectives = response_data.get("objectives")
        assert objectives

        assert len(work_item_containers) == 2 if separator_index != 8 else 1
        assert len(objectives) == min(separator_index + 3, 8)

        for objective in objectives:
            if objective["id"] == first_objective_id:
                assert objective["child_objectives_count"] == 2
                assert objective["key_results_count"] == 2
            elif objective["id"] == last_objective_id:
                assert objective["child_objectives_count"] == 0
                assert objective["key_results_count"] == 1
            else:
                assert objective["child_objectives_count"] == 1
                assert objective["key_results_count"] == 1

        response_data, response_status = await actions.multi_level_okr(
            request=request_with_jwt,
            body={
                "input": {
                    "external_id": external_id_2,
                    "external_type": "leankit",
                    "from_date": "2024-01-01T00:00:00+00:01",
                    "to_date": "2030-12-31T23:59:59+00:00",
                    "is_card_view": False,
                    "level_depth": [0, 1, 2, 3, 4, 5, 6, 7],
                    "order_by": "name",
                    "order": "asc",
                },
                "action": {"name": "multi_level_okr"},
            },
        )

        assert response_status == HTTPStatus.OK
        work_item_containers = response_data.get("work_item_containers")
        assert work_item_containers is not None
        objectives = response_data.get("objectives")
        assert objectives is not None
        assert len(work_item_containers) == (2 if separator_index != 8 else 0)
        assert len(objectives) == (
            min(8 - separator_index + 3, 8) if separator_index != 8 else 0
        )


class TestRollupSettings:
    @pytest.mark.integration
    async def test_update_rollup_settings(
        self, db_session, request_with_real_pvadmin_settings_jwt, build_level_config
    ):
        """Test to update roll up progress settings."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (
            response_data,
            response_status,
        ) = await actions.update_roll_up_progress_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "roll_up_progress": True,
                },
                "action": {"name": "toggle_rollup_setting"},
            },
        )
        assert response_data["roll_up_progress"] == True

    @pytest.mark.integration
    async def test_update_rollup_settings_fail_for_non_pvadmin(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Test to update roll up progress settings fail for non-pvadmin."""

        request_with_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (
            response_data,
            response_status,
        ) = await actions.update_roll_up_progress_configuration(
            request=request_with_jwt,
            body={
                "input": {
                    "roll_up_progress": True,
                },
                "action": {"name": "toggle_rollup_setting"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST
        assert (
            response_data["extensions"]["details"][0]["error_code"]
            == "NOT_PVADMIN_CUSTOMER"
        )

    @pytest.mark.integration
    async def test_update_rollup_settings_fail_for_edit_user(
        self, db_session, request_with_real_edit_jwt, build_level_config
    ):
        """Test to update roll up progress settings fail for edit user."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (
            response_data,
            response_status,
        ) = await actions.update_roll_up_progress_configuration(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "roll_up_progress": True,
                },
                "action": {"name": "toggle_rollup_setting"},
            },
        )
        assert response_status == HTTPStatus.FORBIDDEN
        assert (
            response_data["extensions"]["details"][0]["error_code"] == "NOT_MANAGE_ROLE"
        )


class TestColorThresholdConfigSettings:
    @pytest.mark.integration
    async def test_update_use_color_threshold_flag(
        self, db_session, request_with_real_pvadmin_settings_jwt, build_level_config
    ):
        """Test to update color threshold flag settings."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                is_color_threshold_enabled=False,
            )
        )
        db_session.commit()

        (
            response_data,
            response_status,
        ) = await actions.update_is_color_threshold_enabled_flag(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "is_color_threshold_enabled": True,
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert response_data["is_color_threshold_enabled"] == True

    @pytest.mark.integration
    async def test_update_use_color_threshold_flag_fail_for_non_pvadmin(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Test to update color threshold flag settings fail for non-pvadmin."""

        request_with_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (
            response_data,
            response_status,
        ) = await actions.update_is_color_threshold_enabled_flag(
            request=request_with_jwt,
            body={
                "input": {
                    "is_color_threshold_enabled": True,
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST
        assert (
            response_data["extensions"]["details"][0]["error_code"]
            == "NOT_PVADMIN_CUSTOMER"
        )

    @pytest.mark.integration
    async def test_update_use_color_threshold_flag_fail_for_edit_user(
        self, db_session, request_with_real_edit_jwt, build_level_config
    ):
        """Test to update roll up progress settings fail for edit user."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (
            response_data,
            response_status,
        ) = await actions.update_is_color_threshold_enabled_flag(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "is_color_threshold_enabled": True,
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert response_status == HTTPStatus.FORBIDDEN
        assert (
            response_data["extensions"]["details"][0]["error_code"] == "NOT_MANAGE_ROLE"
        )

    @pytest.mark.integration
    async def test_update_color_threshold_config_fail_for_non_pvadmin(
        self, db_session, request_with_jwt, build_level_config
    ):
        """Test to update color threshold flag settings fail for non-pvadmin."""

        request_with_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (response_data, response_status,) = await actions.update_color_threshold_config(
            request=request_with_jwt,
            body={
                "input": {
                    "color_threshold_config": [
                        {"max": 39, "min": 0, "name": "Red", "colorCode": "#F33535"},
                        {"max": 69, "min": 40, "name": "Amber", "colorCode": "#E97407"},
                        {
                            "max": 100,
                            "min": 70,
                            "name": "Green",
                            "colorCode": "#27A444",
                        },
                    ],
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert response_status == HTTPStatus.BAD_REQUEST
        assert (
            response_data["extensions"]["details"][0]["error_code"]
            == "NOT_PVADMIN_CUSTOMER"
        )

    @pytest.mark.integration
    async def test_update_color_threshold_config_fail_for_edit_user(
        self, db_session, request_with_real_edit_jwt, build_level_config
    ):
        """Test to update roll up progress settings fail for edit user."""

        request_with_real_edit_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                roll_up_progress=False,
            )
        )
        db_session.commit()

        (response_data, response_status,) = await actions.update_color_threshold_config(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "color_threshold_config": [
                        {"max": 39, "min": 0, "name": "Red", "colorCode": "#F33535"},
                        {"max": 69, "min": 40, "name": "Amber", "colorCode": "#E97407"},
                        {
                            "max": 100,
                            "min": 70,
                            "name": "Green",
                            "colorCode": "#27A444",
                        },
                    ],
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert response_status == HTTPStatus.FORBIDDEN
        assert (
            response_data["extensions"]["details"][0]["error_code"] == "NOT_MANAGE_ROLE"
        )

    @pytest.mark.integration
    async def test_update_color_threshold_config(
        self, db_session, request_with_real_pvadmin_settings_jwt, build_level_config
    ):
        """Test to update color threshold config settings."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                is_color_threshold_enabled=False,
            )
        )
        db_session.commit()

        (response_data, response_status,) = await actions.update_color_threshold_config(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "input": [
                        {"max": 40, "min": 0, "name": "Red", "colorCode": "#F33535"},
                        {"max": 70, "min": 40, "name": "Amber", "colorCode": "#E97407"},
                        {
                            "max": 100,
                            "min": 70,
                            "name": "Green",
                            "colorCode": "#27A444",
                        },
                    ],
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert response_data["is_color_threshold_enabled"] == False
        assert response_data["color_threshold_config"] == [
            {"max": 40, "min": 0, "name": "Red", "colorCode": "#F33535"},
            {"max": 70, "min": 40, "name": "Amber", "colorCode": "#E97407"},
            {"max": 100, "min": 70, "name": "Green", "colorCode": "#27A444"},
        ]

    @pytest.mark.integration
    async def test_update_color_threshold_config_min_max_fail(
        self, db_session, request_with_real_pvadmin_settings_jwt, build_level_config
    ):
        """Test to update color threshold config settings fail for next min value not equal to prev max value + 1."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                is_color_threshold_enabled=False,
            )
        )
        db_session.commit()

        (response_data, response_status,) = await actions.update_color_threshold_config(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "input": [
                        {"max": 39, "min": 0, "name": "Red", "colorCode": "#F33535"},
                        {"max": 69, "min": 41, "name": "Amber", "colorCode": "#E97407"},
                        {
                            "max": 100,
                            "min": 75,
                            "name": "Green",
                            "colorCode": "#27A444",
                        },
                    ],
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert (
            response_data["extensions"]["details"][0]["error_code"]
            == "INVALID_COLOR_THRESHOLD_CONFIGURATION"
        )
        assert response_data["extensions"]["details"][0]["message"] == [
            "Min value (41) of object at index 1 is not equal to max value (39) of previous object",
            "Min value (75) of object at index 2 is not equal to max value (69) of previous object",
        ]

    @pytest.mark.integration
    async def test_update_color_threshold_config_duplicate_names_fail(
        self, db_session, request_with_real_pvadmin_settings_jwt, build_level_config
    ):
        """Test to update color threshold config settings fail for duplicate color names."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                is_color_threshold_enabled=False,
            )
        )
        db_session.commit()

        (response_data, response_status,) = await actions.update_color_threshold_config(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "input": [
                        {"max": 40, "min": 0, "name": "Red", "colorCode": "#F33535"},
                        {"max": 70, "min": 40, "name": "Amber", "colorCode": "#E97407"},
                        {
                            "max": 100,
                            "min": 70,
                            "name": "Amber",
                            "colorCode": "#27A444",
                        },
                    ],
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert (
            response_data["extensions"]["details"][0]["error_code"]
            == "INVALID_COLOR_THRESHOLD_CONFIGURATION"
        )
        assert response_data["extensions"]["details"][0]["message"] == [
            "Duplicate name 'Amber' found at index 2"
        ]

    @pytest.mark.integration
    async def test_update_color_threshold_config_duplicate_colors_fail(
        self, db_session, request_with_real_pvadmin_settings_jwt, build_level_config
    ):
        """Test to update color threshold config settings fail for duplicate color codes."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        # Setup database.
        level_config = build_level_config(
            names=["Portfolio", "Team", "Support"], default_level_depth=2
        )
        db_session.add(
            models.Setting(
                level_config=level_config,
                tenant_group_id_str=tenant_group_id,
                is_color_threshold_enabled=False,
            )
        )
        db_session.commit()

        (response_data, response_status,) = await actions.update_color_threshold_config(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "input": [
                        {"max": 40, "min": 0, "name": "Red", "colorCode": "#F33535"},
                        {"max": 70, "min": 40, "name": "Amber", "colorCode": "#E97407"},
                        {
                            "max": 100,
                            "min": 70,
                            "name": "Green",
                            "colorCode": "#E97407",
                        },
                    ],
                },
                "action": {"name": "update_color_threshold_config"},
            },
        )
        assert (
            response_data["extensions"]["details"][0]["error_code"]
            == "INVALID_COLOR_THRESHOLD_CONFIGURATION"
        )
        assert response_data["extensions"]["details"][0]["message"] == [
            "Duplicate colorCode '#E97407' found at index 2"
        ]


class TestMultiLevelOkrs:
    """Tests for Upcoming Targets in Multi Level OKRs"""

    @pytest.mark.integration
    async def test_multi_level_okrs(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        user_settings_factory,
    ):
        """Test creating and retrieving a multi-level OKR"""

        # Setup request context
        request_with_real_edit_jwt.app["db_session"] = db_session

        # --- Tenant & Container Setup ---
        settings = setting_factory()
        tenant_id = "LEANKIT~d03-10128137327"
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.tenant_id_str = tenant_id
        settings.tenant_group_id_str = tenant_group_id
        settings.roll_up_progress = False

        wic = work_item_container_factory()
        wic.tenant_id_str = tenant_id
        wic.tenant_group_id_str = tenant_group_id
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        external_id = wic.external_id
        external_type = wic.external_type
        external_title = wic.external_title
        level_depth_default = wic.level_depth_default
        # --- Dates Setup ---
        now = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        objective_starts_at = (now - timedelta(days=20)).isoformat()
        objective_ends_at = (now + timedelta(days=20)).isoformat()
        key_result_starts_at = (now - timedelta(days=1)).isoformat()
        key_result_ends_at = now.isoformat()

        user_setting = user_settings_factory(
            type="listviewcolumnconfig",
            user_id="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_user_id="10135757550",
            value=[
                {
                    "id": "upcoming_target",
                    "index": 0,
                    "name": "Upcoming Target",
                    "hidden": False,
                    "column_type": "static",
                }
            ],
            tenant_id_str=tenant_id,
        )
        db_session.commit()

        # --- Insert Objective ---
        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "external_title": external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": objective_starts_at,
                    "ends_at": objective_ends_at,
                },
                "action": {"name": "insert_objective"},
            },
        )
        assert response_status == HTTPStatus.OK, "Objective insert failed"
        obj_id = response_data.get("id")
        assert obj_id, "No Objective ID returned"

        # --- Insert Key Result ---
        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": key_result_starts_at,
                    "ends_at": key_result_ends_at,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK, "Key Result insert failed"
        kr_id = response_data.get("id")
        assert kr_id, "No Key Result ID returned"

        # --- Fetch Multi-Level OKR ---
        response_data, response_status = await actions.multi_level_okr(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "from_date": objective_starts_at,
                    "to_date": objective_ends_at,
                    "is_card_view": False,
                    "filter_from_date": None,
                    "filter_to_date": None,
                    "filter_keyword": "",
                    "filter_parent_objective_ids": [],
                    "filter_child_objective_ids": [],
                    "order": "asc",
                    "order_by": "starts_at",
                    "level_depth": [level_depth_default],
                    "filter_owners": [],
                    "filter_is_unassigned": False,
                },
                "action": {"name": "multi_level_okr"},
            },
        )
        assert response_status == HTTPStatus.OK, "multi_level_okr failed"

        kr = response_data["objectives"][0]["key_results"][0]
        assert kr.get("upcoming_target_date") == now, "Incorrect upcoming_target_date"
        assert (
            kr.get("upcoming_target_value") == 100.0
        ), "Incorrect upcoming_target_value"

    @pytest.mark.integration
    async def test_multi_level_okrs_with_multiple_targets_ends_tomorrow(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        user_settings_factory,
    ):
        """Test creating and retrieving a multi-level OKR"""

        # Setup request context
        request_with_real_edit_jwt.app["db_session"] = db_session

        # --- Tenant & Container Setup ---
        settings = setting_factory()
        tenant_id = "LEANKIT~d03-10128137327"
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.tenant_id_str = tenant_id
        settings.tenant_group_id_str = tenant_group_id
        settings.roll_up_progress = False

        wic = work_item_container_factory()
        wic.tenant_id_str = tenant_id
        wic.tenant_group_id_str = tenant_group_id
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        external_id = wic.external_id
        external_type = wic.external_type
        external_title = wic.external_title
        level_depth_default = wic.level_depth_default
        # --- Dates Setup ---
        now = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        objective_starts_at = (now - timedelta(days=20)).isoformat()
        objective_ends_at = (now + timedelta(days=20)).isoformat()
        key_result_starts_at = (now - timedelta(days=2)).isoformat()
        # key_result_ends_at = now.isoformat()
        target_one_starts_at = key_result_starts_at
        target_one_ends_at = (now - timedelta(days=1)).isoformat()
        target_two_starts_at = (now - timedelta(days=0)).isoformat()
        target_two_ends_at = (now + timedelta(days=1)).isoformat()

        target_three_starts_at = (now + timedelta(days=2)).isoformat()
        target_three_ends_at = (now + timedelta(days=3)).isoformat()

        key_result_ends_at = target_three_ends_at

        user_setting = user_settings_factory(
            type="listviewcolumnconfig",
            user_id="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_user_id="10135757550",
            value=[
                {
                    "id": "upcoming_target",
                    "index": 0,
                    "name": "Upcoming Target",
                    "hidden": False,
                    "column_type": "static",
                }
            ],
            tenant_id_str=tenant_id,
        )
        db_session.commit()

        # --- Insert Objective ---
        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "external_title": external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": objective_starts_at,
                    "ends_at": objective_ends_at,
                },
                "action": {"name": "insert_objective"},
            },
        )
        assert response_status == HTTPStatus.OK, "Objective insert failed"
        obj_id = response_data.get("id")
        assert obj_id, "No Objective ID returned"

        # --- Insert Key Result ---
        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": key_result_starts_at,
                    "ends_at": key_result_ends_at,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                    "targets": [
                        {
                            "id": 1,
                            "starts_at": target_one_starts_at,
                            "ends_at": target_one_ends_at,
                            "value": 10,
                        },
                        {
                            "id": 2,
                            "starts_at": target_two_starts_at,
                            "ends_at": target_two_ends_at,
                            "value": 15,
                        },
                        {
                            "id": 3,
                            "starts_at": target_three_starts_at,
                            "ends_at": target_three_ends_at,
                            "value": 100,
                        },
                    ],
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK, "Key Result insert failed"
        kr_id = response_data.get("id")
        assert kr_id, "No Key Result ID returned"

        # --- Fetch Multi-Level OKR ---
        response_data, response_status = await actions.multi_level_okr(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "from_date": objective_starts_at,
                    "to_date": objective_ends_at,
                    "is_card_view": False,
                    "filter_from_date": None,
                    "filter_to_date": None,
                    "filter_keyword": "",
                    "filter_parent_objective_ids": [],
                    "filter_child_objective_ids": [],
                    "order": "asc",
                    "order_by": "starts_at",
                    "level_depth": [level_depth_default],
                    "filter_owners": [],
                    "filter_is_unassigned": False,
                },
                "action": {"name": "multi_level_okr"},
            },
        )
        assert response_status == HTTPStatus.OK, "multi_level_okr failed"

        kr = response_data["objectives"][0]["key_results"][0]
        assert kr.get("upcoming_target_date") == (
            now + timedelta(days=1)
        ), "Incorrect upcoming_target_date"
        assert (
            kr.get("upcoming_target_value") == 15.0
        ), "Incorrect upcoming_target_value"

    @pytest.mark.integration
    async def test_multi_level_okrs_with_multiple_targets_ends_today(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
        user_settings_factory,
    ):
        """Test creating and retrieving a multi-level OKR"""

        # Setup request context
        request_with_real_edit_jwt.app["db_session"] = db_session

        # --- Tenant & Container Setup ---
        settings = setting_factory()
        tenant_id = "LEANKIT~d03-10128137327"
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.tenant_id_str = tenant_id
        settings.tenant_group_id_str = tenant_group_id
        settings.roll_up_progress = False

        wic = work_item_container_factory()
        wic.tenant_id_str = tenant_id
        wic.tenant_group_id_str = tenant_group_id
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        external_id = wic.external_id
        external_type = wic.external_type
        external_title = wic.external_title
        level_depth_default = wic.level_depth_default
        # --- Dates Setup ---
        now = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        objective_starts_at = (now - timedelta(days=20)).isoformat()
        objective_ends_at = (now + timedelta(days=20)).isoformat()
        key_result_starts_at = (now - timedelta(days=3)).isoformat()
        # key_result_ends_at = now.isoformat()
        target_one_starts_at = key_result_starts_at
        target_one_ends_at = (now - timedelta(days=2)).isoformat()
        target_two_starts_at = (now - timedelta(days=1)).isoformat()
        target_two_ends_at = (now + timedelta(days=0)).isoformat()

        target_three_starts_at = (now + timedelta(days=1)).isoformat()
        target_three_ends_at = (now + timedelta(days=3)).isoformat()

        key_result_ends_at = target_three_ends_at

        user_setting = user_settings_factory(
            type="listviewcolumnconfig",
            user_id="1e8c7640-1ed9-437d-a981-7e64f405136f",
            app_user_id="10135757550",
            value=[
                {
                    "id": "upcoming_target",
                    "index": 0,
                    "name": "Upcoming Target",
                    "hidden": False,
                    "column_type": "static",
                }
            ],
            tenant_id_str=tenant_id,
        )
        db_session.commit()

        # --- Insert Objective ---
        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "external_title": external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": objective_starts_at,
                    "ends_at": objective_ends_at,
                },
                "action": {"name": "insert_objective"},
            },
        )
        assert response_status == HTTPStatus.OK, "Objective insert failed"
        obj_id = response_data.get("id")
        assert obj_id, "No Objective ID returned"

        # --- Insert Key Result ---
        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": key_result_starts_at,
                    "ends_at": key_result_ends_at,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                    "targets": [
                        {
                            "id": 1,
                            "starts_at": target_one_starts_at,
                            "ends_at": target_one_ends_at,
                            "value": 10,
                        },
                        {
                            "id": 2,
                            "starts_at": target_two_starts_at,
                            "ends_at": target_two_ends_at,
                            "value": 15,
                        },
                        {
                            "id": 3,
                            "starts_at": target_three_starts_at,
                            "ends_at": target_three_ends_at,
                            "value": 100,
                        },
                    ],
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK, "Key Result insert failed"
        kr_id = response_data.get("id")
        assert kr_id, "No Key Result ID returned"

        # --- Fetch Multi-Level OKR ---
        response_data, response_status = await actions.multi_level_okr(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "from_date": objective_starts_at,
                    "to_date": objective_ends_at,
                    "is_card_view": False,
                    "filter_from_date": None,
                    "filter_to_date": None,
                    "filter_keyword": "",
                    "filter_parent_objective_ids": [],
                    "filter_child_objective_ids": [],
                    "order": "asc",
                    "order_by": "starts_at",
                    "level_depth": [level_depth_default],
                    "filter_owners": [],
                    "filter_is_unassigned": False,
                },
                "action": {"name": "multi_level_okr"},
            },
        )
        assert response_status == HTTPStatus.OK, "multi_level_okr failed"

        kr = response_data["objectives"][0]["key_results"][0]
        assert kr.get("upcoming_target_date") == now, "Incorrect upcoming_target_date"
        assert (
            kr.get("upcoming_target_value") == 15.0
        ), "Incorrect upcoming_target_value"

    @pytest.mark.integration
    async def test_multi_level_okrs_with_multiple_targets_ends_yesterday(
        self,
        db_session,
        request_with_real_edit_jwt,
        request_with_real_edit_jwt_2,
        setting_factory,
        work_item_container_factory,
        work_item_container_role_factory,
    ):
        """Test creating and retrieving a multi-level OKR"""

        # Setup request context
        request_with_real_edit_jwt.app["db_session"] = db_session

        # --- Tenant & Container Setup ---
        settings = setting_factory()
        tenant_id = "LEANKIT~d03-10128137327"
        tenant_group_id = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        settings.tenant_id_str = tenant_id
        settings.tenant_group_id_str = tenant_group_id
        settings.roll_up_progress = False

        wic = work_item_container_factory()
        wic.tenant_id_str = tenant_id
        wic.tenant_group_id_str = tenant_group_id
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="1e8c7640-1ed9-437d-a981-7e64f405136f"
        )
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        external_id = wic.external_id
        external_type = wic.external_type
        external_title = wic.external_title
        level_depth_default = wic.level_depth_default
        # --- Dates Setup ---
        now = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        objective_starts_at = (now - timedelta(days=20)).isoformat()
        objective_ends_at = (now + timedelta(days=20)).isoformat()
        key_result_starts_at = (now - timedelta(days=4)).isoformat()
        # key_result_ends_at = now.isoformat()
        target_one_starts_at = key_result_starts_at
        target_one_ends_at = (now - timedelta(days=3)).isoformat()
        # target_two_starts_at = (now - timedelta(days=1)).isoformat()
        # target_two_ends_at = (now + timedelta(days=0)).isoformat()

        # target_three_starts_at = (now + timedelta(days=1)).isoformat()
        # target_three_ends_at = (now + timedelta(days=3)).isoformat()

        key_result_ends_at = target_one_ends_at
        # --- Insert Objective ---
        response_data, response_status = await actions.insert_objective(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "external_title": external_title,
                    "name": "Obj 1",
                    "level_depth": 3,
                    "starts_at": objective_starts_at,
                    "ends_at": objective_ends_at,
                },
                "action": {"name": "insert_objective"},
            },
        )
        assert response_status == HTTPStatus.OK, "Objective insert failed"
        obj_id = response_data.get("id")
        assert obj_id, "No Objective ID returned"

        # --- Insert Key Result ---
        response_data, response_status = await actions.insert_keyresult(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "objective_id": obj_id,
                    "starts_at": key_result_starts_at,
                    "ends_at": key_result_ends_at,
                    "name": "Test KR",
                    "description": "Test KR Description",
                    "data_source": "Somewhere",
                    "starting_value": 23,
                    "target_value": 100,
                    "value_type": "constant",
                    "targets": [
                        {
                            "id": 1,
                            "starts_at": target_one_starts_at,
                            "ends_at": target_one_ends_at,
                            "value": 10,
                        }
                    ],
                },
                "action": {"name": "insert_keyresult"},
            },
        )
        assert response_status == HTTPStatus.OK, "Key Result insert failed"
        kr_id = response_data.get("id")
        assert kr_id, "No Key Result ID returned"

        # --- Fetch Multi-Level OKR ---
        response_data, response_status = await actions.multi_level_okr(
            request=request_with_real_edit_jwt,
            body={
                "input": {
                    "external_id": external_id,
                    "external_type": external_type,
                    "from_date": objective_starts_at,
                    "to_date": objective_ends_at,
                    "is_card_view": False,
                    "filter_from_date": None,
                    "filter_to_date": None,
                    "filter_keyword": "",
                    "filter_parent_objective_ids": [],
                    "filter_child_objective_ids": [],
                    "order": "asc",
                    "order_by": "starts_at",
                    "level_depth": [level_depth_default],
                    "filter_owners": [],
                    "filter_is_unassigned": False,
                },
                "action": {"name": "multi_level_okr"},
            },
        )
        assert response_status == HTTPStatus.OK, "multi_level_okr failed"

        kr = response_data["objectives"][0]["key_results"][0]
        assert kr.get("upcoming_target_date") == None, "Incorrect upcoming_target_date"
        assert (
            kr.get("upcoming_target_value") == None
        ), "Incorrect upcoming_target_value"


class TestActivityOKRs:
    @pytest.mark.integration
    async def test_activity_okr_manager_no_linked_objectives(
        self, db_session, work_item_factory, request_with_jwt
    ):
        # Setup
        activity_ids = ["test-activity-no-link"]

        # Create work items with no connection to objectives
        wi = work_item_factory()
        db_session.commit()

        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.activity_associated_okrs(
            request=request_with_jwt,
            body={
                "input": {"activity_ids": activity_ids, "container_type": "lk_board"},
                "action": {"name": "activity_associated_okrs"},
            },
        )

        # Assert
        assert response_status == HTTPStatus.OK
        assert response_data is not None
        assert "objectives" in response_data
        assert "work_item_containers" in response_data
        assert "work_items" in response_data

        # Check empty results
        assert len(response_data["objectives"]) == 0
        assert len(response_data["work_item_containers"]) == 0
        assert len(response_data["work_items"]) == 0

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "activity_id_index, object_len",
        [
            (1, 2),
            (0, 1),
        ],
    )
    async def test_activity_okr_manager_get_okrs(
        self,
        mocker,
        db_session,
        work_item_container_factory,
        objective_factory,
        key_result_factory,
        work_item_factory,
        key_result_work_item_mapping_factory,
        work_item_container_role_factory,
        request_with_jwt,
        activity_id_index,
        object_len,
    ):
        activity_ids = ["test-activity-1", "test-activity-2"]

        # Create work item containers
        wic1 = work_item_container_factory(external_id="test-wic-1")
        wic2 = work_item_container_factory(external_id="test-wic-2")
        db_session.commit()

        user_id = "1234"
        # Mock the user id in our JWT to match that of the user id in this test
        mocker.patch("okrs_api.hasura.actions.auth.JWTParser.user_id", user_id)

        wic_role1 = work_item_container_role_factory(
            okr_role="manage", app_created_by=user_id
        )
        wic_role1.work_item_container_id = wic1.id
        wic_role2 = work_item_container_role_factory(
            okr_role="manage", app_created_by=user_id
        )
        wic_role2.work_item_container_id = wic2.id

        # Create objectives
        obj1 = objective_factory(
            name="Test Objective 1", work_item_container=wic1, level_depth=1
        )
        db_session.commit()
        obj2 = objective_factory(
            name="Test Objective 2",
            work_item_container=wic2,
            level_depth=2,
            parent_objective_id=obj1.id,
        )
        db_session.commit()

        # Create key results
        kr1 = key_result_factory(objective=obj1, name="Test KR 1")
        kr2 = key_result_factory(objective=obj2, name="Test KR 2")
        db_session.commit()

        # Create work items linked to key results
        wi1 = work_item_factory(
            external_id=activity_ids[0],
            title="activities_okrs.py",
            work_item_container=wic1,
        )
        wi2 = work_item_factory(
            external_id=activity_ids[1],
            title="test_actions.py",
            work_item_container=wic2,
        )
        db_session.commit()

        # Create mappings between KRs and work items
        key_result_work_item_mapping_factory(key_result=kr1, work_item=wi1)
        key_result_work_item_mapping_factory(key_result=kr2, work_item=wi2)
        db_session.commit()

        obj1_id, obj2_id = obj1.id, obj2.id
        kr1_id, kr2_id = kr1.id, kr2.id
        wic1_id, wic2_id = wic1.id, wic2.id
        wi1_id, wi2_id = wi1.id, wi2.id

        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.activity_associated_okrs(
            request=request_with_jwt,
            body={
                "input": {
                    "activity_ids": [activity_ids[activity_id_index]],
                    "container_type": "lk_board",
                },
                "action": {"name": "activity_associated_okrs"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data is not None
        assert "objectives" in response_data
        assert "work_item_containers" in response_data
        assert "work_items" in response_data

        # Check objectives
        assert len(response_data["objectives"]) == object_len
        objective_ids = {obj["id"] for obj in response_data["objectives"]}
        assert obj1_id in objective_ids

        # Check KRs within objectives
        for obj in response_data["objectives"]:
            if obj["id"] == obj1_id:
                assert len(obj["key_results"]) == 1
                assert obj["key_results"][0]["id"] == kr1_id
                assert wi1_id in obj["key_results"][0]["work_item_ids"]
            elif obj["id"] == obj2_id:
                assert len(obj["key_results"]) == 1
                assert obj["key_results"][0]["id"] == kr2_id
                assert wi2_id in obj["key_results"][0]["work_item_ids"]

        # Check WICs
        assert len(response_data["work_item_containers"]) == object_len
        wic_ids = {wic["id"] for wic in response_data["work_item_containers"]}
        assert wic1_id in wic_ids

        # Check work items
        assert len(response_data["work_items"]) == object_len
        wi_ids = {wi["id"] for wi in response_data["work_items"]}
        assert wi1_id in wi_ids

        # Check when child KR's activity_id given as input
        if object_len == 2:
            assert {obj1_id, obj2_id} == objective_ids
            assert {wic1_id, wic2_id} == wic_ids
            assert {wi1_id, wi2_id} == wi_ids

    @pytest.mark.integration
    async def test_activity_okr_manager_none_role(
        self,
        mocker,
        db_session,
        work_item_container_factory,
        objective_factory,
        key_result_factory,
        work_item_factory,
        key_result_work_item_mapping_factory,
        work_item_container_role_factory,
        request_with_jwt,
    ):
        activity_ids = ["test-activity-1", "test-activity-2"]

        # Create work item containers
        wic1 = work_item_container_factory(external_id="test-wic-1")
        wic2 = work_item_container_factory(external_id="test-wic-2")
        db_session.commit()

        user_id = "1234"
        # Mock the user id in our JWT to match that of the user id in this test
        mocker.patch("okrs_api.hasura.actions.auth.JWTParser.user_id", user_id)

        wic_role1 = work_item_container_role_factory(
            okr_role="manage", app_created_by=user_id
        )
        wic_role1.work_item_container_id = wic1.id
        wic_role2 = work_item_container_role_factory(
            okr_role="none", app_created_by=user_id
        )
        wic_role2.work_item_container_id = wic2.id

        # Create objectives
        obj1 = objective_factory(
            name="Test Objective 1", work_item_container=wic1, level_depth=1
        )
        db_session.commit()
        obj2 = objective_factory(
            name="Test Objective 2",
            work_item_container=wic2,
            level_depth=2,
            parent_objective_id=obj1.id,
        )
        db_session.commit()

        # Create key results
        kr1 = key_result_factory(objective=obj1, name="Test KR 1")
        kr2 = key_result_factory(objective=obj2, name="Test KR 2")
        db_session.commit()

        # Create work items linked to key results
        wi1 = work_item_factory(
            external_id=activity_ids[0],
            title="activities_okrs.py",
            work_item_container=wic1,
        )
        wi2 = work_item_factory(
            external_id=activity_ids[1],
            title="test_actions.py",
            work_item_container=wic2,
        )
        db_session.commit()

        # Create mappings between KRs and work items
        key_result_work_item_mapping_factory(key_result=kr1, work_item=wi1)
        key_result_work_item_mapping_factory(key_result=kr2, work_item=wi2)
        db_session.commit()

        obj1_id = obj1.id
        kr1_id = kr1.id
        wic1_id = wic1.id
        wi1_id = wi1.id

        request_with_jwt.app = {"db_session": db_session}

        response_data, response_status = await actions.activity_associated_okrs(
            request=request_with_jwt,
            body={
                "input": {
                    "activity_ids": [activity_ids[1]],
                    "container_type": "lk_board",
                },
                "action": {"name": "activity_associated_okrs"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert response_data is not None
        assert "objectives" in response_data
        assert "work_item_containers" in response_data
        assert "work_items" in response_data

        # Check objectives
        assert len(response_data["objectives"]) == 1
        curr_objective = response_data["objectives"][0]
        assert obj1_id == curr_objective["id"]

        # Check KRs within objectives
        assert len(curr_objective["key_results"]) == 1
        assert curr_objective["key_results"][0]["id"] == kr1_id
        assert len(curr_objective["key_results"][0]["work_item_ids"]) == 1
        assert wi1_id in curr_objective["key_results"][0]["work_item_ids"]

        # Check WICs
        assert len(response_data["work_item_containers"]) == 1
        assert wic1_id == response_data["work_item_containers"][0]["id"]

        # Check work items
        assert len(response_data["work_items"]) == 1
        assert wi1_id == response_data["work_items"][0]["id"]


class TestDeleteWorkItemContainer:
    @pytest.fixture
    async def preset_column_configs(
        self, db_session, request_with_real_pvadmin_settings_jwt
    ):
        """A fixture to create default set of fields."""
        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple text field",
                    "ca_config_type": "text",
                    "tooltip": "A very simple text field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple date field",
                    "ca_config_type": "date",
                    "tooltip": "A very simple date field",
                    "is_objective": False,
                    "is_keyresult": True,
                    "is_mandatory_keyresult": True,
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        await actions.insert_custom_attributes_configuration(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "label": "Simple multiselect field",
                    "ca_config_type": "multiselect",
                    "tooltip": "A very simple multiselect field",
                    "is_objective": True,
                    "is_keyresult": False,
                    "is_mandatory_keyresult": True,
                    "value": [
                        dict(value="Ini"),
                        dict(value="Mini"),
                        dict(value="Myni"),
                        dict(value="Mo"),
                    ],
                },
                "action": {"name": "insert_custom_attributes_configurations"},
            },
        )

        response_data, _ = await actions.custom_attributes_configurations(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"is_active": True},
                "action": {"name": "custom_attributes_configurations"},
            },
        )

        return response_data

    @pytest.mark.integration
    async def test_delete_wic_cascade(
        self,
        db_session,
        setting_factory,
        target_factory,
        progress_point_factory,
        key_result_factory,
        objective_factory,
        work_item_container_factory,
        request_with_real_edit_jwt_2,
        work_item_container_role_factory,
    ):
        """Test to delete work item container and all its entities."""

        request_with_real_edit_jwt_2.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic2 = work_item_container_factory()
        wic.external_id = "12345"
        wic.container_type = "lk_board"
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic.tenant_id_str = "LEANKIT~d03-10128137327"
        wic2.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        wic2.tenant_id_str = "LEANKIT~d03-10128137327"
        wic2_id = wic2.id
        db_session.commit()

        wic_role = work_item_container_role_factory(
            okr_role="manage", created_by="35b4fbf6-5b65-4e69-9a46-2c281e944d3b"
        )
        db_session.add(wic_role)
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        obj = objective_factory()
        obj.work_item_container_id = wic.id
        obj.level_depth = 2
        obj.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.add(obj)
        db_session.commit()
        objective_id = obj.id

        # child objective in a different board
        child_objective = objective_factory()
        child_objective.level_depth = 3
        child_objective.parent_objective_id = objective_id
        child_objective.work_item_container_id = wic2_id
        child_objective.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.add(child_objective)
        db_session.commit()
        child_objective_id = child_objective.id

        # key result with target
        kr = key_result_factory(
            objective=obj,
        )
        tr = target_factory(
            key_result=kr,
        )
        kr.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        tr.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.add(tr)
        db_session.add(kr)
        progress_point = progress_point_factory(key_result=kr)
        progress_point.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:p"
        db_session.add(progress_point)
        db_session.commit()
        kr_id = kr.id
        tr_id = tr.id
        pp_id = progress_point.id

        response, response_status = await actions.delete_work_item_containers(
            request=request_with_real_edit_jwt_2,
            body={
                "input": {"container_type": "lk_board", "external_ids": ["12345"]},
                "action": {"name": "delete_work_item_containers_async"},
            },
        )

        assert response_status == HTTPStatus.OK

        # All these assertion after deletion of wic
        obj = db_session.query(models.Objective).get(objective_id)
        assert obj.deleted_at_epoch != 0

        kr = db_session.query(models.KeyResult).get(kr_id)
        assert kr.deleted_at_epoch != 0

        tr = db_session.query(models.Target).get(tr_id)
        assert tr.is_deleted == True

        pp = db_session.query(models.ProgressPoint).get(pp_id)
        assert pp.deleted_at_epoch != 0

        child_objective = db_session.query(models.Objective).get(child_objective_id)
        assert child_objective.parent_objective_id is None

    @pytest.mark.integration
    async def test_delete_wic_cascade_custom_attributes(
        self,
        db_session,
        preset_column_configs,
        setting_factory,
        work_item_container_factory,
        request_with_real_pvadmin_settings_jwt,
        work_item_container_role_factory,
    ):
        """Test to delete work item container and custom attribute values for its objectives."""

        request_with_real_pvadmin_settings_jwt.app["db_session"] = db_session
        setting_factory()
        wic = work_item_container_factory()
        wic.external_id = "54321"
        wic.container_type = "lk_board"
        wic.tenant_group_id_str = "7db85cde-95ac-4df1-a3d1-0e986180f6ba:sb"
        wic_role = work_item_container_role_factory(
            okr_role="manage",
            created_by="13128f97-d58a-4ab5-90b5-5c9697aaf417",
            work_item_container=wic,
        )
        db_session.add(wic_role)
        wic_role.work_item_container_id = wic.id
        db_session.commit()
        text_config = None

        for config in preset_column_configs:
            if config["ca_config_type"] == "text":
                text_config = config

        response_data, response_status = await actions.insert_objective(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {
                    "external_id": wic.external_id,
                    "external_type": wic.external_type,
                    "external_title": wic.external_title,
                    "name": "Obj wic delete",
                    "level_depth": 2,
                    "starts_at": "2023-08-01T00:00:00+00:00",
                    "ends_at": "2023-08-28T00:00:00+00:00",
                    "ca_values": json.dumps({text_config["id"]: "Hello world"}),
                },
                "action": {"name": "insert_objective"},
            },
        )

        assert response_status == HTTPStatus.OK
        assert "id" in response_data

        objective_id = response_data["id"]

        response, response_status = await actions.delete_work_item_containers(
            request=request_with_real_pvadmin_settings_jwt,
            body={
                "input": {"container_type": "lk_board", "external_ids": ["54321"]},
                "action": {"name": "delete_work_item_containers_async"},
            },
        )
        assert response_status == HTTPStatus.OK

        custom_attributes_value = (
            db_session.query(models.CustomAttributesValue)
            .filter(
                models.CustomAttributesValue.object_type == "objective",
                models.CustomAttributesValue.object_id == objective_id,
            )
            .all()
        )

        assert custom_attributes_value[0].deleted_at_epoch != 0
