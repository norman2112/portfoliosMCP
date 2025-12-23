"""Set up the http client in order to make external requests."""

from aiohttp import ClientSession


async def init(app):
    """Initialize the AIOHTTP client session."""
    # Connexion adds a default subapp.
    sub_app = app._subapps[0]

    # Store the information in the application context.
    sub_app["client_session"] = ClientSession()
    yield

    # Close the client session on quit.
    await sub_app["client_session"].close()
