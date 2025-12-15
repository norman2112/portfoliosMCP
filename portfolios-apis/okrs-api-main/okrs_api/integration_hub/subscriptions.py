"""Subscription handlers for Integration Hub."""

from datetime import datetime, timezone

from aiohttp import client_exceptions
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    wait_random,
)
import uuid
from yarl import URL


class ActivitySubscriptionManager:
    """Subscriber of an Integration Hub Queue."""

    SYSTEM_CODE = "okrs"
    # Activity types map to the external type of the WorkItem
    ACTIVITY_TYPE_CONFIGS = {
        "leankit": {"code": "lk", "subscription_type": "CardSubscription"},
    }
    URL_PATH = "/inthub/api/v1/publish"

    def __init__(
        self,
        client_session,
        work_item_attribs,
        app_settings,
        bearer_token,
        global_tenant_id,
        tenant_parser,
    ):
        """
        Initialize the Manager.

        :param session client_session: an Aiohttp client session
        :param dict work_item_attribs: attribs passed from Hasura for the event
        :param settings app_settings: settings for the app
        :param str bearer_token: the integration hub bearer token
        :param str global_tenant_id: the global tenant id from the registration
        :param TenantParser tenant_parser: the TenantParser for the `tenant_id_str`
        """
        self.client_session = client_session
        self.work_item_attribs = work_item_attribs or {}
        self.app_settings = app_settings
        self.bearer_token = bearer_token
        self.global_tenant_id = global_tenant_id
        self.tenant_parser = tenant_parser
        self.errors = []
        # Used for caching
        self.response = None
        self.response_data = None
        self.subscription_body = None

    async def subscribe(self):
        """Subscribe to an activity."""
        self.response = await self._make_subscription_call(action="create")
        await self._set_response_data(self.response)
        return self.response

    async def unsubscribe(self):
        """Unsubscribe from an activity."""
        self.response = await self._make_subscription_call(action="delete")
        await self._set_response_data(self.response)
        return self.response

    @retry(
        wait=wait_fixed(3) + wait_random(0, 2),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(client_exceptions.ClientError),
    )
    async def _make_subscription_call(self, action="create"):
        """
        Call the Integration Hub to either subscribe or unsubscribe.

        Cache the value of the subscription body for later logging, in case
        of failure.

        Return the response from the Integration Hub.
        """
        self.subscription_body = self._subscription_body(action=action)
        return await self.client_session.post(
            self._endpoint,
            json=self.subscription_body,
            headers=self._headers,
        )

    async def _set_response_data(self, response):
        """Cache the response and data and set errors."""
        try:
            # cache the response data
            self.response_data = await response.json()
            if not response.ok:
                self._set_errors(response, self.response_data)
        except Exception:
            self._set_errors(response)

        return self.response

    def _set_errors(self, response, response_data=None):
        """Set errors based on response."""
        if response.ok:
            return

        self.errors = [
            "Subscription failure.",
            self.response.reason,
            self._endpoint,
        ]
        if response_data and response_data.get("errors"):
            self.errors = [*self.errors, *response_data.get("errors")]

        return self.errors

    def _subscription_body(self, action="create"):
        """
        Return the payload to create or delete the subscription.

        :param str action: either "create" or "delete"

        The `action` param determines whether to create or delete the
        Integration Hub subscription.
        """
        return {
            "messageGuid": str(uuid.uuid4()),
            "globalTenantId": self.global_tenant_id,
            "envelopeSchemaVersion": "1.0",
            "publishTimestamp": {
                "iso": datetime.now(timezone.utc).isoformat(),
                "epoch": self.current_timestamp(),
            },
            "sender": {
                "systemCode": self.SYSTEM_CODE,
                "environmentId": self._environment_id(),
                "systemTenantId": self.tenant_parser.okrs_tenant_id,
            },
            "payload": [
                {
                    "type": self._subscription_type,
                    "eventType": action,
                    "schemaVersion": "1.0",
                    "publishedSchemaVersions": ["1.0"],
                    "subscriptionType": self.SYSTEM_CODE,
                    "id": self._activity_id,
                    "integration": {
                        self._product_code: {"id": self._activity_id},
                        "okrs": {"id": str(self._work_item_id)},
                    },
                }
            ],
        }

    def current_timestamp(self):
        """Return the current timestamp for use in the body."""
        return int(datetime.now(timezone.utc).timestamp())

    @property
    def integration_hub_domain(self):
        """Return the AWS Region from the app settings."""
        return self.app_settings.get("integration_hub_domain")

    @property
    def _region(self):
        """Return the AWS Region from the app settings."""
        return self.app_settings.region

    @property
    def _work_item_id(self):
        return self.work_item_attribs.get("id")

    @property
    def _product_type(self):
        return self.work_item_attribs.get("external_type")

    @property
    def _activity_id(self):
        return self.work_item_attribs.get("external_id")

    @property
    def _activity_config(self):
        return self.ACTIVITY_TYPE_CONFIGS.get(self._product_type, {})

    @property
    def _subscription_type(self):
        """
        Return the type for the payload.

        e.g. "CardSubscription" for Leankit.
        """
        return self._activity_config.get("subscription_type")

    @property
    def _product_code(self):
        """
        Return the product code for the payload.

        e.g. "lk" for Leankit.
        """
        return self._activity_config.get("code")

    def _environment_id(self):
        """
        Construct the environment ID used by Integration Hub.

        e.g. "okrs-env-us-west-2"
        """
        return f"{self.SYSTEM_CODE}-env-{self._region}"

    @property
    def _ih_settings(self):
        """Return the integration hub settings."""
        return self.app_settings.integration_hub

    @property
    def _endpoint(self):
        """
        Return the Integration Hub endpoint for the subscription.

        e.g. https://us-west-2.pvintegrations-staging.net/inthub/api/v1/publish
        """
        return str(
            URL.build(scheme="https", host=self._ih_settings.domain, path=self.URL_PATH)
        )

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
