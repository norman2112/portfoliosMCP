"""All Registration Management code for Integration Hub."""
from yarl import URL


class RegistrationManager:
    """Registration Manager for Integration Hub."""

    URL_PATH = "/inthub/api/v1/register"
    SYSTEM_CODE = "okrs"
    QUEUE_COUNT = 1

    def __init__(self, client_session, app_settings, bearer_token, tenant_parser):
        """
        Initialize the Manager.

        :param session client_session: an Aiohttp client session
        :param settings app_settings: settings for the app
        :param str bearer_token: the integration hub bearer token
        :param TenantParser tenant_parser: the tenant_parser for the the tenant_id_str
        """
        self.client_session = client_session
        self.app_settings = app_settings
        self.bearer_token = bearer_token
        self.tenant_parser = tenant_parser
        self.errors = []
        # Used for caching
        self.response = None
        self.response_data = None
        self.raw_response_data = None

    async def register(self):
        """
        Register with Integration Hub.

        This registers a queue and returns our global tenant id.
        """
        self.response = await self.client_session.post(
            self._endpoint,
            json=self.register_body,
            headers=self._headers,
        )
        self.raw_response_data = await self.response.json()

        if self.response.ok:
            self.response_data = RegistrationData(
                data=self.raw_response_data,
                okrs_tenant_id=self.tenant_parser.okrs_tenant_id,
            )
            return True
        else:
            self.errors = [
                "Could not register with Integration Hub.",
                self.response.reason,
                self._endpoint,
                str(self.raw_response_data),
            ]
            return False

    @property
    def register_body(self):
        """Return the body of the registration call to IH."""
        return {
            "systemCode": self.SYSTEM_CODE,
            "environmentId": self._environment_id(),
            "registrationId": self._adapter_id(),
            "numQueues": self.QUEUE_COUNT,
            "systemTenantIds": [self.tenant_parser.okrs_tenant_id],
            "tenantOp": "add",
        }

    @property
    def _headers(self):
        """Return the headers for the register call."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.bearer_token}",
        }

    def _adapter_id(self):
        """
        Construct the adapter ID used by Integration Hub.

        e.g. "adapter-okrs-d08"
        """
        return f"adapter-{self.SYSTEM_CODE}-{self.tenant_parser.tenant_env}"

    def _environment_id(self):
        """
        Construct the environment ID used by Integration Hub.

        e.g. "okrs-env-us-west-2"
        """
        return f"{self.SYSTEM_CODE}-env-{self._region}"

    @property
    def _region(self):
        """Return the AWS Region from the app settings."""
        return self.app_settings.region

    @property
    def _ih_settings(self):
        """Return the settings for Integration Hub."""
        return self.app_settings.integration_hub

    @property
    def _endpoint(self):
        """Return the endpoint to make the register call to."""
        return str(
            URL.build(scheme="https", host=self._ih_settings.domain, path=self.URL_PATH)
        )


class RegistrationData:
    """A data parser for the registration response data."""

    def __init__(self, data, okrs_tenant_id):
        """
        Initialize the registration data.

        :param dict data: the registration response data
        :param str okrs_tenant_id: our system tenant id for this registration
        """

        self.data = data
        self.okrs_tenant_id = okrs_tenant_id

    @property
    def global_tenant_id(self):
        """Return the global tenant id."""
        return self.all_global_tenant_ids[0]

    @property
    def all_global_tenant_ids(self):
        """All global tenant ids from the registration data."""
        return (
            self.data.get("tenantMapping")
            .get(self.okrs_tenant_id)
            .get("globalTenantIds")
            or []
        )
