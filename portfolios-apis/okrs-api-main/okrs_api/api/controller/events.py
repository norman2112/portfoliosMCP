"""Define the events controller."""
from http import HTTPStatus

from connexion import NoContent
import sentry_sdk

from okrs_api.hasura.events.dispatcher import Dispatcher


async def post(request, body):
    """Dispatch event based on event body params."""
    if not (body and body.get("event")):
        return NoContent, HTTPStatus.BAD_REQUEST

    with request.app["db_session"]() as db_session:
        dispatcher = Dispatcher(request, body, db_session)
        await dispatcher.dispatch()

    if not dispatcher.dispatch_ok:
        sentry_sdk.set_context(
            "event_dispatcher_errors",
            {"errors": dispatcher.errors},
        )
        raise Exception("dispatcher errors present")

    return NoContent, HTTPStatus.OK
