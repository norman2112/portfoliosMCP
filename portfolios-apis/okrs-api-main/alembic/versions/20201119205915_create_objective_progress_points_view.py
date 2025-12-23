"""Create objective_progress_points_view

Revision ID: 20201119205915
Revises: 20201119205629
Create Date: 2020-11-19 20:59:16.225810

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201119205915"
down_revision = "20201119205629"
branch_labels = None
depends_on = None

VIEW_NAME = "objective_progress_points_view"
VIEW_SQL = (
    f"CREATE OR REPLACE VIEW {VIEW_NAME} AS "
    "SELECT objective_id, progress_points.* "
    "FROM key_results LEFT JOIN progress_points "
    "ON key_results.id = progress_points.key_result_id"
)


def upgrade():
    op.execute(VIEW_SQL)


def downgrade():
    op.execute(f"DROP VIEW IF EXISTS {VIEW_NAME}")
