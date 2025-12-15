"""Test the leankit API service."""
from http import HTTPStatus
import pytest

from okrs_api.external_apis.leankit.services import (
    BoardService,
    CardService,
    UserService,
)
from okrs_api import utils


# D08 User and Board ID
# LK_DOMAIN = "d08.leankit.io"
# LK_USER_ID = "10121496032"
# CONTEXT_ID = "10121496436"
# CARD_TYPE_ID = "10121496438"

# D09 User and Board ID
LK_DOMAIN = "d09.leankit.io"
LK_USER_ID = "10145734719"
CONTEXT_ID = "10136408886"
CARD_TYPE_ID = "10136408888"


@pytest.fixture()
def planview_token_service_token(app_settings):
    """
    Return your PTS token you have specified in your ENV.

    This token is supplied only for local testing and cannot be accessed in
    any other environment other than Local.
    """
    return app_settings.local_test.planview_token_service_jwt or ""


class TestCardService:

    """Test the Card Service of the Leankit API."""

    BASE_INPUT_DATA = {
        "context_id": CONTEXT_ID,
        "domain": LK_DOMAIN,
        "product_type": "leankit",
    }

    @pytest.fixture
    def card_service(self, connexion_client, planview_token_service_token):
        """Return an instance of the LeanKit API Service."""

        input_parser = utils.Map(**self.BASE_INPUT_DATA)
        return CardService(
            input_parser=input_parser,
            client_session=connexion_client.session,
            api_token=planview_token_service_token,
        )

    @pytest.mark.vcr()
    async def test_create(self, card_service):
        """Ensure the application creates a new card."""
        response = await card_service.create(
            title="[TEST] Petting Zoo Field Trip",
            planned_start="2020-01-01",
            planned_finish="2021-01-01",
            external_activity_type_id=CARD_TYPE_ID,
        )
        data = await response.json()
        activity_id = data["id"]
        assert response.status == HTTPStatus.CREATED
        assert activity_id.isnumeric()

    @pytest.mark.vcr()
    async def test_search(self, card_service):
        """Ensure the application retrieves the correct data from GET endpoints."""
        response = await card_service.search("TEST", None)
        text = await response.text()
        assert response.status == 200
        assert "Petting Zoo" in text


class TestBoardService:
    """Test the Board Service of the Leankit API."""

    BASE_INPUT_DATA = {
        "domain": LK_DOMAIN,
        "product_type": "leankit",
    }

    @pytest.fixture
    def board_service(self, connexion_client):
        """
        Return an instance of the LeanKit API Service.

        :param InputParserBase input_parser: the parser
        :param str api_token: the token for Leankit API
        """

        def _board_service(input_parser, api_token):
            return BoardService(
                input_parser=input_parser,
                client_session=connexion_client.session,
                api_token=api_token,
            )

        # Return the function only, to have the input_parser argument supplied
        # by the calling function.
        return _board_service

    @pytest.mark.vcr()
    async def test_search(self, board_service, planview_token_service_token):
        """Ensure the application retrieves the correct data from GET endpoints."""
        input_parser = utils.Map(**self.BASE_INPUT_DATA)
        response = await board_service(
            input_parser, planview_token_service_token
        ).search("Test", None)
        text = await response.text()
        assert response.status == 200
        assert "Test Board" in text

    @pytest.mark.vcr()
    async def test_board_details(self, board_service, planview_token_service_token):
        """Ensure the application retrieves the correct data from GET endpoints."""
        input_data = {**self.BASE_INPUT_DATA, "context_id": CONTEXT_ID}
        input_parser = utils.Map(**input_data)

        response = await board_service(
            input_parser, planview_token_service_token
        ).board_details()
        assert response.status == 200

        response_data = await response.json()
        card_types = [cardType["name"] for cardType in response_data["cardTypes"]]
        assert "Other Work" in card_types

    @pytest.mark.vcr()
    async def test_search_users(self, board_service, planview_token_service_token):
        """Ensure the application retrieves the correct data from GET endpoints."""
        input_data = {**self.BASE_INPUT_DATA, "context_id": CONTEXT_ID}
        input_parser = utils.Map(**input_data)
        response = await board_service(
            input_parser, planview_token_service_token
        ).search_users("", None, filter_access=False)
        data = await response.json()
        assert response.status == 200
        assert data["pageMeta"]["totalRecords"]


class TestUserService:
    """Ensure the User Service works."""

    BASE_INPUT_DATA = {
        "domain": LK_DOMAIN,
        "product_type": "leankit",
    }

    @pytest.fixture
    def user_service(self, connexion_client):
        """
        Return an instance of the LeanKit API Service.

        :param InputParserBase input_parser: the parser
        """

        def _user_service(input_parser, api_token):
            return UserService(
                input_parser=input_parser,
                client_session=connexion_client.session,
                api_token=api_token,
            )

        # Return the function only, to have the input_parser argument supplied
        # by the calling function.
        return _user_service

    @pytest.mark.vcr()
    async def test_info(self, user_service, planview_token_service_token):
        """Ensure that user info is returned."""
        input_parser = utils.Map(**self.BASE_INPUT_DATA)
        response = await user_service(input_parser, planview_token_service_token).info()

        assert response.status == 200

        response_data = await response.json()
        assert response_data.get("id").isnumeric()
