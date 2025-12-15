"""views with deleted at epoch

Revision ID: 20210816113628
Revises: 20210809100526
Create Date: 2021-08-16 11:36:32.057743

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20210816113628"
down_revision = "20210809100526"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP VIEW IF EXISTS objective_progress_points_view")
    op.execute(
        """
        CREATE OR REPLACE VIEW objective_progress_points_view
        AS SELECT key_results.objective_id,
        progress_points.id,
        progress_points.value,
        progress_points.created_at,
        progress_points.updated_at,
        progress_points.key_result_id,
        progress_points.measured_at,
        progress_points.key_result_progress_percentage,
        progress_points.objective_progress_percentage,
        progress_points.comment,
        progress_points.app_created_by,
        progress_points.app_last_updated_by
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
        key_results.id,
        key_results.name,
        key_results.description,
        key_results.starting_value,
        key_results.target_value,
        key_results.value_type,
        key_results.objective_id,
        key_results.achieved_at,
        key_results.ends_at,
        key_results.starts_at,
        key_results.created_at,
        key_results.updated_at,
        key_results.data_source,
        key_results.progress_percentage
        FROM key_result_work_item_mappings mappings
        LEFT JOIN key_results ON mappings.key_result_id = key_results.id
        WHERE key_results.deleted_at_epoch = 0
        """
    )


def downgrade():
    op.execute("DROP VIEW IF EXISTS objective_progress_points_view")
    op.execute(
        """
        CREATE OR REPLACE VIEW objective_progress_points_view
        AS SELECT key_results.objective_id,
        progress_points.id,
        progress_points.value,
        progress_points.created_at,
        progress_points.updated_at,
        progress_points.key_result_id,
        progress_points.measured_at,
        progress_points.key_result_progress_percentage,
        progress_points.objective_progress_percentage,
        progress_points.comment,
        progress_points.app_created_by,
        progress_points.app_last_updated_by
        FROM key_results
        LEFT JOIN progress_points ON key_results.id = progress_points.key_result_id
        """
    )

    op.execute("DROP VIEW IF EXISTS work_item_key_results_view")
    op.execute(
        """
        CREATE OR REPLACE VIEW work_item_key_results_view
        AS SELECT mappings.work_item_id,
        key_results.id,
        key_results.name,
        key_results.description,
        key_results.starting_value,
        key_results.target_value,
        key_results.value_type,
        key_results.objective_id,
        key_results.achieved_at,
        key_results.ends_at,
        key_results.starts_at,
        key_results.created_at,
        key_results.updated_at,
        key_results.data_source,
        key_results.progress_percentage
        FROM key_result_work_item_mappings mappings
        LEFT JOIN key_results ON mappings.key_result_id = key_results.id
        """
    )
