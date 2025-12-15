"""Define utilities to create and configure a connexion app."""
import os

import aiohttp_cors
import connexion
from connexion.resolver import RestyResolver
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from open_alchemy import init_yaml
from swagger_ui_bundle import swagger_ui_3_path

from okrs_api import database
from okrs_api import http_client
from okrs_api import settings
from okrs_api.api.controller.health import health_check


def create_connexion_app(environment_override=None):
    """Create and configure a connexion app."""

    env_str = environment_override or os.environ["CONNEXION_ENVIRONMENT"]
    app_settings = settings.get(env_str)
    app_options = {
        "import_name": __name__,
        "port": app_settings.port,
        "specification_dir": app_settings.specification_dir,
        "debug": app_settings.debug,
        "options": {"swagger_ui": True, "swagger_path": swagger_ui_3_path},
    }

    # Create the application.
    app = connexion.AioHttpApp(**app_options)

    # Generate models.
    init_yaml(app_settings.specification_file)

    # Save the settings within the application context.
    # More information here:
    # https://docs.aiohttp.org/en/stable/web_advanced.html?highlight=config#application-s-config
    app.app["settings"] = app_settings

    # Initialize the database connection.
    app.app.cleanup_ctx.append(database.init)

    # Initialize the pubnub object.
    from okrs_api import pubnub_session  # pylint: disable=import-outside-toplevel

    app.app.cleanup_ctx.append(pubnub_session.init)

    # Initialize the http client session.
    app.app.cleanup_ctx.append(http_client.init)

    # Add the specification file.
    app.add_api(
        app_settings.specification_file,
        resolver=RestyResolver(app_settings.resolver_module_name),
        base_path="/api",
        pass_context_arg_name="request",
    )

    # Add the health check route
    app.app.router.add_get("/healthcheck", health_check)

    # Configure the CORS extension.
    cors = aiohttp_cors.setup(
        app.app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    for route in list(app.app.router.routes()):
        cors.add(route)

    sentry_sdk.init(
        integrations=[AioHttpIntegration(), SqlalchemyIntegration()],
        environment=env_str,
        traces_sample_rate=app_settings.sentry_traces_sample_rate,
    )

    return app
