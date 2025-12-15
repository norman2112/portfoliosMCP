"""Script to generate a bunch of SQLs for migrating a tenant_id_str in DB to a different one."""

import sys

OKRS_TABLE_LIST = [
    "activity_logs",
    "key_result_work_item_mappings",
    "key_results",
    "objectives",
    "progress_points",
    "settings",
    "work_item_container_roles",
    "work_item_containers",
    "work_items",
]

FIELD_TO_MIGRATE = "tenant_id_str"

UPDATE_STATEMENT = """
UPDATE {table}
    set {field} = '{new_value}'
WHERE
    {field} = '{old_value}';
"""

SELECT_STATEMENT = """
SELECT * FROM {table}
WHERE {field} = '{old_value}';
"""


def generate_update_statement(table_name, field, old_value, new_value):
    """Generate a single update statement for a table."""

    return UPDATE_STATEMENT.format(
        table=table_name, field=field, old_value=old_value, new_value=new_value
    )


def generate_select_statement(table_name, field, old_value):
    """Generate a single select statement for a table."""

    return SELECT_STATEMENT.format(table=table_name, field=field, old_value=old_value)


def print_all_updates(field, old_value, new_value):
    """Print update for all tables."""

    for table in OKRS_TABLE_LIST:
        print(generate_update_statement(table, field, old_value, new_value))


def print_all_selects(field, old_value):
    """Print select for all tables."""

    for table in OKRS_TABLE_LIST:
        print(generate_select_statement(table, field, old_value))


def usage():
    """Print out usage message."""

    print("Arguments: (run | dry_run) <old_tenant> <new_tenant>")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        usage()
        sys.exit(1)

    old_value = sys.argv[2]
    new_value = sys.argv[3]

    if sys.argv[1].lower() == "dry_run":
        print_all_selects(FIELD_TO_MIGRATE, old_value)
    elif sys.argv[1].lower() == "run":
        print_all_updates(FIELD_TO_MIGRATE, old_value, new_value)
    else:
        usage()
