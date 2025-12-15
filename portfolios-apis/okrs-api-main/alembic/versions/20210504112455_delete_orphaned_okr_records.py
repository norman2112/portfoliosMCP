"""delete orphaned okr records

Revision ID: 20210504112455
Revises: 20210415143946
Create Date: 2021-05-04 11:25:01.198958

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210504112455"
down_revision = "20210415143946"
branch_labels = None
depends_on = None


def upgrade():
    """Delete orphaned objectives, key results, and progress points."""
    op.execute("DELETE FROM objectives where work_item_container_id IS NULL")
    op.execute("DELETE FROM key_results where objective_id IS NULL")
    op.execute("DELETE FROM progress_points where key_result_id IS NULL")


def downgrade():
    """Irreversible migration."""
    pass
