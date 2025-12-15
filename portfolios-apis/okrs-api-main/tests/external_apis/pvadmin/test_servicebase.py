"""Test the PVID Service Base class."""

import pytest

from okrs_api.external_apis.pvadmin.services import PVAdminServiceBase
from okrs_api.hasura.actions.prepper import prepper_factory
from tests.conftest import (
    request_with_jwt,
    request_with_jwt_having_admin_url,
    request_with_jwt_having_admin_url_https,
)
from tests.hasura.actions.action_payloads import make_payload


@pytest.fixture
def input_prepper(request_with_jwt):
    """Make an input prepper."""

    body = make_payload("search_users")
    input_prepper = prepper_factory(request_with_jwt, body)
    return input_prepper


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


def test_empty_planview_admin_url(input_prepper):
    """Test None endpoint of service base."""

    service_base = PVAdminServiceBase(input_prepper)
    try:
        service_base.endpoint()
    except ValueError as err:
        assert str(err) == "Cannot call API without a valid planview_admin_url"


def test_planview_admin_url(input_prepper_with_url):
    """Test existing endpoint of service base."""

    service_base = PVAdminServiceBase(input_prepper_with_url)
    assert service_base.planview_admin_url == "pvid.somesite.planview.com"


def test_planview_admin_url_https(input_prepper_with_url_https):
    """Test existing endpoint of service base."""

    service_base = PVAdminServiceBase(input_prepper_with_url_https)
    assert service_base.planview_admin_url == "https://pvid.somesite.planview.com"
