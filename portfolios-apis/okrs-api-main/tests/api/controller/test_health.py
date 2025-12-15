from okrs_api.api.controller import health
from aiohttp.test_utils import make_mocked_request


async def test_health():
    """
    This test ensures that health check method returns a 200 OK Response.
    """
    request = make_mocked_request("GET", "/")
    response = await health.health_check(request)
    assert response.status == 200
    assert response.reason == "OK"
