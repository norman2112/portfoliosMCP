"""Merge heads

Revision ID: 20210329081202
Revises: 20210326104550, 20210328121220
Create Date: 2021-03-29 08:12:04.828969

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210329081202"
down_revision = ("20210326104550", "20210328121220")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
