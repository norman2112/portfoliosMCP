"""The E1 PRM API Services."""
# pylint:disable=R0903, W0613, W0611

# from multidict import MultiDict
import asyncio

from okrs_api.hasura.actions.proxy_response import chunk_params, ChunkedResponse

API_CHUNK_SIZE = 80


class Base:
    """The E1 PRM Base. Used to access E1 API."""

    API_BASE_PATH = "/internal-api"
    PRODUCT_API = "e1_prm"
    SERVICE_PATH = ""

    def __init__(self, input_parser, client_session, api_token):
        """
        Initialize the class.

        :param InputParser input_parser: the parser for the input
        :param ClientSession client_session: the aiohttp client session
        :param str api_token: an api token for the PRM API
        """
        self.parser = input_parser
        self.client_session = client_session
        self.api_token = api_token

    def headers(self, additional_headers=None):
        """
        Return headers for the API.

        :param dict additional_headers: additional headers to use
        """
        full_headers = {"Authorization": f"Bearer {self.api_token}"}
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

        return "{scheme}://{host}{path}".format(
            scheme="https", host=self.host, path=f"{self.API_BASE_PATH}/{path}"
        )


class ProjectService(Base):
    """Services for E1 projects."""

    SERVICE_PATH = "projects"

    async def get_by_ids(self, project_ids):
        """Get the projects by IDs."""

        params = {"projectIds": project_ids, "attributeIds": ["ExecType"]}

        return await self.client_session.post(
            self.endpoint(f"{self.SERVICE_PATH}/byIds"),
            json=params,
            headers=self.headers(),
            ssl=True,
        )

    async def byIds(self, project_ids):
        """Get projects by ids."""
        if len(project_ids) > API_CHUNK_SIZE:
            # Chunk the API calls in API_CHUNK_SIZE and merge resutls
            chunks = chunk_params(project_ids, API_CHUNK_SIZE)
            print("WARNING: Chunking API calls as we have too many IDs")
            return ChunkedResponse(
                await asyncio.gather(*[self.get_by_ids(chunk) for chunk in chunks])
            )

        return await self.get_by_ids(project_ids)

    async def search(self, search_string_or_id, limit=None):
        """Search for projects by description or work id."""

        params = {"searchString": search_string_or_id}
        if limit:
            params["resultCount"] = limit

        return await self.client_session.get(
            self.endpoint(f"{self.SERVICE_PATH}/search"),
            params=params,
            headers=self.headers(),
            ssl=True,
        )


class StrategyService(Base):
    """Services for E1 strategies."""

    SERVICE_PATH = "strategies"

    async def get_by_ids(self, strategy_ids):
        """Get strategies by IDs."""

        params = {"strategyIds": strategy_ids, "attributeIds": ["Access_Level"]}
        return await self.client_session.post(
            self.endpoint(f"{self.SERVICE_PATH}/byIds"),
            json=params,
            headers=self.headers(),
            ssl=True,
        )

    async def byIds(self, strategy_ids):
        """Get strategies by ids."""

        if len(strategy_ids) > API_CHUNK_SIZE:
            # Chunk the API calls in API_CHUNK_SIZE and merge resutls
            chunks = chunk_params(strategy_ids, API_CHUNK_SIZE)
            print("WARNING: Chunking API calls as we have too many IDs")
            return ChunkedResponse(
                await asyncio.gather(*[self.get_by_ids(chunk) for chunk in chunks])
            )
        return await self.get_by_ids(strategy_ids)

    async def strategy_details(self):
        """Get strategy details for current context."""
        return await self.byIds(strategy_ids=[self.parser.context_id])


class UserService(Base):
    """Services for E1 Users."""

    SERVICE_PATH = "users"

    async def findByStrategyId(self, strategy_id, search_string=None, limit=None):
        """Get users of a strategy."""

        params = {"strategyId": strategy_id}

        if search_string:
            params["fullNameSearchText"] = search_string

        if limit:
            params["maxResults"] = limit

        return await self.client_session.get(
            self.endpoint(f"{self.SERVICE_PATH}/findByStrategyId"),
            params=params,
            headers=self.headers(),
            ssl=True,
        )
