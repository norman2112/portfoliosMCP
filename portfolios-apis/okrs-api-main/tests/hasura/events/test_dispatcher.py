from mock_alchemy.mocking import UnifiedAlchemyMagicMock
import pytest

from okrs_api.hasura.events.dispatcher import Dispatcher


class TestDispatcher:
    """Testing the dispatching to the proper collaborators."""

    def trigger_payload(self, trigger):
        table_name = trigger.split("-")[0]
        return {
            "event": {
                "op": "INSERT",
                "data": {
                    "old": None,
                    "new": {},
                },
            },
            "trigger": {"name": trigger},
            "table": {"name": table_name},
        }

    @pytest.mark.parametrize(
        "trigger_name",
        [
            pytest.param("key_results", id="key_results"),
            pytest.param(
                "key_result_work_item_mappings", id="key_result_work_item_mappings"
            ),
            pytest.param("objectives", id="objectives"),
            pytest.param("progress_points", id="progress_points"),
            pytest.param("settings", id="settings"),
            pytest.param("work_items", id="work_items"),
            pytest.param(
                "work_item_containers",
                id="work_item_containers",
            ),
        ],
    )
    async def test_handler_instantiation(self, mocker, trigger_name):
        """
        Ensure the the dispatcher instantiates the proper handlers, and then
        called the `handle_event` operation on each of them.
        """
        db_session = UnifiedAlchemyMagicMock()
        mock_request = mocker.patch("aiohttp.web.Request", autospec=True)
        body = self.trigger_payload(trigger_name)
        dispatcher = Dispatcher(mock_request, body, db_session)
        mocker.patch(
            "okrs_api.hasura.events.handlers.base.Base.handle_event",
            mocker.AsyncMock(return_value=True),
        )
        assert await dispatcher.dispatch()

    async def test_handler_missing(self, mocker):
        """Raise our error if handler isn't found."""
        db_session = UnifiedAlchemyMagicMock()
        mock_request = mocker.patch("aiohttp.web.Request", autospec=True)
        dispatcher = Dispatcher(mock_request, {}, db_session)
        mocker.patch(
            "okrs_api.hasura.events.handlers.base.Base.handle_event",
            mocker.AsyncMock(return_value=True),
        )
        with pytest.raises(KeyError):
            assert await dispatcher.dispatch()
