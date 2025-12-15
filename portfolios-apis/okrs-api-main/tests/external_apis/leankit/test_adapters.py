from open_alchemy import models

import pytest

from okrs_api.external_apis.leankit import adapters
from okrs_api.external_apis.leankit.adapters import AdapterLauncher
from tests.external_apis.leankit import response_payloads
from okrs_api import utils


class TestErrorAdapter:
    """Errors from leankit."""

    LK_RESPONSE_DATA = {"message": "Could not do the thing"}

    CUSTOM_ERRORS = ["Context id is wrong", "Domain is wrong"]

    @pytest.mark.parametrize(
        "custom_errors, reason, result",
        [
            pytest.param(
                None, None, ("Could not do the thing", None), id="nothing-special"
            ),
            pytest.param(
                CUSTOM_ERRORS, None, ("Domain is wrong", None), id="custom-errors-only"
            ),
            pytest.param(
                None,
                "Bad input",
                ("Could not do the thing", "Bad input"),
                id="reason-only",
            ),
            pytest.param(
                CUSTOM_ERRORS,
                "Bad input",
                ("Context id is wrong", "Bad input"),
                id="everything",
            ),
        ],
    )
    def test_errors(self, custom_errors, reason, result):
        """Ensure errors and reasons are packaged properly."""
        adapted_data = adapters.errors(self.LK_RESPONSE_DATA, custom_errors, reason)
        expected_message, expected_reason = result
        assert expected_message in adapted_data["errors"]
        assert expected_reason == adapted_data["reason"]


class TestActivityTypesResponseAdapter:
    """Test the LeanKitActivityTypes Service of the Leankit API."""

    LK_RESPONSE_DATA = {
        "cardTypes": [
            {
                "id": "10121496438",
                "name": "Defect",
                "colorHex": "#F69679",
                "isCardType": True,
                "isTaskType": True,
            },
            {
                "id": "10121496439",
                "name": "User Story",
                "colorHex": "#FFBB00",
                "isCardType": True,
                "isTaskType": True,
            },
            {
                "id": "10121496440",
                "name": "Task",
                "colorHex": "#D3E0E4",
                "isCardType": True,
                "isTaskType": True,
            },
            {
                "id": "10121496441",
                "name": "Epic",
                "colorHex": "#8CC63F",
                "isCardType": False,
                "isTaskType": True,
            },
        ]
    }

    def test_adapt_card_types(self):
        """Ensure data proper data normalization."""
        adapter = adapters.ActivityTypesAdapter(self.LK_RESPONSE_DATA)
        activity_types = adapter.adapt()
        activity_type_names = [
            activity_type["name"] for activity_type in activity_types
        ]
        activity_type_ids = [activity_type["id"] for activity_type in activity_types]

        assert "User Story" in activity_type_names

        # Only get card types that have `isCardType` set to True
        assert "10121496441" not in activity_type_ids

    def test_list_activity_types(self):
        """Ensure that the activity types are present."""
        launcher = AdapterLauncher(self.LK_RESPONSE_DATA)
        adapted_data = launcher.list_activity_types()
        activity_type_names = [activity_type["name"] for activity_type in adapted_data]
        assert "User Story" in activity_type_names


class TestLeanKitCardToWorkItemAdapter:
    """Tests for the LeanKitCard to WorkItem conversion."""

    @pytest.fixture
    def response_data_builder(self):
        """ "Build LK response data with the lane card status."""

        def _response_data_builder(lane_card_status):
            return {
                "card_details": {
                    "id": "12345",
                    "title": "Pizza Party",
                    "plannedStart": "2019-12-20",
                    "plannedFinish": "2019-12-23",
                    "actualFinish": "2019-12-05T21:52:12Z",
                    "actualStart": "2019-12-05T21:52:10Z",
                    "type": {
                        "id": "999",
                        "title": "Improvement",
                        "cardColor": "#B8CFDF",
                    },
                    "lane": {
                        "id": "1",
                        "laneClassType": "active",
                        "laneType": "completed",
                        "title": "Recently Finished",
                    },
                },
                "board_details": {
                    "lanes": [
                        {
                            "id": "1",
                            "name": "Not Started - Future Work",
                            "cardStatus": lane_card_status,
                            "active": True,
                            "isDefaultDropLane": False,
                        },
                    ]
                },
            }

        return _response_data_builder

    @pytest.mark.parametrize(
        "lane_card_status, expected_state",
        [
            pytest.param("notStarted", "not_started", id="Not Started"),
            pytest.param("started", "in_progress", id="In Progress"),
            pytest.param("finished", "finished", id="Finished"),
        ],
    )
    def test_adapt(self, response_data_builder, lane_card_status, expected_state):
        """Ensure that a card is converted to Work Item attributes."""

        input_data = response_data_builder(lane_card_status)
        expected = {
            "title": "Pizza Party",
            "external_type": "leankit",
            "container_type": "lk_board",
            "external_id": "12345",
            "item_type": "Improvement",
            "state": expected_state,
            "planned_start": "2019-12-20",
            "planned_finish": "2019-12-23",
        }

        adapter = adapters.CardToWorkItemAdapter(input_data)
        work_item_obj = adapter.adapt()

        assert work_item_obj == expected


class TestLeanKitUsersAdapter:
    """Ensure that the leankit user adapter returns the proper attributes."""

    def test_adapt(self):
        """Ensure that leankit response data is converted to [users]."""
        input_data = response_payloads.search_users_response()

        expected = [
            {
                "id": "1234",
                "first_name": "Bob",
                "last_name": "Smith",
                "email_address": "Bob@myco.com",
                "role": "Reader",
                "administrator": False,
            }
        ]

        adapter = adapters.UsersAdapter(input_data)
        users = adapter.adapt()

        assert users == expected


class TestUserInfoAdapter:
    """Ensure that the leankit user"""

    @pytest.mark.parametrize(
        "app_role_key, okrs_role",
        [
            pytest.param("boardReader", "read", id="reader"),
            pytest.param("boardUser", "edit", id="user"),
            pytest.param("boardManager", "manage", id="manager"),
            pytest.param("boardAdministrator", "manage", id="administrator"),
            pytest.param("boardCreator", "manage", id="creator"),
        ],
    )
    @pytest.mark.integration
    def test_adapt(
        self,
        db_session,
        setting_factory,
        work_item_container_factory,
        app_role_key,
        okrs_role,
    ):
        """
        Ensure the user info comes back properly.

        This test takes in no context_ids, so all the permissions will be
        limited to the board ids from the available WorkItemContainers for that
        user.
        """
        setting_factory()
        wic = work_item_container_factory(
            external_title="Test WIC",
            external_id="1234",
        )

        # begin test
        input_data = response_payloads.user_info_response(board_role_key=app_role_key)

        expected = {
            "id": "1234",
            "first_name": "Patti",
            "last_name": "Stiles",
            "email_address": "pstiles@planview.com",
            "work_item_container_roles": [
                {
                    "context_id": "1234",
                    "okr_role": okrs_role,
                    "app_role": app_role_key,
                }
            ],
        }
        adapter = adapters.UserInfoAdapter(
            response_data=input_data,
            org_id=wic.tenant_id_str,
            available_work_item_containers=[wic],
        )
        info = adapter.adapt()

        assert info == expected

    @pytest.mark.parametrize(
        "context_ids, expected_okr_roles",
        [
            pytest.param(["1", "1234"], ["none", "manage"], id="multiple-wics"),
            pytest.param(None, ["manage"], id="no-context-ids"),
        ],
    )
    @pytest.mark.integration
    def test_adapt_with_context_ids(
        self, db_session, work_item_container_factory, context_ids, expected_okr_roles
    ):
        """Ensure the user info comes back properly."""
        #  Setup DB
        wic = work_item_container_factory(external_id="1234")
        db_session.commit()

        # begin test
        api_payload = response_payloads.user_info_response(
            board_role_key="boardManager"
        )

        adapter = adapters.UserInfoAdapter(
            response_data=api_payload,
            db_session=db_session,
            org_id=wic.tenant_id_str,
            context_ids=context_ids,
            available_work_item_containers=[wic],
        )

        info = adapter.adapt()
        role_names = [role["okr_role"] for role in info["work_item_container_roles"]]

        # We should get back the appropriate role names
        assert set(role_names) == set(expected_okr_roles)

    @pytest.mark.integration
    def test_adapt_with_duplicate_context_ids(
        self, db_session, work_item_container_factory
    ):
        """
        Ensure the user info comes back, even for duplicate roles.

        If Leankit provides multiple roles for a board [erroneously], we will
        only take the first match.
        """
        #  Setup DB
        wic = work_item_container_factory()
        db_session.commit()

        # begin test
        api_payload = response_payloads.user_info_response(
            board_role_data=[
                (wic.external_id, "boardReader"),
                (wic.external_id, "noAccess"),
            ]
        )

        adapter = adapters.UserInfoAdapter(
            response_data=api_payload,
            db_session=db_session,
            org_id=wic.tenant_id_str,
            context_ids=[wic.external_id],
            available_work_item_containers=[wic],
        )

        info = adapter.adapt()
        role_names = [role["okr_role"] for role in info["work_item_container_roles"]]

        # We should get back the appropriate role name and only one role.
        assert len(role_names) == 1
        assert role_names[0] == "read"

    @pytest.mark.integration
    def test_no_access(self, db_session, work_item_container_factory):
        """Ensure the case for no access is handled properly."""
        #  Setup DB
        wic = work_item_container_factory(
            external_title="Test WIC",
            external_id="abc-1234",
        )
        db_session.commit()

        # begin test
        input_data = {
            "username": "pstiles@planview.com",
            "firstName": "Patti",
            "lastName": "Stiles",
            "fullName": "Patti Stiles",
            "emailAddress": "pstiles@planview.com",
            "lastAccess": "2021-03-30T17:20:46.900Z",
            "dateFormat": "MM/dd/yyyy",
            "administrator": False,
            "enabled": True,
            "deleted": False,
            "organizationId": "10100000101",
            "boardCreator": False,
            "timeZone": "America/Chicago",
            "licenseType": "full",
            "externalUserName": None,
            "boardRoles": [],
        }
        expected = {
            "id": wic.id,
            "first_name": "Patti",
            "last_name": "Stiles",
            "email_address": "pstiles@planview.com",
            "work_item_container_roles": [
                {
                    "context_id": "abc-1234",
                    "okr_role": "none",
                    "app_role": "noAccess",
                }
            ],
        }
        adapter = adapters.UserInfoAdapter(
            response_data=input_data,
            org_id=wic.tenant_id_str,
            available_work_item_containers=[wic],
        )
        info = adapter.adapt()

        assert (
            info["work_item_container_roles"] == expected["work_item_container_roles"]
        )


class TestLeanKitCardListWithAccessAdapter:
    """Tests for the LeanKitCard to WorkItem conversion."""

    @pytest.fixture
    def response_data_builder(self):
        """ "Build LK response data with the lane card status."""

        def _response_data_builder(lane_card_status):
            return {
                "card_list": {
                    "cards": [],
                    "inaccessibleCards": [
                        {
                            "id": "12345",
                            "title": "Pizza Party",
                            "plannedStart": "2019-12-20",
                            "plannedFinish": "2019-12-23",
                            "actualFinish": "2019-12-05T21:52:12Z",
                            "actualStart": "2019-12-05T21:52:10Z",
                            "isDeleted": True,
                            "state": lane_card_status,
                            "type": {
                                "id": "999",
                                "title": "Improvement",
                                "cardColor": "#B8CFDF",
                            },
                            "lane": {
                                "id": "1",
                                "laneClassType": "active",
                                "laneType": "completed",
                                "title": "Recently Finished",
                            },
                            "board": {
                                "id": "1",
                                "name": "Not Started - Future Work",
                                "cardStatus": lane_card_status,
                                "active": True,
                                "isDefaultDropLane": False,
                            },
                        }
                    ],
                }
            }

        return _response_data_builder

    def test_adapt(self, mocker, response_data_builder):
        """Ensure that a card is converted to Work Item attributes."""

        # mocker.patch("okrs_api.model_helpers.common.clean_wi_and_kr_wi_mapping", mocker.Mock(return_value=None))
        input_data = response_data_builder("nat_started")
        input_prepper = utils.Map(
            {
                "input_parser": utils.Map(
                    {
                        "context_id": "1212",
                        "domain": "d09.leankit.io",
                        "exclude_no_access": False,
                        "product_type": "leankit",
                    }
                )
            }
        )

        expected = []
        adapter = adapters.CardListWithAccessAdapter(input_data, input_prepper)
        work_item_obj = adapter.adapt()
        assert work_item_obj == expected
