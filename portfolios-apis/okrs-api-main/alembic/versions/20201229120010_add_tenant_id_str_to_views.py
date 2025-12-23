"""Add tenant_id_str to views

Revision ID: 20201229120010
Revises: 20201222120820
Create Date: 2020-12-29 12:00:11.495860

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201229120010"
down_revision = "20201222120820"
branch_labels = None
depends_on = None


def upgrade():
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
        "work_items.tenant_id_str "
        "FROM (key_result_work_item_mappings mappings "
        "LEFT JOIN work_items ON ((mappings.work_item_id = work_items.id))); "
    )
    op.execute(
        "CREATE OR REPLACE VIEW objective_progress_points_view AS "
        "SELECT key_results.objective_id ,"
        "progress_points.id, "
        "progress_points.value, "
        "progress_points.created_at, "
        "progress_points.updated_at, "
        "progress_points.key_result_id, "
        "progress_points.measured_at, "
        "progress_points.key_result_progress_percentage,"
        "progress_points.objective_progress_percentage,"
        "progress_points.tenant_id_str "
        "FROM (key_results "
        "LEFT JOIN progress_points ON ((key_results.id = progress_points.key_result_id)));"
    )
    op.execute(
        "CREATE OR REPLACE VIEW space_work_item_containers_view AS "
        "SELECT mappings.space_id, "
        "wics.id, "
        "wics.created_at, "
        "wics.updated_at, "
        "wics.external_title, "
        "wics.external_id, "
        "wics.external_type, "
        "wics.tenant_id_str "
        "FROM (space_work_item_container_mappings mappings "
        "LEFT JOIN work_item_containers wics ON ((mappings.work_item_container_id = wics.id)));"
    )
    op.execute(
        "CREATE OR REPLACE VIEW work_item_container_spaces_view AS "
        "SELECT mappings.work_item_container_id, "
        "spaces.id, "
        "spaces.name, "
        "spaces.created_at, "
        "spaces.updated_at, "
        "spaces.tenant_id_str "
        "FROM (space_work_item_container_mappings mappings "
        "LEFT JOIN spaces ON ((mappings.space_id = spaces.id)));"
    )
    op.execute(
        "CREATE OR REPLACE VIEW work_item_key_results_view AS "
        "SELECT mappings.work_item_id, "
        "key_results.id, "
        "key_results.name, "
        "key_results.description, "
        "key_results.starting_value, "
        "key_results.target_value, "
        "key_results.value_type, "
        "key_results.objective_id, "
        "key_results.achieved_at, "
        "key_results.ends_at, "
        "key_results.starts_at, "
        "key_results.created_at, "
        "key_results.updated_at, "
        "key_results.data_source, "
        "key_results.progress_percentage, "
        "key_results.tenant_id_str "
        "FROM (key_result_work_item_mappings mappings "
        "LEFT JOIN key_results ON ((mappings.key_result_id = key_results.id)));"
    )


def downgrade():
    op.execute("DROP VIEW key_result_work_items_view")
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
        "work_items.external_type "
        "FROM (key_result_work_item_mappings mappings "
        "LEFT JOIN work_items ON ((mappings.work_item_id = work_items.id))); "
    )
    op.execute("DROP VIEW objective_progress_points_view")
    op.execute(
        "CREATE OR REPLACE VIEW objective_progress_points_view AS "
        "SELECT key_results.objective_id ,"
        "progress_points.id, "
        "progress_points.value, "
        "progress_points.created_at, "
        "progress_points.updated_at, "
        "progress_points.key_result_id, "
        "progress_points.measured_at, "
        "progress_points.key_result_progress_percentage, "
        "progress_points.objective_progress_percentage "
        "FROM (key_results "
        "LEFT JOIN progress_points ON ((key_results.id = progress_points.key_result_id)));"
    )
    op.execute("DROP VIEW space_work_item_containers_view")
    op.execute(
        "CREATE OR REPLACE VIEW space_work_item_containers_view AS "
        "SELECT mappings.space_id, "
        "wics.id, "
        "wics.created_at, "
        "wics.updated_at, "
        "wics.external_title, "
        "wics.external_id, "
        "wics.external_type "
        "FROM (space_work_item_container_mappings mappings "
        "LEFT JOIN work_item_containers wics ON ((mappings.work_item_container_id = wics.id)));"
    )
    op.execute("DROP VIEW work_item_container_spaces_view")
    op.execute(
        "CREATE OR REPLACE VIEW work_item_container_spaces_view AS "
        "SELECT mappings.work_item_container_id, "
        "spaces.id, "
        "spaces.name, "
        "spaces.created_at, "
        "spaces.updated_at "
        "FROM (space_work_item_container_mappings mappings "
        "LEFT JOIN spaces ON ((mappings.space_id = spaces.id)));"
    )
    op.execute("DROP VIEW work_item_key_results_view")
    op.execute(
        "CREATE OR REPLACE VIEW work_item_key_results_view AS "
        "SELECT mappings.work_item_id, "
        "key_results.id, "
        "key_results.name, "
        "key_results.description, "
        "key_results.starting_value, "
        "key_results.target_value, "
        "key_results.value_type, "
        "key_results.objective_id, "
        "key_results.achieved_at, "
        "key_results.ends_at, "
        "key_results.starts_at, "
        "key_results.created_at, "
        "key_results.updated_at, "
        "key_results.data_source, "
        "key_results.progress_percentage "
        "FROM (key_result_work_item_mappings mappings "
        "LEFT JOIN key_results ON ((mappings.key_result_id = key_results.id)));"
    )
