"""Leankit Proxy for specific controller actions that require external apis."""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    wait_random,
)

from okrs_api.external_apis.leankit import services


class ExternalAPIError(Exception):
    """Raised when the External API is not available."""


SERVICE_PRODUCT_TYPE = "leankit"


class ServiceProxy:
    """
    A proxy to adapt input and call the appropriate LeanKit service.

    Any call to Leankit API from a controller in the actions should go
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
        Call the leankit card service create.

        Also call the leankit board service and return that response as well.
        The adapter will need the board response in order to determine what the
        lane is.
        """
        card_service = self._service_factory("Card")
        board_response = await self._board_details()
        card_response = await card_service.create(
            title=self.input_parser.title,
            planned_start=self.input_parser.planned_start,
            planned_finish=self.input_parser.planned_finish,
            external_activity_type_id=self.input_parser.external_activity_type_id,
        )
        if response_is_server_error(card_response):
            raise ExternalAPIError(card_response)

        return {
            "board_details": board_response,
            "card_details": card_response,
        }

    async def current_user(self):
        """Call `info` on the leankit UserService."""
        user_service = self._service_factory("User")
        return await user_service.info()

    async def list_activity_types(self):
        """Call the leankit board service list activity types."""
        return await self._board_details()

    async def search_activities(self):
        """Call the leankit card service search."""
        board_details_response = await self._board_details()
        card_service = self._service_factory("Card")
        card_list_response = await card_service.search(
            search_string=self.input_parser.search_string, limit=self.input_parser.limit
        )
        #  Return a multi-response dict back to the service wrangler.
        return {
            "board_details": board_details_response,
            "card_list": card_list_response,
        }

    async def list_activities(self):
        """Call the leankit card service for listing cards."""
        card_service = self._service_factory("Card")
        card_list_response = await card_service.list_cards(
            card_ids=self.input_parser.activity_ids,
            limit=self.input_parser.limit,
            search_string=self.input_parser.search_string,
        )
        return {
            "card_list": card_list_response,
        }

    async def search_activity_containers(self):
        """Call the leankit board service search."""
        board_service = self._service_factory("Board")
        return await board_service.search(
            search_string=self.input_parser.search_string, limit=self.input_parser.limit
        )

    async def list_activity_containers(self):
        """Call the leankit board list service."""
        board_service = self._service_factory("Board")
        return await board_service.list_boards(
            board_ids=self.input_parser.container_ids,
            search_string=self.input_parser.search_string,
            limit=self.input_parser.limit,
        )

    async def search_users(self):
        """Call the leankit board service users endpoint."""
        board_service = self._service_factory("Board")
        return await board_service.search_users(
            search_string=self.input_parser.search_string, limit=self.input_parser.limit
        )

    def _get_api_token(self):
        """Generate api token if necessary."""

        # Since e1_prm token works in leankit, we don't generate a token yet
        return self.input_prepper.hasura_jwt

    def _service_factory(self, service_name):
        """Return the appropriate Leankit API Service."""
        return getattr(services, f"{service_name}Service")(
            input_parser=self.input_parser,
            client_session=self.client_session,
            api_token=self._get_api_token(),
        )

    async def _board_details(self):
        """
        Return the board details response.

        Some of the proxy services also require an additional set of board details.
        This private method allows us to retrieve that response.
        """
        board_service = self._service_factory("Board")
        return await board_service.board_details()


def response_is_server_error(response):
    """
    Determine if response is any kind of server/timeout error (e.g 5xx or 408).

    This function is for use by our Tenacity retry mechanism.
    https://tenacity.readthedocs.io/en/latest/

    :param webResponse response: a web response from the external api
    """
    return response.status >= 500 or response.status == 408
