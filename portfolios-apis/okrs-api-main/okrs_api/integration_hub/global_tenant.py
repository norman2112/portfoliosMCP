"""Regarding all GlobalTenant operations."""
from yarl import URL


class GlobalTenantBase:
    """BaseClass for the GlobalTenant classes."""

    def __init__(self, admin_auth_token, tenant_parser, app_settings, client_session):
        """
        Initialize the Global Tenant Base class.

        :param str admin_auth_token: an auth token for integration hub
        :param TenantParser tenant_parser:
        :params dict app_settings:
        :params (AIOHttp session) client_session:
        """
        self.admin_auth_token = admin_auth_token
        self.tenant_parser = tenant_parser
        self.app_settings = app_settings
        self.client_session = client_session

    @property
    def url_path(self):
        """Return the URL Path for the request."""
        raise NotImplementedError("You must provide a URL_PATH in order to work.")

    @property
    def headers(self):
        """Return headers for the API."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.admin_auth_token}",
        }

    @property
    def _ih_settings(self):
        return self.app_settings.integration_hub

    def _endpoint(self, query_params=None):
        """
        Return the basic endpoint for the specific request.

        Implement the `URL_PATH` in your child class in order
        to allow this to function.

        :param dict query_params: query params for the url, if any
        """
        return str(
            URL.build(
                scheme="https",
                host=self._ih_settings.admin_domain,
                path=self.url_path,
                query=query_params,
            )
        )

    @property
    def region(self):
        """Return the application settings region."""
        return self.app_settings.region

    @property
    def okrs_environment_id(self):
        """Return the okrs environment id."""
        return f"okrs-env-{self.region}"

    @property
    def okrs_system_code(self):
        """Return the okrs system code."""
        return self.tenant_parser.OKRS_SYSTEM_CODE

    @property
    def okrs_system_tenant_id(self):
        """Return the okrs_system_tenant_id."""
        return self.tenant_parser.okrs_tenant_id


class GlobalTenantFinder(GlobalTenantBase):
    """
    Finder for global tenant ids.

    The response from the finder might be different in the development
    environment than the other environments. As such, the response is parsed
    both ways.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the Global Tenant Finder."""
        super().__init__(*args, **kwargs)
        self._response_data = {}

    async def find_existing(self):
        """
        Look for an existing global tenant id.

        We must perform [up to] two searches for the global tenant id.

        Search 1 - looking for an existing global tenant id based on an "okrs"
        systemTenantId.

        The curl version of this request is as follows:

        ```
        curl --location --request GET \
        'https://prod.pvintegrations.net/inthub/admin/api/v1/deployments \
        /find?systemCode=okrs&environmentId=okrs-env-<region>& \
        systemTenantId=okrs-<env>-<numeric_portion_of_tenant_id_str>' \
            --header 'Authorization: Bearer <prod_admin_token>'
        ```

        Search 2 - looking for an existing global tenant id based on a "leankit"
        systemTenantId.

        This will be called if we can't find a global tenant id in Search 1.

        ```
        curl --location --request GET
        https://prod.pvintegrations.net/inthub/admin/api/v1/deployments \
        /find?systemCode=lk&environmentId=<lk-region>& \
        systemTenantId=<numeric_portion_of_tenant_id_str>
        ```

        Will set the `_response_data` on success to the first entry in the
        list.

        """
        for query_params in [self._okr_query_params, self._leankit_query_params]:
            response = await self.client_session.get(
                self._endpoint(query_params=query_params),
                headers=self.headers,
            )
            if response.ok:
                # An OK response means that a global tenant id was found.
                data = await response.json()
                if isinstance(data, list):
                    self._response_data = data[0] if data else None
                elif isinstance(data, dict):
                    self._response_data = data["data"][0]

                # We set the self._response_data above, from which the
                # self.global_tenant_id will be found. If found, return.
                if self.global_tenant_id:
                    return self.global_tenant_id

    @property
    def url_path(self):
        """Return the url path."""
        return "/inthub/admin/api/v1/deployments/find"

    @property
    def global_tenant_id(self):
        """
        Return the global tenant id.

        The global tenant id is parsed from the response data.
        Since the response data might be different, depending on the IH
        environment, we accommodate for either response.
        """
        global_tenant_list = self._response_data.get(
            "globalTenantId"
        ) or self._response_data.get("globalTenantIds")
        return global_tenant_list[0] if global_tenant_list else None

    @property
    def response_system_code(self):
        """Return the systemCode of the response data."""
        return self._response_data.get("systemCode") or self._response_data.get(
            "integratedDeployment"
        ).get("systemCode")

    @property
    def response_environment_id(self):
        """Return the environmentId of the response data."""
        return self._response_data.get("environmentId") or self._response_data.get(
            "integratedDeployment"
        ).get("environmentId")

    @property
    def response_tenant_id(self):
        """Return the systemTenantId of the response data."""
        return self._response_data.get("systemTenantId") or self._response_data.get(
            "integratedDeployment"
        ).get("systemTenantId")

    def okr_tenant_exists(self):
        """
        Check the existing integrated deployment (mapping).

        If an integrated deployment already exists:
            - verify that the mapping is indeed a correct okrs tenant mapping,
            or throw an error.
            - return True
        If an integrated deployment does NOT already exist:
            - return False

        An example result:
        [
            {
                "systemCode": "okrs",
                "environmentId": "okrs-env-us-west-2",
                "systemTenantId": "okrs-d08-10100000101",
                "globalTenantId": ["74ef27c7-aa51-40ca-ace6-78efdd2e40b3"]
            }
        ]
        """

        if self.response_system_code != self.tenant_parser.OKRS_SYSTEM_CODE:
            return False

        response_mapping_info = (self.response_environment_id, self.response_tenant_id)
        expected_mapping_info = (self.okrs_environment_id, self.okrs_system_tenant_id)
        assert response_mapping_info == expected_mapping_info
        return True

    @property
    def _okr_query_params(self):
        """Return the okr system tenant query params as a dict."""
        # ?systemCode=okrs&environmentId=okrs-env-<region>& \
        #  systemTenantId=okrs-<env>-<numeric_portion_of_tenant_id_str>'
        return {
            "systemCode": self.okrs_system_code,
            "environmentId": self.okrs_environment_id,
            "systemTenantId": self.okrs_system_tenant_id,
        }

    @property
    def _leankit_query_params(self):
        """Return the leankit system tenant query params as a dict."""
        #  ?systemCode=lk&environmentId=<lk-region>& \
        #   systemTenantId=<numeric_portion_of_tenant_id_str>
        return {
            "systemCode": self.tenant_parser.app_system_code,
            "environmentId": self.tenant_parser.tenant_env,
            "systemTenantId": self.tenant_parser.tenant_id,
        }


class GlobalTenantUpdater(GlobalTenantBase):
    """Creation of the global tenant mappings."""

    def __init__(self, global_tenant_id, *args, **kwargs):
        """Initialize this class."""
        self.global_tenant_id = global_tenant_id
        super().__init__(*args, **kwargs)

    @property
    def url_path(self):
        """Return the URL path."""
        return f"/inthub/admin/api/v1/tenants/{self.global_tenant_id}"

    async def update(self):
        """
        Update a mapping for an existing global tenant id.

        Return the global tenant id on success.

        This is a curl example of the request:
        curl --location --request PATCH
        'https://prod.pvintegrations.net/inthub/admin/ \
        api/v1/tenants/<globalTenantId>' \
        --header 'Content-Type: application/json-patch+json' \
        --header 'Authorization: Bearer <prod_admin_token>' \
        --data-raw '[
            {
                "op": "add",
                "path": "/integratedDeployments/-",
                "value": {
                    "systemCode": "okrs",
                    "environmentId": "okrs-env-<region>",
                    "systemTenantId": "okrs-<env>-<numeric_portion_of_tenant_id_str>"
                }
            }
        ]'

        """
        response = await self.client_session.patch(
            self._endpoint(),
            json=[
                {
                    "op": "add",
                    "path": "/integratedDeployments/-",
                    "value": {
                        "systemCode": self.okrs_system_code,
                        "environmentId": self.okrs_environment_id,
                        "systemTenantId": self.okrs_system_tenant_id,
                    },
                }
            ],
            headers=self.headers,
        )
        if response.ok:
            data = await response.json()
            return data["globalTenantId"]

        raise Exception(
            "Could not update the mapping for the global tenant id "
            f"{self.global_tenant_id}"
        )


class GlobalTenantCreator(GlobalTenantBase):
    """Create a global tenant id."""

    @property
    def url_path(self):
        """Return the url path for creation of a new global tenant."""
        return "/inthub/admin/api/v1/tenants"

    async def create(self):
        """
        Create a new global tenant.

        Curl example:

        curl --location --request POST
        'https://prod.pvintegrations.net/inthub/admin/api/v1/tenants' \
        --header 'Authorization: Bearer <prod_admin_token>' \
        --header 'Content-Type: application/json' \
        --data-raw '{
          "data": [
            {
              "tenantName": "<customer_name>",
              "integratedDeployments": [
                {
                  "systemCode": "okrs",
                  "environmentId": "okrs-env-<region>",
                  "systemTenantId": "okrs-<env>-<numeric_portion_of_tenant_id_str>"
                },
                {
                  "systemCode": "lk",
                  "environmentId": "<env>",
                  "systemTenantId": "<numeric_portion_of_tenant_id_str>"
                }
              ]
            }
          ]
        }'
        """
        response = await self.client_session.post(
            self._endpoint(),
            json=self._request_body,
            headers=self.headers,
        )
        if response.ok:
            data = await response.json()
            return data["data"][0]["globalTenantId"]

        raise Exception("Could not create a global tenant id.")

    @property
    def _request_body(self):
        return {
            "data": [
                {
                    "tenantName": "okrs-customer",
                    "integratedDeployments": [
                        {
                            "systemCode": self.okrs_system_code,
                            "environmentId": self.okrs_environment_id,
                            "systemTenantId": self.okrs_system_tenant_id,
                        },
                        {
                            "systemCode": self.tenant_parser.app_system_code,
                            "environmentId": self.tenant_parser.tenant_env,
                            "systemTenantId": self.tenant_parser.tenant_id,
                        },
                    ],
                }
            ],
        }


async def setup_global_tenant(*args, **kwargs):
    """
    Find or create a global tenant. Return the global tenant id.

    Takes in the parameters for the GlobalTenantBase class.

    :param str admin_auth_token: an auth token for integration hub
    :param TenantParser tenant_parser:
    :params dict app_settings:
    :params (AIOHttp session) client_session:
    """
    finder = GlobalTenantFinder(*args, **kwargs)
    global_tenant_id = await finder.find_existing()
    if global_tenant_id:
        if finder.okr_tenant_exists():
            return global_tenant_id

        updater = GlobalTenantUpdater(global_tenant_id, *args, **kwargs)
        return await updater.update()

    creator = GlobalTenantCreator(*args, **kwargs)
    return await creator.create()
