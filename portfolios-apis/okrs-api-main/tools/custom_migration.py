"""
Generate a custom migration from a migration template.

The migration template may or may not have a set of values that can be pulled
from a yml file with the same basename.
"""

import os
import sys
from pathlib import Path
import yaml

from mako.template import Template
import typer

from platforma_invocations.utils import common


TEMPLATE_DIR = Path("./alembic/migration_templates")


def create_blank_migration(migration_message):
    """Create a blank migration that will be modified later."""
    migration_revision = common.custom_now()
    os.system(
        "poetry run alembic revision "
        f"--rev-id={migration_revision} -m {migration_message}"
    )
    return f"{migration_revision}_{migration_message}"


def replace_migration_text(migration_filename, migration_data):
    """Write the migration data into the specified migration."""
    with open(f"alembic/versions/{migration_filename}.py", "r+") as f:
        data = f.read()
        f.seek(data.find("def upgrade"))
        f.write(migration_data)
        f.truncate()


def make_custom_migration(migration_message, migration_data):
    """Create a blank migration, then modify it."""
    migration_filename = create_blank_migration(migration_message)
    replace_migration_text(
        migration_filename=migration_filename, migration_data=migration_data
    )


def get_template_vars(template_name):
    """Get the template vars, if provided."""
    vars_file = Path(TEMPLATE_DIR / f"{template_name}.yml")
    if not vars_file.exists():
        return None

    with open(vars_file, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def get_template_output(template_name):
    """Get template output for the selected template."""
    template_file = Path(TEMPLATE_DIR / f"{template_name}.py.mako")
    print(f"Using template file {template_file}")
    if not template_file.exists():
        print(
            f"The template file {template_file} does not exist. "
            "Try another template name."
        )
        sys.exit()

    template_vars = get_template_vars(template_name) or {}
    template = Template(filename=str(template_file))
    output = template.render(**template_vars)
    return output


def main(
    template_name: str,
    migration_message: str = typer.Argument(None),
    dry_run: bool = typer.Option(
        False, help="print only the output that would be written to a migration."
    ),
):
    """
    Define the program entrypoint.

    :param str template_name: the base name of the template.
    :param str migration_message: (optional) message for the migration. If
    none is provided, then the template name is used.
    :param bool dry_run: only perform a dry run, rather than
    creating a migration.
    """

    output = get_template_output(template_name)
    if dry_run:
        print(output)
        return

    migration_message = migration_message or template_name
    make_custom_migration(migration_message=migration_message, migration_data=output)
    os.system("poetry run black alembic/versions")


if __name__ == "__main__":
    typer.run(main)
