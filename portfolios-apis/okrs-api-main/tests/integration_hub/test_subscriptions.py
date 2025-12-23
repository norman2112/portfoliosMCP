"""Test the subscriptions to queues in Integration Hub."""

import pytest
import tenacity
from aiohttp import client_exceptions

from okrs_api.integration_hub.auth import TokenFetcher
from okrs_api.integration_hub.registrations import RegistrationManager
from okrs_api.integration_hub.subscriptions import ActivitySubscriptionManager
from okrs_api.tenant_parser import TenantParser

# IMPORTANT: WHEN RECORDING A NEW VCR CASSETTE FOR THIS TEST
#
# In your .env file, you will need to change the following values to the staging
# versions:
# IH_DOMAIN, IH_CLIENT_ID, IH_CLIENT_SECRET
# in order for this to record a new vcr cassette properly.
# Presently, there is something potentially mis-configured in the development
# environment on Integration Hub; this will not work in dev.
class TestSubscriptionManagement:
    """Test the subscription management to Integration Hub."""

    TENANT_CODE = "LEANKIT~d08-10100000101"

    @pytest.fixture
    def token_fetcher(self, connexion_client):
        """Return an instance of the TokenFetcher."""

        return TokenFetcher(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
        )

    @pytest.fixture
    def subscription_manager_factory(self, connexion_client):
        """Return an instance of a ActivitySubscriptionManager."""
        DEFAULT_WORK_ITEM_ATTRIBS = {
            "id": "12345",
            "external_type": "leankit",
            "external_id": "55555",
        }

        def _subscription_manager_factory(
            global_tenant_id="1234",
            bearer_token="auth-123",
            work_item_attribs=None,
            app_settings=None,
            tenant_code=None,
        ):
            work_item_attribs = work_item_attribs or DEFAULT_WORK_ITEM_ATTRIBS
            app_settings = app_settings or connexion_client.app["settings"]
            tenant_code = tenant_code or "LEANKIT~d08-10100000101"
            return ActivitySubscriptionManager(
                client_session=connexion_client.session,
                work_item_attribs=work_item_attribs,
                app_settings=app_settings,
                bearer_token=bearer_token,
                global_tenant_id=global_tenant_id,
                tenant_parser=TenantParser(tenant_code),
            )

        return _subscription_manager_factory

    @pytest.mark.vcr
    async def test_subscription(
        self, connexion_client, token_fetcher, subscription_manager_factory
    ):
        # 1. Get a token
        token = await token_fetcher.fetch_token()
        registration_manager = RegistrationManager(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
            bearer_token=token,
            tenant_parser=TenantParser(self.TENANT_CODE),
        )
        # 2. Register to get the global tenant id
        await registration_manager.register()

        gt_id = registration_manager.response_data.global_tenant_id
        subscription_manager = subscription_manager_factory(
            bearer_token=token,
            global_tenant_id=gt_id,
        )

        # 3. Subscribe to the adapter
        await subscription_manager.subscribe()

        response_data = subscription_manager.response_data
        assert response_data.get("successfulDelivery")

    async def test_subscription_retry(self, mocker, subscription_manager_factory):
        """Test that a retry happens on client failure."""
        subscription_manager = subscription_manager_factory()
        mocker.patch.object(
            subscription_manager.client_session,
            "post",
            mocker.AsyncMock(side_effect=client_exceptions.ClientError),
        )
        subscription_manager._make_subscription_call.retry.wait = tenacity.wait_none()
        with pytest.raises(tenacity.RetryError):
            await subscription_manager.subscribe()

    @pytest.mark.vcr
    async def test_unauthorized_subscription(self, connexion_client):
        """Ensure errors are reported when subscription is unauthorized."""
        subscription_manager = ActivitySubscriptionManager(
            client_session=connexion_client.session,
            work_item_attribs={"id": "12345"},
            app_settings=connexion_client.app["settings"],
            bearer_token="bogus-token",
            global_tenant_id="55555",
            tenant_parser=TenantParser(self.TENANT_CODE),
        )
        await subscription_manager.subscribe()

        assert len(subscription_manager.errors) > 0
        assert not subscription_manager.response.ok
