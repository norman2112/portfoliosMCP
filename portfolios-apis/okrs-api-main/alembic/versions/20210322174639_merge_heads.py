"""Merge heads

Revision ID: 20210322174639
Revises: 20210322131038, 20210317142948
Create Date: 2021-03-22 17:46:41.566820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210322174639"
down_revision = ("20210322131038", "20210317142948")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
