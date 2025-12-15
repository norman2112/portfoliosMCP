"""add timestamps to wic roles

Revision ID: 20210805163137
Revises: 20210729151505
Create Date: 2021-08-05 16:31:39.770504

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20210805163137"
down_revision = "20210729151505"
branch_labels = None
depends_on = None


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


# Begin Alembic Migrations


def upgrade():
    op.alter_column(
        "work_item_container_roles",
        "updated_at",
        existing_type=postgresql.TIMESTAMP(),
        nullable=True,
        server_default=sa.text("now()"),
    )
    op.alter_column(
        "work_item_container_roles",
        "created_at",
        existing_type=postgresql.TIMESTAMP(),
        nullable=True,
        server_default=sa.text("now()"),
    )
    op.execute(drop_trigger_sql("work_item_container_roles"))
    op.execute(add_trigger_sql("work_item_container_roles"))


def downgrade():
    op.execute(drop_trigger_sql("work_item_container_roles"))
