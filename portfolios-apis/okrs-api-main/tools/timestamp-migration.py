"""Generate timestamp migration fields."""
from typing import List

import typer


MIGRATION_TEMPLATE = """
TIMESTAMP_COLUMNS = ["created_at", "updated_at"]


def add_trigger_sql(table_name):
    return (
        "CREATE TRIGGER set_timestamp "
        "BEFORE UPDATE "
        f"ON {table_name} "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE trigger_set_timestamp();"
    )


def drop_trigger_sql(table_name):
    return (
        f"DROP TRIGGER IF EXISTS set_timestamp ON {table_name}"
    )


def drop_timestamp_columns_sql(table_name):
    return (
        f"ALTER TABLE {table_name} "
        "DROP COLUMN IF EXISTS created_at, "
        "DROP COLUMN IF EXISTS updated_at"
    )


def create_timestamps_with_defaults(table_name):
    with op.batch_alter_table(table_name) as batch_op:
        for column_name in TIMESTAMP_COLUMNS:
            batch_op.add_column(
                sa.Column(
                    column_name,
                    sa.DateTime(timezone=True),
                    nullable=True,
                    server_default=sa.sql.func.now(),
                )
            )


# Begin Alembic Migrations


def upgrade():
    for table_name in TABLES:
        op.execute(drop_trigger_sql(table_name))
        op.execute(drop_timestamp_columns_sql(table_name))
        create_timestamps_with_defaults(table_name)
        op.execute(add_trigger_sql(table_name))


def downgrade():
    for table_name in TABLES:
        op.execute(drop_trigger_sql(table_name))
        op.execute(drop_timestamp_columns_sql(table_name))
"""


def replace_migration_text(migration_filename: str, tablenames: List[str]):
    """Add the migration template into the specified migration."""

    tables_string = (
        f"TABLES = {tablenames}".replace("(", "[").replace(")", "]").replace("'", '"')
    )
    with open(f"alembic/versions/{migration_filename}.py", "r+") as f:
        data = f.read()
        f.seek(data.find("def upgrade"))
        f.write(tables_string)
        f.write(MIGRATION_TEMPLATE)
        f.truncate()


def main():
    """Define the program entrypoint."""
    typer.run(replace_migration_text)


if __name__ == "__main__":
    main()
