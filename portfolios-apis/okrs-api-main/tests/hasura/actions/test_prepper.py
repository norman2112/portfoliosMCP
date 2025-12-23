import pytest

from okrs_api.api.controller.helpers import is_pvadmin_connected_okrs
from okrs_api.hasura.actions.prepper import prepper_factory
from tests.hasura.actions.action_payloads import make_payload


class TestPrepper:
    """Test input available from the InputPrepper."""

    def test_prepper_factory(self, request_with_jwt):
        """Ensure that the prepper factory builds a InputPrepper."""
        body = make_payload("search_activities")
        input_prepper = prepper_factory(request_with_jwt, body)
        assert type(input_prepper).__name__ == "InputPrepper"

    def test_prepper_app_domain(self, request_with_jwt_app_domain):
        """Ensure that prepper has app_domain."""

        body = make_payload("search_activities")
        input_prepper = prepper_factory(request_with_jwt_app_domain, body)
        assert input_prepper.app_domain == "d09.leankit.io"

    def test_prepper_connected_okrs(self, request_with_real_pvadmin_settings_jwt):
        """Ensure that prepper knows if pvadmin connected apps."""

        body = make_payload("search_activities")
        input_prepper = prepper_factory(request_with_real_pvadmin_settings_jwt, body)
        assert is_pvadmin_connected_okrs(input_prepper) is True

    def test_app_domain_with_pvadmin_token(
        self, request_with_real_pvadmin_settings_jwt
    ):
        """Ensure we don't get wrong app domain in pvadmin settings."""

        body = make_payload("search_activities")
        input_prepper = prepper_factory(request_with_real_pvadmin_settings_jwt, body)
        assert input_prepper.app_domain == ""
