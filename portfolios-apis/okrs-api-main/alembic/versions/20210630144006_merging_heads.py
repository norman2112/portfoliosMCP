"""merging heads

Revision ID: 20210630144006
Revises: 20210630102223, 20210629095514
Create Date: 2021-06-30 14:40:07.890087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210630144006"
down_revision = ("20210630102223", "20210629095514")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
