"""recreate timestamps and populate

Revision ID: 20201001154838
Revises: 20201001154800
Create Date: 2020-10-01 15:48:38.654077

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201001154838"
down_revision = "20201001154800"
branch_labels = None
depends_on = None


ALL_TABLES = [
    "objectives",
    "key_results",
    "spaces",
    "progress_points",
    "key_result_work_item_mappings",
    "space_work_item_container_mappings",
    "work_item_containers",
    "work_items",
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


def recreate_timestamps_with_defaults(table_name):
    with op.batch_alter_table(table_name) as batch_op:
        for column_name in TIMESTAMP_COLUMNS:
            batch_op.drop_column(column_name)
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
    for table_name in ALL_TABLES:
        recreate_timestamps_with_defaults(table_name)
        op.execute(add_trigger_sql(table_name))


def downgrade():
    for table_name in ALL_TABLES:
        op.execute(drop_trigger_sql(table_name))
