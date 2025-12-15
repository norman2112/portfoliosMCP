"""Wrangler that determines the proper external api services and adapters."""
# pylint:disable=unused-import,too-many-instance-attributes
from http import HTTPStatus
import time
from inflection import camelize

from aiohttp.client_exceptions import ClientConnectorError

from okrs_api.external_apis.leankit import adapters as leankit_adapters  # noqa: F401
from okrs_api.service_proxies.leankit import (  # noqa: F401
    ServiceProxy as LeankitServiceProxy,
)
from okrs_api.external_apis.e1_prm import adapters as e1_prm_adapters  # noqa: F401
from okrs_api.service_proxies.e1_prm import (  # noqa: F401
    ServiceProxy as E1PrmServiceProxy,
)
from okrs_api.external_apis.work import adapters as work_adapters  # noqa: F401
from okrs_api.service_proxies.work import (  # noqa: F401
    ServiceProxy as WorkServiceProxy,
)
from okrs_api.hasura.actions.proxy_response import ProxyResponseWrapper
from okrs_api.api.controller.helpers import get_wrangler_product_type


def service_wrangler_factory(
    input_prepper,
    adapter_kwargs=None,
    override_action=None,
    product_type=None,
    domain=None,
):
    """
    Create the service wrangler needed for the action provided.

    This factory dynamically determines the service proxy and the adapters
    module from the `product_type`. You must ensure that any service proxies
    and adapter modules are imported into this file for this to work properly.

    For this reason, it is important that the `product_type` be limited
    to a strict set of values in the `openapi.yml` file.
    """
    input_product_type = get_wrangler_product_type(input_prepper)
    product_type = product_type if product_type else input_product_type
    if product_type == "e1_work":
        product_type = "work"
    service_proxy_name = f"{camelize(product_type)}ServiceProxy"
    adapter_module_name = f"{product_type}_adapters"
    if domain:
        input_prepper.input_parser.domain = domain

    service_proxy = globals()[service_proxy_name](input_prepper)
    adapters_module = globals()[adapter_module_name]
    return ServiceWrangler(
        action_name=override_action if override_action else input_prepper.action_name,
        service_proxy=service_proxy,
        adapters_module=adapters_module,
        input_prepper=input_prepper,
        adapter_kwargs=adapter_kwargs,
    )


# pylint:disable=too-many-arguments


class ServiceWrangler:
    """
    The service wrangler calls external apis and adapts the responses.

    It is responsible for:
    1. Selecting the appropriate external API service and calling it.
    2. Selecting the appropriate adapter to adapt the external API return data.
    3. Reporting any errors that come back from that external API service.
    """

    def __init__(
        self,
        action_name,
        service_proxy,
        adapters_module,
        input_prepper=None,
        adapter_kwargs=None,
    ):
        """
        Initialize the data for this service wrangler.

        :param str action_name: the name of the controller/hasura action
        :param ServiceProxy service_proxy: a proxy to the specific external api
        :param module adapters_module: the module containing the correct adapters
        :param InputPrepper input_prepper: the input prepper
        """

        self.action_name = action_name
        self.service_proxy = service_proxy
        self.adapters_module = adapters_module
        self.input_prepper = input_prepper
        self.adapter_kwargs = adapter_kwargs
        # Caching
        self.response = None
        self.adapted_data = None
        self.response_status = None
        self.request_urls = None

    async def call_service(self):
        """
        Call the service proxy.

        Cache the response, adapted_data, and response_status

        Return a tuple of the (response data, response status)
        """
        action_func = getattr(self.service_proxy, self.action_name)
        try:
            start = time.monotonic()
            proxy_response = await action_func()
            self.response = ProxyResponseWrapper(proxy_response)
            self.request_urls = self.response.request_urls()
            response_time = time.monotonic() - start
            print(f"{self.request_urls}  - {response_time}")
        except ClientConnectorError as e:
            print(f"External API error: {self.request_urls}  - {e}")
            return (
                {"errors": [f"Could not connect to external API: {e}"]},
                HTTPStatus.GATEWAY_TIMEOUT,
            )
        self.response_status = self.response.status_to_return()
        try:
            response_data = await self.response.response_data()
        except Exception as ex:
            print("WARNING: Response data error:", ex)
            response_data = {}
        if self.response.ok():
            self.adapted_data = self._adapt_data(response_data=response_data)
        else:
            self.adapted_data = self._adapt_errors(
                response_data=response_data, reason=self.response.reasons()
            )
        return (self.adapted_data, self.response_status)

    @property
    def action_was_successful(self):
        """Return True if the response exists and was ok."""
        return self.response and self.response.ok

    def _adapt_data(self, response_data):
        """Adapt successful data."""
        launcher_instance = getattr(self.adapters_module, "AdapterLauncher")(
            response_data=response_data,
            input_prepper=self.input_prepper,
            adapter_kwargs=self.adapter_kwargs,
        )
        adapter_func = getattr(launcher_instance, self.action_name)
        return adapter_func()

    def _adapt_errors(self, response_data, reason=None):
        adapter_func = getattr(self.adapters_module, "errors")
        custom_errors = [f"Failure from external api ({self.action_name})."]
        for request_url in self.request_urls:
            custom_errors.append(f"External API: {request_url}")
        return adapter_func(response_data, custom_errors, reason) or {}
