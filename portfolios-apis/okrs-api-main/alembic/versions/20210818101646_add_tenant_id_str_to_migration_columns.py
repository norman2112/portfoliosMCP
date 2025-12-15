"""add tenant_id_str to migration columns

Revision ID: 20210818101646
Revises: 20210816162507
Create Date: 2021-08-18 10:16:51.723087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210818101646"
down_revision = "20210816162507"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP VIEW IF EXISTS objective_progress_points_view")
    op.execute(
        """
        CREATE OR REPLACE VIEW objective_progress_points_view
        AS SELECT key_results.objective_id,
        progress_points.*
        FROM key_results
        LEFT JOIN progress_points ON key_results.id = progress_points.key_result_id
        WHERE key_results.deleted_at_epoch = 0
        """
    )

    op.execute("DROP VIEW IF EXISTS work_item_key_results_view")
    op.execute(
        """
        CREATE OR REPLACE VIEW work_item_key_results_view
        AS SELECT mappings.work_item_id,
        key_results.*
        FROM key_result_work_item_mappings mappings
        LEFT JOIN key_results ON mappings.key_result_id = key_results.id
        WHERE key_results.deleted_at_epoch = 0
        """
    )


def downgrade():
    # Irreversible migration!!
    pass
