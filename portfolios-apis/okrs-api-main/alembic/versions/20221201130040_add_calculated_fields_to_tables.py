"""Add calculated fields to tables

Revision ID: 20221201130040
Revises: 20221118110041
Create Date: 2022-12-01 13:00:45.810005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20221201130040"
down_revision = "20221118110041"
branch_labels = None
depends_on = None


def upgrade():
    # Migrations for objectives
    op.execute(
        "alter table objectives "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_objectives_pv_tenant_id",
        "objectives",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table objectives "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_objectives_pv_created_by",
        "objectives",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table objectives "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_objectives_pv_last_updated_by",
        "objectives",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for key_results
    op.execute(
        "alter table key_results "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_key_results_pv_tenant_id",
        "key_results",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table key_results "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_key_results_pv_created_by",
        "key_results",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table key_results "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_key_results_pv_last_updated_by",
        "key_results",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for key_result_work_item_mappings
    op.execute(
        "alter table key_result_work_item_mappings "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_key_result_work_item_mappings_pv_tenant_id",
        "key_result_work_item_mappings",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table key_result_work_item_mappings "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_key_result_work_item_mappings_pv_created_by",
        "key_result_work_item_mappings",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table key_result_work_item_mappings "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_key_result_work_item_mappings_pv_last_updated_by",
        "key_result_work_item_mappings",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for activity_logs
    op.execute(
        "alter table activity_logs "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_activity_logs_pv_tenant_id",
        "activity_logs",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table activity_logs "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_activity_logs_pv_created_by",
        "activity_logs",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table activity_logs "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_activity_logs_pv_last_updated_by",
        "activity_logs",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for progress_points
    op.execute(
        "alter table progress_points "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_progress_points_pv_tenant_id",
        "progress_points",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table progress_points "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_progress_points_pv_created_by",
        "progress_points",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table progress_points "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_progress_points_pv_last_updated_by",
        "progress_points",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for settings
    op.execute(
        "alter table settings "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_settings_pv_tenant_id",
        "settings",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table settings "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_settings_pv_created_by",
        "settings",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table settings "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_settings_pv_last_updated_by",
        "settings",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for work_item_container_roles
    op.execute(
        "alter table work_item_container_roles "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_item_container_roles_pv_tenant_id",
        "work_item_container_roles",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table work_item_container_roles "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_item_container_roles_pv_created_by",
        "work_item_container_roles",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table work_item_container_roles "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_item_container_roles_pv_last_updated_by",
        "work_item_container_roles",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for work_item_containers
    op.execute(
        "alter table work_item_containers "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_item_containers_pv_tenant_id",
        "work_item_containers",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table work_item_containers "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_item_containers_pv_created_by",
        "work_item_containers",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table work_item_containers "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_item_containers_pv_last_updated_by",
        "work_item_containers",
        ["pv_last_updated_by"],
        unique=False,
    )

    # Migrations for work_items
    op.execute(
        "alter table work_items "
        "  add column pv_tenant_id varchar generated always as "
        "    (case "
        "      when (tenant_group_id_str is not null) and "
        "           (tenant_group_id_str <> '') then tenant_group_id_str "
        "      else tenant_id_str "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_items_pv_tenant_id",
        "work_items",
        ["pv_tenant_id"],
        unique=False,
    )

    op.execute(
        "alter table work_items "
        "  add column pv_created_by varchar generated always as "
        "    (case "
        "      when (created_by is not null) and "
        "           (created_by <> '') then created_by "
        "      else app_created_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_items_pv_created_by",
        "work_items",
        ["pv_created_by"],
        unique=False,
    )

    op.execute(
        "alter table work_items "
        "  add column pv_last_updated_by varchar generated always as "
        "    (case "
        "      when (last_updated_by is not null) and "
        "           (last_updated_by <> '') then last_updated_by "
        "      else app_last_updated_by "
        "     end) stored; "
    )

    op.create_index(
        "ix_work_items_pv_last_updated_by",
        "work_items",
        ["pv_last_updated_by"],
        unique=False,
    )


def downgrade():
    # Migrations for objectives
    op.execute("alter table objectives " "  drop column pv_tenant_id; ")

    op.execute("alter table objectives " "  drop column pv_created_by; ")

    op.execute("alter table objectives " "  drop column pv_last_updated_by; ")

    # Migrations for key_results
    op.execute("alter table key_results " "  drop column pv_tenant_id; ")

    op.execute("alter table key_results " "  drop column pv_created_by; ")

    op.execute("alter table key_results " "  drop column pv_last_updated_by; ")

    # Migrations for key_result_work_item_mappings
    op.execute(
        "alter table key_result_work_item_mappings " "  drop column pv_tenant_id; "
    )

    op.execute(
        "alter table key_result_work_item_mappings " "  drop column pv_created_by; "
    )

    op.execute(
        "alter table key_result_work_item_mappings "
        "  drop column pv_last_updated_by; "
    )

    # Migrations for activity_logs
    op.execute("alter table activity_logs " "  drop column pv_tenant_id; ")

    op.execute("alter table activity_logs " "  drop column pv_created_by; ")

    op.execute("alter table activity_logs " "  drop column pv_last_updated_by; ")

    # Migrations for progress_points
    op.execute("alter table progress_points " "  drop column pv_tenant_id; ")

    op.execute("alter table progress_points " "  drop column pv_created_by; ")

    op.execute("alter table progress_points " "  drop column pv_last_updated_by; ")

    # Migrations for settings
    op.execute("alter table settings " "  drop column pv_tenant_id; ")

    op.execute("alter table settings " "  drop column pv_created_by; ")

    op.execute("alter table settings " "  drop column pv_last_updated_by; ")

    # Migrations for work_item_container_roles
    op.execute("alter table work_item_container_roles " "  drop column pv_tenant_id; ")

    op.execute("alter table work_item_container_roles " "  drop column pv_created_by; ")

    op.execute(
        "alter table work_item_container_roles " "  drop column pv_last_updated_by; "
    )

    # Migrations for work_item_containers
    op.execute("alter table work_item_containers " "  drop column pv_tenant_id; ")

    op.execute("alter table work_item_containers " "  drop column pv_created_by; ")

    op.execute("alter table work_item_containers " "  drop column pv_last_updated_by; ")

    # Migrations for work_items
    op.execute("alter table work_items " "  drop column pv_tenant_id; ")

    op.execute("alter table work_items " "  drop column pv_created_by; ")

    op.execute("alter table work_items " "  drop column pv_last_updated_by; ")
