"""convert columns to timestamptz

Revision ID: 20201001100516
Revises: 20200921152000
Create Date: 2020-10-01 10:05:16.597589

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201001100516"
down_revision = "20200921152000"
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
DEFAULT_TIMESTAMP_COLUMNS = ["created_at", "updated_at"]
ADDITIONAL_TIMESTAMP_COLUMNS = ["achieved_at", "starts_at", "ends_at"]
ADDITIONAL_TIMESTAMP_TABLES = ["objectives", "key_results"]


def columns_for_table(table_name):
    columns = DEFAULT_TIMESTAMP_COLUMNS.copy()
    if table_name in ADDITIONAL_TIMESTAMP_TABLES:
        columns.extend(ADDITIONAL_TIMESTAMP_COLUMNS)
    return columns


def migrate_tz(use_timezone=True):
    for table_name in ALL_TABLES:
        with op.batch_alter_table(table_name) as batch_op:
            for column_name in columns_for_table(table_name):
                batch_op.alter_column(
                    column_name, type_=sa.DateTime(timezone=use_timezone)
                )


# Alembic Migrations below


def upgrade():
    migrate_tz(True)


def downgrade():
    migrate_tz(False)
