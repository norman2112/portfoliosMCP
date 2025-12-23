"""An utility to export the OKR data from source location."""

import sys
import asyncio

from loguru import logger

from okrs_api import connexion_utils
from okrs_api.api.controller.data_migration import export_from_json_input

# Create the Connexion application.
try:
    # Create the WSGI app
    app = connexion_utils.create_connexion_app().app
except Exception as e:
    logger.exception(e)
    sys.exit(1)


def main():
    """Adapt AgilePlace manifest and export OKR manifest."""
    try:
        input_json = sys.argv[1]
    except BaseException:
        print("Unable to run, input is missing", file=sys.stderr)
        sys.exit(1)
    asyncio.run(export_from_json_input(app, input_json))


if __name__ == "__main__":
    main()
