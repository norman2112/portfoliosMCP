"""set_objective_editing_levels trigger

Revision ID: 20210521121214
Revises: 20210512161113
Create Date: 2021-05-21 12:12:23.125866

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210521121214"
down_revision = "20210512161113"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION set_wic_objective_editing_levels_and_level_depth_default_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "default_level_depth TEXT; "
        "BEGIN "
        "SELECT CAST(obj.val->>'depth' AS TEXT) INTO default_level_depth "
        "FROM settings "
        "JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val->>'depth' AS INTEGER) > -1 "
        "WHERE tenant_id_str = NEW.tenant_id_str "
        "AND CAST(obj.val->>'is_default' AS BOOLEAN) IS TRUE; "
        "NEW.level_depth_default = default_level_depth::int; "
        "NEW.objective_editing_levels = CONCAT('[', default_level_depth, ']'); "
        "RETURN NEW; "
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER set_wic_objective_editing_levels_and_level_depth_default "
        "BEFORE INSERT ON work_item_containers "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE set_wic_objective_editing_levels_and_level_depth_default_function();"
    )
    op.execute(
        "ALTER TABLE work_item_containers ENABLE TRIGGER set_wic_objective_editing_levels_and_level_depth_default;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE work_item_containers DISABLE TRIGGER set_wic_objective_editing_levels_and_level_depth_default;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS set_wic_objective_editing_levels_and_level_depth_default on work_item_containers;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS set_wic_objective_editing_levels_and_level_depth_default_function;"
    )
