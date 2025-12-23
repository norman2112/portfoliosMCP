from http import HTTPStatus

import pytest

from okrs_api.hasura.actions.prepper import prepper_factory
from okrs_api.hasura.actions.service_wranglers import service_wrangler_factory
from tests.hasura.actions.action_payloads import make_payload

REQUIRED_CONTROLLER_NAMES = [
    "create_activity",
    "current_user",
    "list_activity_types",
    "search_activities",
    "search_activity_containers",
    "search_users",
]

# Right now, there is only one we are testing.
PRODUCT_TYPES = ["leankit"]


class TestServiceWrangler:
    """Ensure ServiceWrangler and factory work properly."""

    def make_service_wrangler(self, action_name, request, product_type=None):
        """A way to make a service wrangler and input prepper for tests."""
        input_merge = None
        if product_type:
            input_merge = {"product_type": product_type}
        body = make_payload(action_name, input_merge=input_merge)
        input_prepper = prepper_factory(request, body)
        return service_wrangler_factory(input_prepper)

    @pytest.mark.parametrize(
        "action_name, product_type",
        [
            pytest.param(
                controller_name, product_type, id=f"{product_type}-{controller_name}"
            )
            for controller_name in REQUIRED_CONTROLLER_NAMES
            for product_type in PRODUCT_TYPES
        ],
    )
    def test_service_wrangler_factory(
        self, request_with_jwt, action_name, product_type
    ):
        """
        Ensure that a service wrangler is created from the factory.

        This will also ensure that the wrangler has access to all required
        methods for the service proxy and the adapters.
        """
        service_wrangler = self.make_service_wrangler(
            action_name, request_with_jwt, product_type
        )
        service_proxy = service_wrangler.service_proxy
        adapters_module = service_wrangler.adapters_module
        launcher = getattr(adapters_module, "AdapterLauncher")({})
        assert type(service_proxy).__name__ == "ServiceProxy"
        assert type(adapters_module).__name__ == "module"
        assert hasattr(launcher, action_name)
        assert hasattr(service_proxy, action_name)

    async def test_service_wrangler_request_on_error(self, mocker, request_with_jwt):
        """Ensure that the external api request url is returned with the errors."""
        external_api_url = "https://d08.leankit.io/okrs/io/card"
        service_wrangler = self.make_service_wrangler(
            "search_activities", request_with_jwt
        )
        mocker.patch(
            "okrs_api.service_proxies.leankit.ServiceProxy.search_activities",
            return_value=mocker.AsyncMock(
                json=mocker.AsyncMock(
                    return_value={"message": "Search criteria missing"}
                ),
                ok=False,
                request_info=mocker.Mock(url=external_api_url),
                status=HTTPStatus.UNPROCESSABLE_ENTITY,
                reason="Missing parameters",
            ),
        )
        adapted_response, status = await service_wrangler.call_service()
        assert service_wrangler.request_urls == [external_api_url]
        assert f"External API: {external_api_url}" in adapted_response["errors"]
