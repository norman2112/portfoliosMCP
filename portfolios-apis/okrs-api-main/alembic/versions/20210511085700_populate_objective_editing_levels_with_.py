"""populate objective editing levels with default

Revision ID: 20210511085700
Revises: 20210507143715
Create Date: 2021-05-11 08:57:02.266999

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210511085700"
down_revision = "20210507143715"
branch_labels = None
depends_on = None


def upgrade():
    # Set any objective editing levels that were set to NULL to the default `[0,1,2,3]`
    op.execute(
        "update work_item_containers set objective_editing_levels = '[0,1,2,3]' "
        "where work_item_containers.objective_editing_levels is NULL"
    )


def downgrade():
    # irreversible migration
    pass
