"""update null key result target values to zero

Revision ID: 20210119114440
Revises: 20201229120010
Create Date: 2021-01-19 11:44:41.409310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210119114440"
down_revision = "20201229120010"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE key_results SET starting_value = 0 WHERE starting_value ISNULL;"
        "UPDATE key_results SET target_value = 0 WHERE target_value ISNULL;"
    )


def downgrade():
    print(
        "Irreversible. This migration changed all null "
        "target and starting values to 0."
    )
