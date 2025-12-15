# flake8: noqa: F401
"""Generate migration to remove old or renamed event triggers from hasura invocations."""

import typer


MIGRATION_TEMPLATE = """
from pathlib import Path
from sqlalchemy import text
import yaml

HASURA_METADATA_TABLE_FILE = Path("./hasura/metadata/tables.yaml")

def make_trigger_group(trigger_dict):
    # Return the hasuran notifier trigger names for a single trigger.
    allowed_ops = ["insert", "update", "delete"]
    name = f"notify_hasura_{trigger_dict['name']}"
    all_ops = trigger_dict["definition"].keys()
    found_ops = [op for op in all_ops if op in allowed_ops]
    return [
        f"{name}_{op.upper()}"
        for op in found_ops
    ]


def convert_hasura_triggers(triggers):
    # Convert trigger dicts to a hasura notifier trigger.
    if not triggers:
        return None

    trigger_groups = [
        make_trigger_group(trigger_dict)
        for trigger_dict in triggers
    ]

    # flatten the list
    return [
        name
        for group in trigger_groups
        for name in group
    ]

with open(HASURA_METADATA_TABLE_FILE, 'r') as stream:
    try:
        HASURA_METADATA = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


def drop_all_unused_trigger_logs_sql(allowed_trigger_names):
    quoted_trigger_names = [f"'{name}'" for name in allowed_trigger_names]
    allowed_triggers_str = ", ".join(quoted_trigger_names)
    return (
        "DO $$ "
        "BEGIN "
        "IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'hdb_catalog') "
        "THEN "
        "DELETE FROM hdb_catalog.event_invocation_logs "
        "WHERE event_id IN ( "
        "SELECT id FROM hdb_catalog.event_log "
        f"WHERE trigger_name NOT IN ({allowed_triggers_str}) ); "
        "DELETE FROM hdb_catalog.event_log "
        f"WHERE trigger_name NOT IN ({allowed_triggers_str});"
        "END IF; "
        "END "
        "$$"
    )

# SQL used to get a full postgres trigger list, along with table names
TRIGGER_LIST_SQL = (
    "select event_object_table as table_name, trigger_name "
    "from information_schema.triggers "
    "where trigger_name like 'notify_hasura_%';"
)

# Return a dict of table_name:[current allowed postgres triggers]
CURRENT_PG_TRIGGERS = {
    table_obj["table"]["name"]: convert_hasura_triggers(table_obj.get("event_triggers", []))
    for table_obj in HASURA_METADATA
}

CURRENT_HASURA_TRIGGER_NAMES = [
    trigger_obj["name"]
    for table_obj in HASURA_METADATA
    for trigger_obj in table_obj.get("event_triggers", [])
]

def ok_to_delete_pg_trigger(table_name, trigger_name):
    # Returns bool if trigger is not found in current triggers.
    triggers_for_table = CURRENT_PG_TRIGGERS.get(table_name, [])
    return trigger_name not in triggers_for_table


def upgrade():
    print("Cleaning up Postgres Event Triggers and Hasura Event Trigger logs...")
    engine = op.get_bind()
    with engine.connect() as connection:
        result = connection.execute(text(TRIGGER_LIST_SQL))
        for row in result:
            table_name, trigger_name = row
            if ok_to_delete_pg_trigger(table_name, trigger_name):
                print(f"!! trigger ({trigger_name}) in {table_name} is unused. DELETING...")
                op.execute(
                    "DROP TRIGGER IF EXISTS "
                    f'"{trigger_name}" '
                    f"ON {table_name} CASCADE;"
                )

        print(f"{CURRENT_HASURA_TRIGGER_NAMES=}")
        print("!! Dropping all hasura triggers not in this list.")
        cmd = drop_all_unused_trigger_logs_sql(CURRENT_HASURA_TRIGGER_NAMES)
        # delete all other hasura event logs from the table
        op.execute(cmd)

def downgrade():
    print("!!! No-op. Irreversible Migration!")
"""


def replace_migration_text(migration_filename: str):
    """Add the migration template into the specified migration."""

    with open(f"alembic/versions/{migration_filename}.py", "r+") as f:
        data = f.read()
        f.seek(data.find("def upgrade"))
        f.write(MIGRATION_TEMPLATE)
        f.truncate()


def main():
    """Define the program entrypoint."""
    typer.run(replace_migration_text)


if __name__ == "__main__":
    main()
