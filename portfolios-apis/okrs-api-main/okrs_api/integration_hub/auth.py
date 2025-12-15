"""Handles all the authorization necessary to work with Integration Hub."""

from yarl import URL


class TokenFetcher:
    """Responsible for bearer token for authorization."""

    URL_PATH = "/inthub/api/v1/oauth2/token"

    def __init__(self, client_session, app_settings, admin=False):
        """
        Initialize the TokenFetcher.

        :param session client_session: Aiohttp client session
        :param settings app_settings: the settings for the application
        """
        self.client_session = client_session
        self.app_settings = app_settings
        self.admin = admin
        self.errors = []
        self.request_body = None
        self.endpoint = None

    async def fetch_token(self):
        """Fetch new access token."""
        response = await self.token_response()
        if response.ok:
            data = await response.json()
            return data["access_token"]

        self.errors = [
            "Could not fetch authentication token",
            response.reason,
            self._endpoint,
        ]

    async def token_response(self):
        """Return the response of the token fetch."""
        # Store the endpoint and request body for troubleshooting
        # in case there is an error later.
        self.endpoint = self._endpoint
        self.request_body = self._client_auth_data
        return await self.client_session.post(
            self._endpoint,
            data=self._client_auth_data,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    def _get_auth_by_key(self, key_name):
        """Retrieve the auth key by the correct name given the level requested."""
        key_prefix = "admin" if self.admin else None
        auth_method = "_".join(filter(None, [key_prefix, key_name]))
        return getattr(self._ih_settings, auth_method)

    @property
    def _client_auth_data(self):
        """Return the data for a client auth request."""
        return {
            "grant_type": "client_credentials",
            "client_id": self._get_auth_by_key("client_id"),
            "client_secret": self._get_auth_by_key("client_secret"),
        }

    @property
    def _ih_settings(self):
        return self.app_settings.integration_hub

    @property
    def _host(self):
        return (
            self._ih_settings.admin_domain if self.admin else self._ih_settings.domain
        )

    @property
    def _endpoint(self):
        """Return the basic endpoint for the specific request."""
        return str(URL.build(scheme="https", host=self._host, path=self.URL_PATH))
