"""Merging migrations

Revision ID: 20210312182753
Revises: 20210312170021, 20210310062009
Create Date: 2021-03-12 18:27:55.523007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210312182753"
down_revision = ("20210312170021", "20210310062009")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
