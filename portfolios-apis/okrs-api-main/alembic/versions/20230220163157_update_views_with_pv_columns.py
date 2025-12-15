"""update views with pv columns

Revision ID: 20230220163157
Revises: 20221118110041
Create Date: 2023-02-20 16:32:03.837650

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20230220163157"
down_revision = "20221201130040"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP VIEW IF EXISTS key_result_work_items_view")
    op.execute(
        "CREATE OR REPLACE VIEW key_result_work_items_view AS "
        "SELECT mappings.key_result_id, "
        "work_items.id, "
        "work_items.state, "
        "work_items.work_item_container_id, "
        "work_items.created_at, "
        "work_items.updated_at, "
        "work_items.item_type, "
        "work_items.planned_finish, "
        "work_items.planned_start, "
        "work_items.title, "
        "work_items.external_id, "
        "work_items.external_type, "
        "work_items.tenant_id_str, "
        "work_items.tenant_group_id_str, "
        "work_items.created_by, "
        "work_items.last_updated_by, "
        "work_items.pv_tenant_id, "
        "work_items.pv_created_by, "
        "work_items.pv_last_updated_by "
        "FROM (key_result_work_item_mappings mappings "
        "LEFT JOIN work_items ON ((mappings.work_item_id = work_items.id))); "
    )

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
    op.execute("DROP VIEW IF EXISTS key_result_work_items_view")
    op.execute(
        "CREATE OR REPLACE VIEW key_result_work_items_view AS "
        "SELECT mappings.key_result_id, "
        "work_items.id, "
        "work_items.state, "
        "work_items.work_item_container_id, "
        "work_items.created_at, "
        "work_items.updated_at, "
        "work_items.item_type, "
        "work_items.planned_finish, "
        "work_items.planned_start, "
        "work_items.title, "
        "work_items.external_id, "
        "work_items.external_type, "
        "work_items.tenant_id_str, "
        "work_items.pv_tenant_id, "
        "work_items.pv_created_by, "
        "work_items.pv_last_updated_by "
        "FROM (key_result_work_item_mappings mappings "
        "LEFT JOIN work_items ON ((mappings.work_item_id = work_items.id))); "
    )

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
