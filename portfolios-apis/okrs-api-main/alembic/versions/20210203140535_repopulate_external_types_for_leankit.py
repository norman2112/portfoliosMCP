"""repopulate external_types for leankit

Revision ID: 20210203140535
Revises: 20210202090215
Create Date: 2021-02-03 14:05:36.624481

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210203140535"
down_revision = "20210202090215"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE work_items SET external_type = 'leankit' WHERE external_type = 'lk_card'"
    )
    op.execute(
        "UPDATE work_item_containers SET external_type = 'leankit' WHERE external_type = 'lk_board'"
    )


def downgrade():
    op.execute(
        "UPDATE work_items SET external_type = 'lk_card' WHERE external_type = 'leankit'"
    )
    op.execute(
        "UPDATE work_item_containers SET external_type = 'lk_board' WHERE external_type = 'leankit'"
    )
