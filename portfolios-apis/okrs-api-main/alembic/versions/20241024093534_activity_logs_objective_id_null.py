"""activity_logs_objective_id_null

Revision ID: 20241024093534
Revises: 20241004134758
Create Date: 2024-10-24 09:35:38.633371

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241024093534"
down_revision = "20241004134758"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE activity_logs ALTER COLUMN objective_id DROP NOT NULL;")


def downgrade():
    op.execute("ALTER TABLE activity_logs ALTER COLUMN objective_id BIGINT NULL;")
