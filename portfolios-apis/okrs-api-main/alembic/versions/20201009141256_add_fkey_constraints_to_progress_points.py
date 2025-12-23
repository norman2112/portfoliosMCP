"""Add fkey constraints to progress points

Revision ID: 20201009141256
Revises: 20201006134829
Create Date: 2020-10-09 14:12:57.134865

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20201009141256"
down_revision = "20201006134829"
branch_labels = None
depends_on = None

CHECK_SQL = (
    "("
    "(objective_id is not null)::integer +"
    "(key_result_id is not null)::integer"
    ") = 1"
)

CHECK_CONSTRAINT_NAME = "mutually_exclusive_fk_check"


def upgrade():
    op.create_check_constraint(CHECK_CONSTRAINT_NAME, "progress_points", CHECK_SQL)


def downgrade():
    op.drop_constraint(CHECK_CONSTRAINT_NAME, "progress_points")
