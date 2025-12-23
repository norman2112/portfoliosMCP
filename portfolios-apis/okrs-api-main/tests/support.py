from collections import namedtuple

from okrs_api.hasura.actions.prepper import prepper_factory


def response_parser(response):
    """
    Converts the response tuple to a namedtuple.
    """
    response_tuple = namedtuple("response", ["response_data", "HTTPStatus"])
    return response_tuple(*response)


def wrangler_factory(wrangler_klass, request, body):
    """Make a service wrangler from the request and body."""
    input_prepper = prepper_factory(request, body)
    return wrangler_klass(
        input_parser=input_prepper.input_parser,
        jwt_parser=input_prepper.jwt_parser,
        db_session=input_prepper.db_session,
        client_session=input_prepper.client_session,
        app_settings=input_prepper.app_settings,
    )
