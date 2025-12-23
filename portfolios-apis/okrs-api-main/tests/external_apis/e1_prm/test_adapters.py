from open_alchemy import models

import pytest

from okrs_api.external_apis.e1_prm import adapters
from okrs_api.external_apis.e1_prm.adapters import AdapterLauncher
from okrs_api.hasura.actions.prepper import prepper_factory


class TestErrorAdapter:
    """Errors from e1 prm."""

    RESPONSE_DATA = {"message": "Could not do the thing"}

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
        adapted_data = adapters.errors(self.RESPONSE_DATA, custom_errors, reason)
        expected_message, expected_reason = result
        assert expected_message in adapted_data["errors"]
        assert expected_reason == adapted_data["reason"]


class TestPRMCardToWorkItemAdapter:
    """Tests for the PRMCard to WorkItem conversion."""

    @pytest.fixture
    def response_data_builder(self):
        """ "Build LK response data with the lane card status."""

        def _response_data_builder():
            return {
                "project_details": {
                    "Entities": [
                        {
                            "ShortName": "0000015",
                            "ProductInvestmentApproval": {
                                "StructureCode": "WBS27$ANLZ",
                                "Description": "Analyze",
                            },
                            "RequestedStart": "2016-08-29T08:00:00",
                            "RequestedFinish": "2017-03-27T17:00:00",
                            "CreatedOn": "2015-04-16T14:30:23",
                            "CreatedBy": {
                                "UserName": "cfrances",
                                "FullName": "Charles Frances - Product Mgr.",
                            },
                            "LifecycleAdminUser": {
                                "UserName": "cfrances",
                                "FullName": "Charles Frances - Product Mgr.",
                            },
                            "IsLifecycleEnabled": False,
                            "HasLifecycle": True,
                            "StructureCode": "1906",
                            "ScheduleStart": "2017-06-26T08:00:00",
                            "ScheduleFinish": "2018-09-05T14:08:00",
                            "ScheduleDuration": 149108,
                            "ActualStart": "2015-10-11T00:00:00",
                            "ActualFinish": None,
                            "Calendar": {
                                "StructureCode": "STANDARD",
                                "Description": "Standard",
                            },
                            "Status": {
                                "StructureCode": "WBS20$OPEN",
                                "Description": "Open / Active",
                            },
                            "IsMilestone": False,
                            "Project": {
                                "StructureCode": "1906",
                                "Description": "Vendor e-Commerce",
                            },
                            "Place": 4,
                            "Parent": {
                                "StructureCode": "9",
                                "Description": "E-Commerce",
                            },
                            "Description": "Vendor e-Commerce",
                            "HasChildren": True,
                            "Depth": 5,
                            "ConstraintDate": "2017-04-10T08:00:00",
                            "ConstraintType": 5,
                            "ProgressAsPlanned": False,
                            "EnterStatus": False,
                            "Ticketable": False,
                            "DoNotProgress": False,
                            "Attributes": {
                                "ExecType": {
                                    "StructureCode": "29978",
                                    "Description": "project",
                                },
                                "AccessLevel": 3,
                            },
                        },
                        {
                            "ShortName": "0002251",
                            "ProductInvestmentApproval": {
                                "StructureCode": "WBS27$PEND",
                                "Description": "Pending",
                            },
                            "RequestedStart": None,
                            "RequestedFinish": None,
                            "CreatedOn": "2022-02-21T17:24:44.017",
                            "CreatedBy": {
                                "UserName": "pvmaster",
                                "FullName": "Planview Master User",
                            },
                            "LifecycleAdminUser": {
                                "UserName": "pvmaster",
                                "FullName": "Planview Master User",
                            },
                            "IsLifecycleEnabled": True,
                            "HasLifecycle": True,
                            "StructureCode": "39405",
                            "ScheduleStart": None,
                            "ScheduleFinish": None,
                            "ScheduleDuration": 0,
                            "ActualStart": None,
                            "ActualFinish": None,
                            "Calendar": {
                                "StructureCode": "STANDARD",
                                "Description": "Standard",
                            },
                            "Status": {
                                "StructureCode": "WBS20$REQT",
                                "Description": "Request",
                            },
                            "IsMilestone": False,
                            "Project": {
                                "StructureCode": "39405",
                                "Description": "testee",
                            },
                            "Place": 1,
                            "Parent": {
                                "StructureCode": "13",
                                "Description": "Accounts Payable",
                            },
                            "Description": "testee",
                            "HasChildren": True,
                            "Depth": 5,
                            "ConstraintDate": None,
                            "ConstraintType": 0,
                            "ProgressAsPlanned": True,
                            "EnterStatus": False,
                            "Ticketable": False,
                            "DoNotProgress": False,
                            "Attributes": {
                                "ExecType": {
                                    "StructureCode": "ExecTp$WRK",
                                    "Description": "Work",
                                },
                                "AccessLevel": 3,
                            },
                        },
                        {
                            "ShortName": "0002280",
                            "ProductInvestmentApproval": {
                                "StructureCode": "WBS27$PEND",
                                "Description": "Pending",
                            },
                            "RequestedStart": None,
                            "RequestedFinish": None,
                            "CreatedOn": "2022-05-12T12:34:24.067",
                            "CreatedBy": {
                                "UserName": "mdavis",
                                "FullName": "Miles Davis - Executive",
                            },
                            "LifecycleAdminUser": {
                                "UserName": "mdavis",
                                "FullName": "Miles Davis - Executive",
                            },
                            "IsLifecycleEnabled": True,
                            "HasLifecycle": True,
                            "StructureCode": "39507",
                            "ScheduleStart": "2017-06-05T08:00:00",
                            "ScheduleFinish": "2017-06-30T17:00:00",
                            "ScheduleDuration": 9600,
                            "ActualStart": None,
                            "ActualFinish": None,
                            "Calendar": {
                                "StructureCode": "STANDARD",
                                "Description": "Standard",
                            },
                            "Status": {
                                "StructureCode": "WBS20$REQT",
                                "Description": "Request",
                            },
                            "IsMilestone": False,
                            "Project": {
                                "StructureCode": "39507",
                                "Description": "DNT Work 2-DNT=N",
                            },
                            "Place": 34,
                            "Parent": {
                                "StructureCode": "2215",
                                "Description": "Business Applications",
                            },
                            "Description": "DNT Work 2-DNT=N",
                            "HasChildren": True,
                            "Depth": 5,
                            "ConstraintDate": None,
                            "ConstraintType": 0,
                            "ProgressAsPlanned": False,
                            "EnterStatus": False,
                            "Ticketable": False,
                            "DoNotProgress": False,
                            "Attributes": {
                                "ExecType": {
                                    "StructureCode": "ExecTp$WRK",
                                    "Description": "Work",
                                },
                                "AccessLevel": 3,
                            },
                        },
                    ],
                    "NoAccessEntities": [],
                    "MissingEntities": [],
                }
            }

        return _response_data_builder

    def test_adapt(self, response_data_builder, request_with_jwt_having_id_token):
        """Ensure that a card is converted to Work Item attributes."""

        input_data = response_data_builder()
        expected = [
            {
                "title": "Vendor e-Commerce",
                "external_type": "e1_prm",
                "container_type": "e1_strategy",
                "external_id": "1906",
                "item_type": "project",
                "state": "in_progress",
                "planned_start": "2017-06-26T08:00:00",
                "planned_finish": "2018-09-05T14:08:00",
            },
            {
                "title": "testee",
                "external_type": "e1_prm",
                "container_type": "e1_strategy",
                "external_id": "39405",
                "item_type": "Work",
                "state": "not_started",
                "planned_start": None,
                "planned_finish": None,
            },
            {
                "title": "DNT Work 2-DNT=N",
                "external_type": "e1_prm",
                "container_type": "e1_strategy",
                "external_id": "39507",
                "item_type": "Work",
                "state": "not_started",
                "planned_start": "2017-06-05T08:00:00",
                "planned_finish": "2017-06-30T17:00:00",
            },
        ]

        prepper = prepper_factory(
            request_with_jwt_having_id_token, dict(input=dict(exclude_no_access=False))
        )
        adapter = adapters.ProjectListAdapter(input_data, prepper)
        work_item_objs = adapter.adapt()

        assert work_item_objs == expected


class TestPRMUsersAdapter:
    """Ensure that the PRM user adapter returns the proper attributes."""

    def test_adapt(self):
        """Ensure that PRM response data is converted to [users]."""
        input_data = [
            {
                "UserId": "61645BC3-E742-4A40-93AF-AA220DA32B2D",
                "UserName": "myuser1",
                "FullName": "Mera User 1",
                "Email": "mu1@ok1.com",
                "Phone": "",
            },
            {
                "UserId": "ACF9D496-4EA3-4889-813D-3E012435E643",
                "UserName": "pvmaster",
                "FullName": "Planview Master User",
                "Email": "",
                "Phone": "",
            },
        ]

        expected = [
            {
                "id": "61645BC3-E742-4A40-93AF-AA220DA32B2D",
                "first_name": "Mera User 1",
                "last_name": "",
                "email_address": "mu1@ok1.com",
                "role": "user",
                "administrator": False,
            }
        ]

        adapter = adapters.UsersAdapter(input_data)
        users = adapter.adapt()
        assert users == expected
