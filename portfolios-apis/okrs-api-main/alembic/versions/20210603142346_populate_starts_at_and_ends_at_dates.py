"""populate starts at and ends at dates

Revision ID: 20210603142346
Revises: 20210526114642
Create Date: 2021-06-03 14:23:47.999807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210603142346"
down_revision = "20210526114642"
branch_labels = None
depends_on = None


def upgrade():
    # Set the objectives `starts_at` and `ends_at` columns to now() if
    # they were null.
    op.execute("update objectives SET starts_at = now() where starts_at IS NULL")
    op.execute("update objectives SET ends_at = now() where ends_at IS NULL")

    # This allows us to set the key results [null] `starts_at` and `ends_at`
    # columns to their Objective's counterparts with confidence, knowing that we
    # won't still be setting the key_results timeframe columns to null.
    op.execute(
        "update key_results "
        "SET starts_at = objectives.starts_at "
        "from objectives "
        "where key_results.starts_at IS NULL "
        "and key_results.objective_id = objectives.id"
    )
    op.execute(
        "update key_results "
        "SET ends_at = objectives.ends_at "
        "from objectives "
        "where key_results.ends_at IS NULL "
        "and key_results.objective_id = objectives.id"
    )


def downgrade():
    pass
    # Irreversible migration!!
