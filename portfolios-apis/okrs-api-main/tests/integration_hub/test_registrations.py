"""Test the registratinos to Integration Hub."""

import pytest

from okrs_api.integration_hub.auth import TokenFetcher
from okrs_api.integration_hub.registrations import RegistrationManager
from okrs_api.tenant_parser import TenantParser


class TestIHRegistrations:
    """Ensure Registrations work for Integration Hub."""

    TENANT_CODE = "LEANKIT~d08-10100000101"

    @pytest.fixture
    def token_fetcher(self, connexion_client):
        """Return an instance of the TokenFetcher."""

        return TokenFetcher(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
        )

    @pytest.mark.parametrize(
        "tenant_id_str",
        [
            pytest.param("LEANKIT~d08-10100000101", id="with-env"),
        ],
    )
    def test_registration_body(self, connexion_client, tenant_id_str):
        """Ensure that the registration body is correct."""
        manager = RegistrationManager(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
            bearer_token="test-token",
            tenant_parser=TenantParser(tenant_id_str),
        )
        expected = {
            "environmentId": "okrs-env-us-west-2",
            "numQueues": 1,
            "registrationId": "adapter-okrs-d08",
            "systemCode": "okrs",
            "systemTenantIds": ["okrs-d08-10100000101"],
            "tenantOp": "add",
        }

        assert manager.register_body == expected

    @pytest.mark.vcr
    async def test_registration(self, connexion_client, token_fetcher):
        """Ensure a successful registration can happen."""
        token = await token_fetcher.fetch_token()
        manager = RegistrationManager(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
            bearer_token=token,
            tenant_parser=TenantParser(self.TENANT_CODE),
        )

        await manager.register()
        assert not manager.errors
        assert isinstance(manager.response_data.global_tenant_id, str)

    @pytest.mark.vcr
    async def test_unauthorized_registration(self, connexion_client):
        """
        Ensure bad authorization returns errors in the errors array.

        The errors should contain the request info and a descriptive message.
        Additionally, the registration call should return True or False.
        """
        manager = RegistrationManager(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
            bearer_token="bogus-token",
            tenant_parser=TenantParser(self.TENANT_CODE),
        )

        assert not await manager.register()
        assert not manager.response.ok
        assert len(manager.errors) > 0
        assert "Could not register with Integration Hub." in manager.errors
        assert any("https://" in error for error in manager.errors)
        assert not manager.response_data
