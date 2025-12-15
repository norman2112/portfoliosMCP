"""The Leankit API Services."""
from multidict import MultiDict
from yarl import URL


class Base:
    """
    The Leankit Base. Used to access LeanKit API.

    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/01-overview
    """

    LK_API_BASE_PATH = "/io/okr"
    PRODUCT_API = "leankit"
    SERVICE_PATH = ""

    def __init__(self, input_parser, client_session, api_token):
        """
        Initialize the class.

        :param InputParser input_parser: the parser for the input
        :param ClientSession client_session: the aiohttp client session
        :param str api_token: an api token for the Leankit API
        """
        self.parser = input_parser
        self.client_session = client_session
        self.api_token = api_token

    def headers(self, additional_headers=None):
        """
        Return headers for the API.

        :param dict additional_headers: additional headers to use
        """
        full_headers = {"Authorization": f"JWT {self.api_token}"}
        if additional_headers:
            full_headers.update(additional_headers)
        return full_headers

    @property
    def host(self):
        """Return the host of the external API."""
        return self.parser.domain

    def endpoint(self, path=None):
        """Return the basic endpoint for the specific request."""
        path = path or self.SERVICE_PATH or ""
        return URL.build(
            scheme="https", host=self.host, path=f"{self.LK_API_BASE_PATH}/{path}"
        )


class CardService(Base):
    """Services for LeanKit cards."""

    SERVICE_PATH = "card"

    async def create(
        self, title, planned_start, planned_finish, external_activity_type_id
    ):
        """Create a Leankit card and return the raw response."""
        return await self.client_session.post(
            self.endpoint(),
            json={
                "boardId": self._board_id,
                "title": title,
                "plannedStart": planned_start,
                "plannedFinish": planned_finish,
                "typeId": external_activity_type_id,
            },
            headers=self.headers(),
            params={"returnFullRecord": "true"},
            ssl=True,
        )

    async def search(self, search_string, limit):
        """
        Return the raw response from the Leankit API.

        https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/card/list
        """

        params = {"board": self._board_id, "search": search_string or ""}
        if limit:
            params["limit"] = limit
        return await self.client_session.get(
            self.endpoint(), params=params, headers=self.headers(), ssl=True
        )

    async def list_cards(self, card_ids, limit, search_string=""):
        """
        Return the raw response from the Leankit API.

        https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/card/list
        """

        if not card_ids:
            card_ids = []

        params = {"cards": ",".join([str(id) for id in card_ids])}
        if limit:
            params["limit"] = limit

        if search_string:
            params["search"] = search_string

        return await self.client_session.get(
            self.endpoint(), params=params, headers=self.headers(), ssl=True
        )

    @property
    def _board_id(self):
        return self.parser.context_id


class BoardService(Base):
    """Services for LeanKit boards."""

    SERVICE_PATH = "board"

    async def search(self, search_string, limit):
        """
        Return a list of boards based on the search string.

        The result is the response object from the Leankit API.
        """

        params = {"search": search_string or ""}
        if limit:
            params["limit"] = limit
        return await self.client_session.get(
            self.endpoint(), params=params, headers=self.headers(), ssl=True
        )

    async def board_details(self):
        """
        Return the board details.

        https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/get
        """
        return await self.client_session.get(
            self.endpoint(path=f"board/{self.parser.context_id}"),
            headers=self.headers(),
            ssl=True,
        )

    async def list_boards(self, board_ids, search_string="", limit=None):
        """
        Return the board details.

        https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/list
        """

        if not board_ids:
            board_ids = []

        params = {
            "boards": ",".join([str(id) for id in board_ids]),
            "minimumAccess": 1,
            "search": search_string if search_string else "",
        }

        if limit:
            params["limit"] = limit

        return await self.client_session.get(
            self.endpoint(path="board"),
            params=params,
            headers=self.headers(),
            ssl=True,
        )

    async def search_users(self, search_string, limit, filter_access=True):
        """
        Return a list of users for the board specified.

        The result is the response object from the Leankit API.
        """

        # filter_access is a hack to get vcr tests working. VCR tests with aiohttp does not work
        # when params is a MultiDict or list of tuples. So, only from within the tests we
        # pass filter_access=False, which forces it to be a dict.
        if not filter_access:
            params = {}
        else:
            params = MultiDict()

        params["search"] = search_string or ""

        if limit:
            params["limit"] = limit

        if filter_access:
            # Restrict access to at least boardReader. Exclude users with no access.
            # https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/user-roles
            # - 0 (No Access)
            # - 1 (boardReader)
            # - 2 (boardUser)
            # - 3 (boardManager)
            # - 4 (boardAdministrator)
            for i in range(1, 5):
                params.add("roleFilterList[]", i)

        return await self.client_session.get(
            self.endpoint(path=f"board/{self.parser.context_id}/user"),
            params=params,
            headers=self.headers(),
            ssl=True,
        )


class UserService(Base):
    """Services for Leankit Users."""

    SERVICE_PATH = "user/me"

    async def info(self):
        """Return the info for the current user."""
        return await self.client_session.get(
            self.endpoint(), headers=self.headers(), ssl=True
        )
