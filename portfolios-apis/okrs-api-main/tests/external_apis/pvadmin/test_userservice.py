"""Test the PVID Service Base class."""

import pytest

from okrs_api.external_apis.pvadmin.services import PVAdminUserService
from okrs_api.hasura.actions.prepper import prepper_factory
from tests.conftest import (
    request_with_jwt_having_admin_url,
    request_with_jwt_having_admin_url_https,
    request_with_jwt_having_id_token,
)
from tests.hasura.actions.action_payloads import make_payload


@pytest.fixture
def input_prepper_with_url(request_with_jwt_having_admin_url):
    """Make an input prepper."""

    body = make_payload("search_users")
    input_prepper = prepper_factory(request_with_jwt_having_admin_url, body)
    return input_prepper


@pytest.fixture
def input_prepper_with_url_https(request_with_jwt_having_admin_url_https):
    """Make an input prepper."""

    body = make_payload("search_users")
    input_prepper = prepper_factory(request_with_jwt_having_admin_url_https, body)
    return input_prepper


@pytest.fixture
def input_prepper_with_id_token(request_with_jwt_having_id_token):
    """Make an input prepper"""

    body = make_payload("search_users")
    input_prepper = prepper_factory(request_with_jwt_having_id_token, body)
    return input_prepper


def test_user_service_endpoint(input_prepper_with_url):
    service = PVAdminUserService(input_prepper_with_url)
    assert (
        str(service.endpoint()) == "https://pvid.somesite.planview.com/io/v1/user/map"
    )


def test_user_service_endpoint_https(input_prepper_with_url_https):
    service = PVAdminUserService(input_prepper_with_url_https)
    assert (
        str(service.endpoint()) == "https://pvid.somesite.planview.com/io/v1/user/map"
    )


def test_user_service_endpoint_with_actual_token(input_prepper_with_id_token):
    service = PVAdminUserService(input_prepper_with_id_token)
    assert (
        str(service.endpoint()) == "https://us.id.planviewlogindev.net/io/v1/user/map"
    )


# async def test_user_service_response(input_prepper_with_id_token):
#     service = PVAdminUserService(input_prepper_with_id_token)
#     response = await service.planview_user_ids(["admin_non_saml_user"])
#     assert response.ok == False
