"""merge 20201009093245 and 20201009141256

Revision ID: 1b42d1ec6eb8
Revises: 20201009093245, 20201009141256
Create Date: 2020-10-09 23:53:47.643635

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1b42d1ec6eb8"
down_revision = ("20201009093245", "20201009141256")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
