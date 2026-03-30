"""Test that the validations of the inputs in openapi work as expected."""

from http import HTTPStatus
import json

import pytest


class TestOpenApiValidations:
    """Ensure validations in the openapi.yml spec work as expected."""

    @pytest.mark.parametrize(
        "domain, expected_success",
        [
            pytest.param("", False, id="blank-string"),
            pytest.param("bogus-domain", False, id="bogus-domain"),
            pytest.param("your-instance.leankit.com", True, id="good-domain"),
        ],
    )
    async def test_domain_pattern(self, connexion_client, domain, expected_success):
        """
        Update: Wed 17 May 2023 - this is no longer the case
        as we take domain name from Token and PVAdmin. We no longer use the one
        passed in action from the FE.

        Reject data that is not valid in openapi.yml.

        Since we don't actually want to run the function when we pass in
        successful inputs, we leave out the JWT here, knowing that we will
        return a 401 Unauthorized after the inputs have been validated.
        That is a "success" in this test.
        """
        request_body = {
            "input": {
                "domain": domain,
                "product_type": "leankit",
            }
        }
        response = await connexion_client.post(
            "/api/actions/search-activity-containers",
            data=json.dumps(request_body),
        )
        response_data = await response.json()
        assert response_data is not None

    @pytest.mark.parametrize(
        "external_id, expected_success",
        [
            pytest.param("", False, id="blank-string"),
            pytest.param("-bogus-external-id", False, id="bogus-external-id"),
            # pytest.param("1", True, id="good-external-id"),
        ],
    )
    async def test_external_id_pattern(
        self, connexion_client, external_id, expected_success
    ):
        """
        Reject data that is not valid in openapi.yml.
        """
        request_body = {
            "input": {
                "key_result_id": 1,
                "work_item_container": {
                    "external_id": "123",
                    "external_type": "leankit",
                },
                "work_items": [
                    {
                        "external_id": external_id,
                        "external_type": "leankit",
                    },
                ],
            }
        }
        response = await connexion_client.post(
            "/api/actions/connect-activities",
            data=json.dumps(request_body),
        )
        response_data = await response.json()

        if expected_success:
            assert response.status == HTTPStatus.UNAUTHORIZED
        else:
            assert response.status == HTTPStatus.BAD_REQUEST
            assert "does not match" in response_data["detail"]
