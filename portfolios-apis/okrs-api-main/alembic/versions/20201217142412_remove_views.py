"""Remove views

Revision ID: 20201217142412
Revises: 20201215135933
Create Date: 2020-12-17 14:24:12.987396

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201217142412"
down_revision = "20201215135933"
branch_labels = None
depends_on = None

KR_VIEW_NAME = "key_result_work_items_view"
WI_VIEW_NAME = "work_item_key_results_view"
SPACE_VIEW_NAME = "space_work_item_containers_view"
WIC_VIEW_NAME = "work_item_container_spaces_view"


def upgrade():
    op.execute(f"DROP VIEW IF EXISTS {KR_VIEW_NAME}")
    op.execute(f"DROP VIEW IF EXISTS {WI_VIEW_NAME}")
    op.execute(f"DROP VIEW IF EXISTS {SPACE_VIEW_NAME}")
    op.execute(f"DROP VIEW IF EXISTS {WIC_VIEW_NAME}")


def downgrade():
    pass
