"""Define the integration tests for the application."""
import pytest


async def test_app_starts(offline_connexion_client):
    """Ensure the application starts."""
    resp = await offline_connexion_client.get("/api/ui/")

    assert resp.status == 200
    text = await resp.text()
    assert "Swagger UI" in text


@pytest.mark.integration
@pytest.mark.parametrize(
    "endpoint, content",
    [
        pytest.param("/api/ui/", "Swagger UI", id="api-ui-endpoint"),
    ],
)
async def test_connexion_app_get_endpoints(connexion_client, endpoint, content):
    """Ensure the application retrieves data from GET endpoints."""
    resp = await connexion_client.get(endpoint)

    assert resp.status == 200
    text = await resp.text()
    assert content in text
