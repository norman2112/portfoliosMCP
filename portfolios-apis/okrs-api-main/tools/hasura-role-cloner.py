"""Clone a Hasura Role in the Hasura metadata."""

import copy
from pathlib import Path
from typing import Optional
import typer
import yaml

HASURA_METADATA_TABLE_FILE = Path("../hasura/metadata/tables.yaml")
ALL_PERMISSIONS = ["select", "insert", "update", "delete"]


# pylint:disable=unsubscriptable-object
def clone_role(
    old_role: str, new_role: str, permissions: Optional[str] = typer.Argument(None)
):
    """Clone a user role in the Hasura metadata."""

    permissions = permissions or ALL_PERMISSIONS
    if isinstance(permissions, str):
        permissions = permissions.split(",")

    print(f"Cloning permissions for role '{new_role}' for {permissions}")
    for permission in permissions:
        if permission not in ALL_PERMISSIONS:
            print(
                f"'{permission}' not allowed. "
                f"Available permissions are: {ALL_PERMISSIONS}"
            )
            return

    current_data = _read_hasura_metadata()
    new_data = copy.deepcopy(current_data)
    for index, table_data in enumerate(new_data):
        for permission in permissions:
            permission_key = f"{permission}_permissions"
            role_list = table_data.get(permission_key)
            if not role_list:
                continue

            new_data[index][permission_key] = _alter_role_list(
                role_list, old_role, new_role
            )

    if new_data == current_data:
        print("No change in metadata. Skipping.")
        return

    with open(HASURA_METADATA_TABLE_FILE, "w") as file:
        try:
            yaml.safe_dump(new_data, file, sort_keys=False, default_flow_style=False)
        except yaml.YAMLError as exc:
            print(exc)

    print(f"Wrote new tables data file to {HASURA_METADATA_TABLE_FILE}.")


def _read_hasura_metadata():
    with open(HASURA_METADATA_TABLE_FILE, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def _role_match(permissions_list, role_name):
    for index, role_dict in enumerate(permissions_list):
        if role_dict.get("role") == role_name:
            return (index, role_dict)

    return None


def _alter_role_list(role_list, old_role, new_role):
    old_role_match = _role_match(role_list, old_role)
    new_role_match = _role_match(role_list, new_role)
    if not old_role_match:
        if new_role_match:
            new_index, _result = new_role_match
            del role_list[new_index]

        return role_list

    _old_index, old_role_dict = old_role_match
    new_role_dict = copy.deepcopy(old_role_dict)
    new_role_dict["role"] = new_role

    if new_role_match:
        new_index, _result = new_role_match
        role_list[new_index] = new_role_dict
    else:
        role_list.append(new_role_dict)

    return role_list


def main():
    """Define the program entrypoint."""
    typer.run(clone_role)


if __name__ == "__main__":
    main()
