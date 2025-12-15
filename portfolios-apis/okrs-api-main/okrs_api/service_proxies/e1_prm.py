"""E1 PRM Proxy for specific controller actions that require external apis."""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    wait_random,
)

from okrs_api.external_apis.e1_prm import services

# from okrs_api.hasura.actions.auth import OKRTokenGenerator
from okrs_api.hasura.actions.auth import OKRTokenGenerator


class ExternalAPIError(Exception):
    """Raised when the External API is not available."""


SERVICE_PRODUCT_TYPE = "e1_prm"


class ServiceProxy:
    """
    A proxy to adapt input and call the appropriate E1 PRM service.

    Any call to E1 PRM API from a controller in the actions should go
    through this proxy.

    The functions in this proxy should exactly match the name of the controller
    endpoint that called it.
    """

    def __init__(self, input_prepper):
        """
        Initialize the service proxy.

        :param InputPrepper input_prepper:
        """
        self.input_prepper = input_prepper
        self.input_parser = input_prepper.input_parser
        self.client_session = input_prepper.client_session

    @retry(
        wait=wait_fixed(3) + wait_random(0, 2),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(ExternalAPIError),
    )
    async def create_activity(self):
        """
        Call the E1 project creation service.

        Currently we do not allow project creation from OKR screen.
        """
        raise ValueError("This operation is not supported")

    async def current_user(self):
        """Call `info` on the E1 User Service."""

        # 1. Get the context IDs
        # 2. Get all strategies by IDs
        # 4. Get user related info from that and put it is "user_info"
        # 5. Put strategies in "strategy_info"
        # 6. Pass to adapter

        strategy_service = self._service_factory("Strategy")

        if (not self.input_parser.context_ids) or (
            self.input_parser.context_ids and len(self.input_parser.context_ids) == 0
        ):
            raise ValueError("One or more context IDs must be passed")

        strategies_info = await strategy_service.byIds(self.input_parser.context_ids)
        # print("+++++ Proxy logs +++++")
        # print(dict(input_prepper=self.input_prepper, response=strategies_info))
        return {"strategies_info": strategies_info}

    async def list_activity_types(self):
        """Call the E1 strategy service list activity types."""
        raise ValueError("This operation is not supported")

    async def search_activities(self):
        """Call the E1 project service search."""
        project_service = self._service_factory("Project")
        project_search_response = await project_service.search(
            search_string_or_id=self.input_parser.search_string,
            limit=self.input_parser.limit,
        )
        search_results = await project_search_response.json()
        project_ids = [response["StructureCode"] for response in search_results][0:10]

        project_list_response = await project_service.byIds(project_ids=project_ids)
        return {
            "project_details": project_list_response,
        }

    async def search_activity_containers(self):
        """Call the E1 strategy service search. This will not be supported action from FE."""
        strategy_service = self._service_factory("Strategy")
        strategy_service = await strategy_service.byIds(strategy_ids=[])
        return {
            "strategy_service": strategy_service,
        }

    async def list_activity_containers(self):
        """Call the PRM strategy list service."""
        strategy_service = self._service_factory("Strategy")
        return await strategy_service.byIds(
            strategy_ids=self.input_parser.container_ids
        )

    async def list_activities(self):
        """Call the PRM project service for listing projects."""
        project_service = self._service_factory("Project")
        project_list_response = await project_service.byIds(
            project_ids=self.input_parser.activity_ids
        )
        return {"project_details": project_list_response}

    async def search_users(self):
        """Call the E1 strategy service users endpoint."""
        users_service = self._service_factory("User")
        return await users_service.findByStrategyId(
            strategy_id=self.input_parser.context_id,
            search_string=self.input_parser.search_string,
            limit=self.input_parser.limit,
        )

    def _get_api_token(self):
        """Generate api token if necessary."""
        if self.input_prepper.app_name != SERVICE_PRODUCT_TYPE:
            print(
                "Generating cross app token for {} from {}".format(
                    SERVICE_PRODUCT_TYPE, self.input_prepper.app_name
                )
            )
            try:
                token_generator = OKRTokenGenerator(
                    self.input_prepper, SERVICE_PRODUCT_TYPE
                )
                new_token = token_generator.generate_token()
                # print("CROSS APP TOKEN +++++++ ", new_token)
                return new_token
            except BaseException as ex:
                print("Error generating token:", str(ex))
                return self.input_prepper.hasura_jwt
            print("Generated token")

        return self.input_prepper.hasura_jwt

    def _service_factory(self, service_name):
        """Return the appropriate E1 PRM API Service."""
        return getattr(services, f"{service_name}Service")(
            input_parser=self.input_parser,
            client_session=self.client_session,
            api_token=self._get_api_token(),
        )


def response_is_server_error(response):
    """
    Determine if response is any kind of server/timeout error (e.g 5xx or 408).

    This function is for use by our Tenacity retry mechanism.
    https://tenacity.readthedocs.io/en/latest/

    :param webResponse response: a web response from the external api
    """
    return response.status >= 500 or response.status == 408
