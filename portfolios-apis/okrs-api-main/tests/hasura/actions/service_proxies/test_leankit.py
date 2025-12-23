"""Tests for the leankit service proxy."""
from http import HTTPStatus

import pytest
import tenacity

from okrs_api.hasura.actions.prepper import prepper_factory
from okrs_api.service_proxies import leankit
from okrs_api.hasura.actions.proxy_response import ProxyResponseWrapper

DEFAULT_BODY = {"input": {"product_type": "leankit", "domain": "d08.leankit.io"}}


class TestLeankitServiceProxy:
    """Test the service proxy for leankit."""

    def make_input_prepper(self, request, action_name):
        body = {
            **DEFAULT_BODY,
            "action": {"name": action_name},
        }
        return prepper_factory(request, body)

    @pytest.mark.parametrize(
        "action_name, leankit_services",
        [
            pytest.param(
                "search_activities",
                ["CardService.search", "BoardService.board_details"],
                id="search-activities",
            ),
            pytest.param(
                "create_activity",
                ["CardService.create", "BoardService.board_details"],
                id="create-activity",
            ),
            pytest.param(
                "search_activity_containers",
                ["BoardService.search"],
                id="search-activity-containers",
            ),
            pytest.param(
                "list_activity_types",
                ["BoardService.board_details"],
                id="list-activity-types",
            ),
            pytest.param(
                "search_users",
                ["BoardService.search_users"],
                id="search-users",
            ),
        ],
    )
    async def test_all_actions(
        self, mocker, request_with_jwt, action_name, leankit_services
    ):
        """Test that the proper service is called."""
        for leankit_service in leankit_services:
            mocker.patch(
                f"okrs_api.external_apis.leankit.services.{leankit_service}",
                return_value=mocker.Mock(ok=True, status=HTTPStatus.OK),
            )
        input_prepper = self.make_input_prepper(request_with_jwt, action_name)
        proxy = leankit.ServiceProxy(input_prepper)
        response = await getattr(proxy, action_name)()
        wrapper = ProxyResponseWrapper(response)
        assert wrapper.ok()

    async def test_create_activity_retry(self, mocker, request_with_jwt):
        """Test that the proper service is called."""
        mocker.patch(
            f"okrs_api.external_apis.leankit.services.CardService.create",
            return_value=mocker.Mock(ok=False, status=HTTPStatus.INTERNAL_SERVER_ERROR),
        )
        mocker.patch(
            f"okrs_api.external_apis.leankit.services.BoardService.board_details",
            return_value=mocker.Mock(ok=False, status=HTTPStatus.INTERNAL_SERVER_ERROR),
        )
        input_prepper = self.make_input_prepper(request_with_jwt, "create_activity")
        proxy = leankit.ServiceProxy(input_prepper)
        # Remove the retry wait time in Tenacity to speed up tests
        proxy.create_activity.retry.wait = tenacity.wait_none()

        with pytest.raises(tenacity.RetryError):
            await proxy.create_activity()
