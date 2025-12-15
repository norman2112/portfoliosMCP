"""merging heads

Revision ID: 20210729151505
Revises: 20210729141331, 20210713145550
Create Date: 2021-07-29 15:15:07.693824

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210729151505"
down_revision = ("20210729141331", "20210713145550")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
