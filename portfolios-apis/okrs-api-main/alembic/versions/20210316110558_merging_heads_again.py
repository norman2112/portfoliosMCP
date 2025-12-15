"""Merging heads again

Revision ID: 20210316110558
Revises: 20210312182753, 20210312161007
Create Date: 2021-03-16 11:05:59.395713

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210316110558"
down_revision = ("20210312182753", "20210312161007")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
