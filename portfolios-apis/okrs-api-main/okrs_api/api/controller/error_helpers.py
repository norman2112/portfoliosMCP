"""Error helper methods."""

from http import HTTPStatus
from okrs_api.utils import adapt_error_for_hasura


def bad_request_error(message, error_code):
    """Return a FORMATTED bad request error."""
    return adapt_error_for_hasura(
        [dict(message=message, error_code=error_code)], HTTPStatus.BAD_REQUEST
    )


def not_found_error(message="Resource not found", error_code="NOT_FOUND"):
    """Return a formatted not found error."""
    return adapt_error_for_hasura(
        [dict(message=message, error_code=error_code)], HTTPStatus.NOT_FOUND
    )


def internal_server_error(message, error_code="INTERNAL_ERROR"):
    """Return a formatted server error."""
    return adapt_error_for_hasura(
        [dict(message=message, error_code=error_code)], HTTPStatus.INTERNAL_SERVER_ERROR
    )


# Common specific errors
def pvadmin_required_error():
    """Return error when PVAdmin is required."""
    return bad_request_error("Not a pvadmin customer", "NOT_PVADMIN_CUSTOMER")


def manager_role_required_error():
    """Return error when manager role is required."""
    return bad_request_error("Not an admin user", "NOT_MANAGE_ROLE")
