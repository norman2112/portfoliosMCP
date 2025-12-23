"""An utility to export the OKR data from source location."""

import sys
import asyncio

from loguru import logger

from okrs_api import connexion_utils
from okrs_api.api.controller.data_migration import migrate_from_json_input

# Create the Connexion application.
try:
    # Create the WSGI app
    app = connexion_utils.create_connexion_app().app
except Exception as e:
    logger.exception(e)
    sys.exit(1)


def main():
    """Adapt AgilePlace manifest and export OKR manifest."""
    print(sys.argv)
    try:
        migration_type = sys.argv[1]
        if migration_type == "export":
            arg1 = sys.argv[2]
            arg2 = sys.argv[3]
            arg3 = sys.argv[4]
            payload = dict(
                migration_type="export",
                manifest_filename=arg1,
                product_type=arg2,
                tenant_id_str=arg3,
            )
        elif migration_type == "import":
            arg1 = sys.argv[2]
            arg2 = sys.argv[3]
            arg3 = sys.argv[4]
            payload = dict(
                migration_type="import",
                product_type=arg1,
                original_tenant_id_str=arg2,
                new_tenant_id_str=arg3,
            )
        elif migration_type == "delete":
            arg1 = sys.argv[2]
            payload = dict(
                migration_type="delete",
                tenant_id_str=arg1,
            )
        else:
            raise ValueError("Unknown command")

        asyncio.run(migrate_from_json_input(app, payload))
    except BaseException as ex:
        print(ex)
        print("Unable to run, input is missing", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
