import pytest

from tests.hasura.events.payloads import bogus_trigger_event, event_payload
from okrs_api.api.controller import events
from http import HTTPStatus
from tests.support import response_parser


async def test_events_with_progress_point_trigger(request_with_jwt):
    """
    Tests the events return HTTPStatus.OK when ProgressPercentageWriter.call is success
    """
    response = await events.post(
        request_with_jwt,
        event_payload("progress_points", "insert"),
    )
    assert response_parser(response).HTTPStatus == HTTPStatus.OK


async def test_events_with_key_result_trigger(mocker, request_with_jwt):
    """Ensure the events return HTTPStatus.OK."""
    mocker.patch(
        "okrs_api.hasura.events.handlers.key_results.progress_percentage.Handler._update_progress",
        mocker.Mock(return_value=True),
    )
    response = await events.post(
        request_with_jwt,
        event_payload("key_results", "delete"),
    )
    assert response_parser(response).HTTPStatus == HTTPStatus.OK


async def test_events_with_empty_body(request_with_jwt):
    """
    Tests the events return HTTPStatus.BAD_REQUEST when the request body is empty
    """
    response = await events.post(request_with_jwt, {})
    assert response_parser(response).HTTPStatus == HTTPStatus.BAD_REQUEST


async def test_events_for_error(mocker, request_with_jwt):
    """
    Ensure the event controller returns HTTPStatus.UNPROCESSABLE_ENTITY on failure.
    """
    mocker.patch(
        "okrs_api.hasura.events.handlers.key_results.progress_percentage.Handler.handle_event",
        mocker.AsyncMock(return_value=False),
    )

    with pytest.raises(Exception) as e:
        await events.post(request_with_jwt, event_payload("key_results", "delete"))


async def test_events_for_invalid_trigger(request_with_jwt):
    """
    Ensure the event controller returns HTTPStatus.UNPROCESSABLE_ENTITY on an invalid trigger.
    """
    with pytest.raises(Exception) as e:
        await events.post(
            request_with_jwt,
            bogus_trigger_event(),
        )
