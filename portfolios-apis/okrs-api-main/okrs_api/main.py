"""Define the Connexion app."""
import asyncio
import logging
import sys

from gunicorn.app.base import BaseApplication

from loguru import logger
import uvloop

from okrs_api import connexion_utils

LOG_FORMAT_VERBOSE = (
    "<level>{time:YYYY-MM-DDTHH:mm:ssZZ} {name}:{line:<4} {message}</level>"
)


# Setup uvloop.
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# Create the Connexion application.
try:
    # Create the WSGI app
    application = connexion_utils.create_connexion_app().app
except Exception as e:
    logger.exception(e)
    sys.exit(1)

# Remove any predefined logger.
logger.remove()

# Set the log colors.
logger.level("ERROR", color="<red><bold>")
logger.level("WARNING", color="<yellow>")
logger.level("SUCCESS", color="<green>")
logger.level("INFO", color="<cyan>")
logger.level("DEBUG", color="<blue>")
logger.level("TRACE", color="<magenta>")

# Add the logger.
logger.add(
    sys.stderr,
    format=LOG_FORMAT_VERBOSE,
    level=application["settings"].log_level,
    colorize=True,
)


class StandaloneApplication(BaseApplication):
    """
    Creates a stand-alone application, using Gunicorn.

    Instead of importing gunicorn into the docker container, this class uses
    the `BaseApplication` to incorporate gunicorn directly into the wsgi app.
    """

    # pylint:disable=abstract-method
    def __init__(self, app, options=None):
        """
        Initialize the app.

        This will initialize the app in a way that gunicorn can run it directly.
        """
        self.options = options or {}
        self.application = app
        self._set_logger()
        super().__init__()

    def load_config(self):
        """
        Overwrite method from the base class.

        Load all configuration into the self.cfg dict.
        """
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        """Return the application."""
        return self.application

    def _set_logger(self):
        """
        Configure the aiohttp access logger.

        Set the logger of this standalone app to this logger after
        configuration.
        """
        # Configure aiohttp access logger.
        # This logger is using the standard logger.
        access_logger = logging.getLogger("aiohttp.access")
        access_logger.setLevel(application["settings"].log_level)
        access_logger.addHandler(logging.StreamHandler())

        # Setting the logger for gunicorn to be the Loguru logger.
        self.logger = logger


@logger.catch
def main():
    """Define the application entrypoint."""

    gunicorn_settings = application["settings"].gunicorn
    options = {
        "bind": "%s:%s" % ("0.0.0.0", gunicorn_settings.port),
        "worker_class": "aiohttp.GunicornUVLoopWebWorker",
        "reload": gunicorn_settings.reload,
        "timeout": gunicorn_settings.timeout,
        "loglevel": gunicorn_settings.log_level,
        "workers": gunicorn_settings.workers,
        "accesslog": gunicorn_settings.access_log,
        "access_log_format": gunicorn_settings.access_logformat,
    }
    # Start the web application.
    StandaloneApplication(application, options).run()


# Start the application.
if __name__ == "__main__":
    main()
