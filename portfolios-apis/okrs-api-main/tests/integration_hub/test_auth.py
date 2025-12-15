"""Test the authorization to Integration Hub."""

import pytest

from okrs_api.integration_hub.auth import TokenFetcher


class TestIntegrationHubAuthorization:
    """Test the authorization to Integration Hub."""

    @pytest.fixture
    def token_fetcher(self, connexion_client):
        """Return an instance of the TokenFetcher."""

        return TokenFetcher(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
        )

    @pytest.mark.vcr
    async def test_fetch_token(self, token_fetcher):
        token = await token_fetcher.fetch_token()
        assert isinstance(token, str)

    @pytest.mark.vcr
    async def test_fetch_admin_token(self, connexion_client):
        """
        Ensure the token is returned.

        Also ensure that the `endpoint` and `request body` are populated.
        """
        token_fetcher = TokenFetcher(
            client_session=connexion_client.session,
            app_settings=connexion_client.app["settings"],
            admin=True,
        )
        token = await token_fetcher.fetch_token()

        assert isinstance(token, str)
        assert token_fetcher.request_body
        assert token_fetcher.endpoint

    @pytest.mark.vcr
    async def test_fetch_token_with_errors(self, mocker, connexion_client):
        app_settings = connexion_client.app["settings"]
        mocker.patch.object(
            app_settings.integration_hub,
            "client_id",
            "bogus-id",
        )

        token_fetcher = TokenFetcher(
            client_session=connexion_client.session,
            app_settings=app_settings,
        )
        token = await token_fetcher.fetch_token()
        assert not token
        assert len(token_fetcher.errors) > 0
        assert "Could not fetch authentication token" in token_fetcher.errors
