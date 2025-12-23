"""
Generate a JWT using the planview token service.

Must set PLANVIEW_TOKEN_SERVICE_CLIENT_ID and PLANVIEW_TOKEN_SERVICE_CLIENT_SECRET
environment vars.
"""
import os
import sys

import typer
import requests


def generate_token(app, user_id, env_id, domain, org_id):
    """
    Generate token based on input and environment parameters.

    ENV variables needed:

    - `PLANVIEW_TOKEN_SERVICE_CLIENT_ID`: the client id for PTS
    - `PLANVIEW_TOKEN_SERVICE_CLIENT_SECRET`: the client secret for PTS
    - `PLANVIEW_TOKEN_SERVICE_REGION`: the region for the service. Default ('us-west-2')

    Variables to pass in:

    :param str app: the application that the PTS token is for.
    :param str user_id: the application user id that the PTS token is for.
    :param str env_id: the application env.
    :param str domain: the domain of the application
    :param str org_id: the org id of the application

    """

    region = os.environ.get("PLANVIEW_TOKEN_SERVICE_REGION") or "us-west-2"
    print(
        f"Generating a token for region {region} with user_id: {user_id}, "
        + f"env_id: {env_id}, domain: {domain}, org_id: {org_id}\n"
    )

    client_id_env_var = "PLANVIEW_TOKEN_SERVICE_CLIENT_ID"
    client_secret_env_var = "PLANVIEW_TOKEN_SERVICE_CLIENT_SECRET"

    if client_id_env_var not in os.environ:
        print(f"{client_id_env_var} environment variable required")
        sys.exit(1)

    if client_secret_env_var not in os.environ:
        print(f"{client_secret_env_var} environment variable required")
        sys.exit(1)

    data = {
        "client_id": os.environ[client_id_env_var],
        "client_secret": os.environ[client_secret_env_var],
        "application_name": str(app),
        "application_domain": str(domain),
        "application_roles": "user",
        "application_account_id": str(org_id),
        "application_user_id": str(user_id),
        "application_context_id": None,
        "role": "user",
        "account_id": f"{app.upper()}~{env_id}-{org_id}",
        "user_id": str(user_id),
        "sections": None,
    }

    response = requests.post(
        f"https://auth-{region}.pv-platforma.xyz/oauth2/token", data=data
    )

    jwt_token = response.json()["id_token"]

    print(f"Generated Token: \n{jwt_token}")
    return jwt_token


def main():
    """Define the program entrypoint."""
    typer.run(generate_token)


if __name__ == "__main__":
    main()
