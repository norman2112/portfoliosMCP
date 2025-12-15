"""Resoving multiple heads

Revision ID: 20210524143947
Revises: 20210521121214, 20210520153717
Create Date: 2021-05-24 14:39:48.730119

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210524143947"
down_revision = ("20210521121214", "20210520153717")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
