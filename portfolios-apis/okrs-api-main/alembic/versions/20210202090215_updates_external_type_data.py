"""Updates external_type data

Revision ID: 20210202090215
Revises: 20210119172936
Create Date: 2021-02-02 09:02:19.493242

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20210202090215"
down_revision = "20210119172936"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "work_items", "external_type", new_column_name="deprecated_external_type"
    )
    op.alter_column("work_items", "deprecated_external_type", nullable=True)
    op.add_column("work_items", sa.Column("external_type", sa.String(), nullable=True))
    op.execute("UPDATE work_items SET external_type = deprecated_external_type")
    op.alter_column("work_items", "external_type", nullable=False)

    op.alter_column(
        "work_item_containers",
        "external_type",
        new_column_name="deprecated_external_type",
    )
    op.alter_column("work_item_containers", "deprecated_external_type", nullable=True)
    op.add_column(
        "work_item_containers", sa.Column("external_type", sa.String(), nullable=True)
    )
    op.execute(
        "UPDATE work_item_containers SET external_type = deprecated_external_type"
    )
    op.alter_column("work_item_containers", "external_type", nullable=False)


def downgrade():
    op.execute("UPDATE work_items SET external_type = 'lk_card'")
    op.drop_column("work_items", "deprecated_external_type")

    op.execute("UPDATE work_item_containers SET external_type = 'lk_board'")
    op.drop_column("work_item_containers", "deprecated_external_type")
