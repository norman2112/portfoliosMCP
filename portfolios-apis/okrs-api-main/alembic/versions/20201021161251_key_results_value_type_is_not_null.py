"""key results value type is not null

Revision ID: 20201021161251
Revises: 20201020150945
Create Date: 2020-10-21 16:12:52.653748

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201021161251"
down_revision = "20201020150945"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("key_results", "value_type", nullable=False, server_default="count")


def downgrade():
    op.alter_column("key_results", "value_type", nullable=True, server_default=None)
