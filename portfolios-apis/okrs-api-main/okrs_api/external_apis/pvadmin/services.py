"""The Planview Admin Services APIs."""

import json
from yarl import URL


class PVAdminServiceBase:
    """The base class for PVID services."""

    def __init__(self, input_prepper):
        """
        Initialize the class.

        :param InputParser input_parser: the parser for the input
        :param ClientSession client_session: the aiohttp client session
        :param str api_token: an api token for the Leankit API
        """
        self.client_session = input_prepper.client_session
        self.planview_admin_url = input_prepper.planview_admin_url
        self.api_token = input_prepper.hasura_jwt

    def get_api_url(self):
        """Get the API url path."""
        raise NotImplementedError("Implement this in a child class")

    def endpoint(self, path=None):
        """Build the complete URL."""
        if not self.planview_admin_url:
            raise ValueError("Cannot call API without a valid planview_admin_url")

        path = path or self.get_api_url()

        if self.planview_admin_url.startswith("https:"):
            if path.startswith("/"):
                path = path[1:]
            return URL(self.planview_admin_url) / path

        return URL.build(scheme="https", host=self.planview_admin_url, path=path)

    def auth_type(self):
        """Get the auth type string - Bearer, JWT etc."""
        return "Bearer"

    def headers(self, **additional_headers):
        """Build the header for api request."""
        all_headers = {
            "Authorization": f"{self.auth_type()} {self.api_token}",
            "Content-Type": "application/json",
        }
        all_headers.update(additional_headers)

        return all_headers


class PVAdminUserService(PVAdminServiceBase):
    """Invoke planview admin api service and retrieve the user maps."""

    def get_api_url(self):
        """Overwrite to return the user API path."""

        return "/io/v1/user/map"

    async def planview_user_ids(self, tenant_user_ids, env_selector=None):
        """Call user API to retrieve planview_user_ids."""

        params_dict = dict(userIds=tenant_user_ids)
        if env_selector:
            params_dict["envSelector"] = env_selector
        params = json.dumps(params_dict)
        return await self.client_session.post(
            self.endpoint(), data=params, headers=self.headers(), ssl=True
        )

    async def planview_user_details(self, pv_user_id):
        """Call user detail API to retrieve details of the users."""

        path = f"/io/v1/user/info/{pv_user_id}"
        return await self.client_session.get(
            self.endpoint(path=path), headers=self.headers(), ssl=True
        )

    async def planview_user_current_details(self):
        """Call current user API to retrieve app names for the user."""

        path = "/io/v1/user/current"
        return await self.client_session.get(
            self.endpoint(path=path), headers=self.headers(), ssl=True
        )
