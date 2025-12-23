"""re-add work item views

Revision ID: 20201217145546
Revises: 20201217145503
Create Date: 2020-12-17 14:55:47.519828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201217145546"
down_revision = "20201217145503"
branch_labels = None
depends_on = None


KR_VIEW_NAME = "key_result_work_items_view"
KR_VIEW_SQL = (
    f"CREATE OR REPLACE VIEW {KR_VIEW_NAME} AS "
    "SELECT mappings.key_result_id, work_items.* "
    "FROM key_result_work_item_mappings AS mappings LEFT JOIN work_items "
    "ON mappings.work_item_id = work_items.id"
)
WI_VIEW_NAME = "work_item_key_results_view"
WI_VIEW_SQL = (
    f"CREATE OR REPLACE VIEW {WI_VIEW_NAME} AS "
    "SELECT mappings.work_item_id, key_results.* "
    "FROM key_result_work_item_mappings AS mappings LEFT JOIN key_results "
    "ON mappings.key_result_id = key_results.id"
)

SPACE_VIEW_NAME = "space_work_item_containers_view"
SPACE_VIEW_SQL = (
    f"CREATE OR REPLACE VIEW {SPACE_VIEW_NAME} AS "
    "SELECT mappings.space_id, wics.* "
    "FROM space_work_item_container_mappings AS mappings "
    "LEFT JOIN work_item_containers AS wics "
    "ON mappings.work_item_container_id = wics.id"
)

WIC_VIEW_NAME = "work_item_container_spaces_view"
WIC_VIEW_SQL = (
    f"CREATE OR REPLACE VIEW {WIC_VIEW_NAME} AS "
    "SELECT mappings.work_item_container_id, spaces.* "
    "FROM space_work_item_container_mappings AS mappings "
    "LEFT JOIN spaces "
    "ON mappings.space_id = spaces.id"
)


def upgrade():
    op.execute(KR_VIEW_SQL)
    op.execute(WI_VIEW_SQL)
    op.execute(SPACE_VIEW_SQL)
    op.execute(WIC_VIEW_SQL)


def downgrade():
    op.execute(f"DROP VIEW IF EXISTS {KR_VIEW_NAME}")
    op.execute(f"DROP VIEW IF EXISTS {WI_VIEW_NAME}")
    op.execute(f"DROP VIEW IF EXISTS {SPACE_VIEW_NAME}")
    op.execute(f"DROP VIEW IF EXISTS {WIC_VIEW_NAME}")
