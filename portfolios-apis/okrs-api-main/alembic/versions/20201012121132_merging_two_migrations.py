"""merging two migrations

Revision ID: 20201012121132
Revises: 20201011153601, 20201012121131
Create Date: 2020-10-12 12:57:21.021416

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201012121132"
down_revision = ("20201011153601", "20201012121131")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
