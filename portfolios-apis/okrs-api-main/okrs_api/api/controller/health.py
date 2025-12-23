"""
Controller for the health endpoint.

It does not run through connexion, and thus, does not have the same input
and return requirements.

See more here for details:
https://docs.aiohttp.org/en/stable/web_quickstart.html#handler
"""

import datetime
from http import HTTPStatus

from aiohttp import web


async def health_check(_request):
    """Render a timestamp and an OK status."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d, %H:%M:%-S.%f")
    data = {"timestamp": timestamp}
    return web.json_response(data, status=HTTPStatus.OK)
