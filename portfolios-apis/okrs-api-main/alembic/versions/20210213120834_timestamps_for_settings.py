"""timestamps_for_settings

Revision ID: 20210213120834
Revises: 20210213120448
Create Date: 2021-02-13 12:08:35.815042

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210213120834"
down_revision = "20210213120448"
branch_labels = None
depends_on = None


TABLES = [
    "settings",
]
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
    return f"DROP TRIGGER IF EXISTS set_timestamp ON {table_name}"


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
