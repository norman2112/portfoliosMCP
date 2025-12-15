"""Merge heads

Revision ID: 20210217143120
Revises: 20210215141941, 20210217115341
Create Date: 2021-02-17 14:31:21.987596

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210217143120"
down_revision = ("20210215141941", "20210217115341")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
