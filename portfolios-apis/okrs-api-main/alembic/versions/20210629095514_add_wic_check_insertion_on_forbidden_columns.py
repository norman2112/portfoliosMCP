"""add wic check constraints

Revision ID: 20210629095514
Revises: 20210629092319
Create Date: 2021-06-29 09:55:16.548208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210629095514"
down_revision = "20210629092319"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_wic_objective_editing_levels_and_level_depth_default_function()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
        AS $$
        DECLARE
        default_level_depth TEXT;
        BEGIN
        IF NEW.objective_editing_levels IS NOT NULL OR NEW.level_depth_default IS NOT NULL THEN
        RAISE EXCEPTION
        'work_item_containers objective_editing_levels and level_depth_default must both be null on insert.';
        END IF;
        SELECT CAST(obj.val->>'depth' AS TEXT) INTO default_level_depth
        FROM settings
        JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val->>'depth' AS INTEGER) > -1
        WHERE tenant_id_str = NEW.tenant_id_str
        AND CAST(obj.val->>'is_default' AS BOOLEAN) IS TRUE;
        NEW.level_depth_default = default_level_depth::int;
        NEW.objective_editing_levels = CONCAT('[', default_level_depth, ']');
        RETURN NEW;
        END;
        $$;
        """
    )


def downgrade():
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_wic_objective_editing_levels_and_level_depth_default_function()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
        AS $$
        DECLARE
        default_level_depth TEXT;
        BEGIN
        SELECT CAST(obj.val->>'depth' AS TEXT) INTO default_level_depth
        FROM settings
        JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val->>'depth' AS INTEGER) > -1
        WHERE tenant_id_str = NEW.tenant_id_str
        AND CAST(obj.val->>'is_default' AS BOOLEAN) IS TRUE;
        NEW.level_depth_default = default_level_depth::int;
        NEW.objective_editing_levels = CONCAT('[', default_level_depth, ']');
        RETURN NEW;
        END;
        $$;
        """
    )
