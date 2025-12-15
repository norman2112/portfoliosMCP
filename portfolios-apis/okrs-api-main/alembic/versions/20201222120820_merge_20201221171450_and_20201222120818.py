"""merge 20201221171450 and 20201222120818

Revision ID: 20201222120820
Revises: 20201221171450, 20201222120818
Create Date: 2020-12-22 14:38:07.645616

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201222120820"
down_revision = ("20201221171450", "20201222120818")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
