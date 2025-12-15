"""merge heads

Revision ID: 20210205100957
Revises: 20210204082127, 20210203124757
Create Date: 2021-02-05 10:09:58.758951

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210205100957"
down_revision = ("20210204082127", "20210203124757")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
