"""Test the Handler for Settings Insertion."""
from aiohttp.client_exceptions import ClientError
from open_alchemy import models
import pytest


from okrs_api.hasura.events.handlers.settings.pubnub import Handler as PubnubHandler
from tests.hasura.events.payloads import event_payload


class TestPubnubHandler:
    """Test the pubnub handlers for objectives."""

    @pytest.mark.parametrize(
        "operation, response",
        [pytest.param("insert", True), pytest.param("update", True)],
    )
    @pytest.mark.usefixtures("init_models")
    async def test_objective_changes(
        self, mocker, event_handler_factory, operation, response
    ):
        """Ensure that we send a pubnub event on objective changes."""

        handler = event_handler_factory(
            handler_klass=PubnubHandler,
            input_data=event_payload("settings", operation),
        )

        mocker.patch.object(handler, "_send_pubnub_event", return_value=True)

        result = await getattr(handler, f"{operation}_event")()

        assert result == response
