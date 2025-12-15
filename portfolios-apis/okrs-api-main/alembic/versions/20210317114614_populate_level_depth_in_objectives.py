"""populate level depth in objectives

Revision ID: 20210317114614
Revises: 20210316110558
Create Date: 2021-03-17 11:46:15.703508

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210317114614"
down_revision = "20210316110558"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE objectives SET level_depth = 3 WHERE level_depth IS NULL")


def downgrade():
    print("!! NO-OP IRREVERSIBLE MIGRATION !!")
