"""Generate connexion controllers."""
# pylint: disable=no-member
from pathlib import Path

from jinja2 import Template
import typer
import yaml

CONTROLLER_TEMPLATE = '''
"""Define the {{ name }} controller."""
from connexion import NoContent
from open_alchemy import models


{% for operations, parameters in operations.items() %}
async def {{ operations }}(request, {{ parameters|join(', ') }}):
    """Define the {{ operations }} operation."""
    db_session = request.app["db_session"]
    return NoContent, 404

{% endfor %}
'''


def get_controllers_from_spec(openapi_dict):
    """
    Retrieve the controllers, associated operations and parameters.

    :param dict openapi_dict: A dictionary representing the OpenAPI
        specification file.
    :returns dict: a dict of controllers, associated operations and parameters.
    """
    controllers = {}

    # Loop through the endpoints and their operations.
    for path, operations in openapi_dict["paths"].items():
        # Collect the controller.
        split_path = [part for part in path.split("/") if part]
        controller = split_path[0]

        # Collect the assiocated parameters.
        raw_parameters = list(filter(lambda x: x.startswith("{"), split_path))
        parameters = [
            raw_parameter.replace("{", "").replace("}", "")
            for raw_parameter in raw_parameters
        ]
        controllers.setdefault(controller, {})

        # Collect the associated operations.
        for operation in operations:

            # A GET operation without parameter is translated to "search" by
            # Connexion.
            if not parameters and operation == "get":
                controllers[controller]["search"] = []
                continue

            # Add all the other operations normally.
            controllers[controller][operation] = parameters

    return controllers


def generate(
    openapi: Path = typer.Option(file_okay=True, dir_okay=False, default="openapi.yml"),
    output: Path = typer.Option(
        file_okay=False, dir_okay=True, writable=True, default="."
    ),
):
    """Generate the controllers."""
    # Read the specification file.
    openapi_dict = yaml.safe_load(openapi.read_text())

    # Extract the controllers information.
    controllers = get_controllers_from_spec(openapi_dict)

    # Render the controllers.
    template = Template(CONTROLLER_TEMPLATE)
    for name, operations in controllers.items():
        t = template.render(name=name, operations=operations).strip()
        f = output / f"{name}.py"
        f.write_text(t)


def main():
    """Define the program entrypoint."""
    typer.run(generate)


if __name__ == "__main__":
    main()
