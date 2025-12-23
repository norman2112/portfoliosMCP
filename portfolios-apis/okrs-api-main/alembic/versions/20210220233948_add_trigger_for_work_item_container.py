"""Add trigger for work_item_container

Revision ID: 20210220233948
Revises: 20210217143120
Create Date: 2021-02-20 23:39:52.724036

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210220233948"
down_revision = "20210217143120"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_wic_level_depth_default_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "level_okay boolean; "
        "BEGIN "
        "IF NEW.level_depth_default IS NOT NULL THEN "
        "SELECT EXISTS INTO level_okay ( "
        "SELECT lc.depth "
        "FROM ( "
        "SELECT CAST(obj.val->>'depth' AS INTEGER) AS depth "
        "FROM settings "
        "JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val->>'depth' AS INTEGER) > -1 "
        "WHERE tenant_id_str = NEW.tenant_id_str "
        ") lc "
        "WHERE lc.depth = NEW.level_depth_default "
        "); "
        "IF NOT level_okay THEN "
        "RAISE EXCEPTION "
        "'work_item_container (id: %, level_depth_default: %) level_depth_default is invalid', "
        "NEW.id, NEW.level_depth_default; "
        "END IF; "
        "END IF; "
        "RETURN NEW; "
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_wic_level_depth_default "
        "BEFORE INSERT OR UPDATE OF level_depth_default ON work_item_containers "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_wic_level_depth_default_function();"
    )
    op.execute(
        "ALTER TABLE work_item_containers ENABLE TRIGGER check_wic_level_depth_default;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE work_item_containers DISABLE TRIGGER check_wic_level_depth_default;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_wic_level_depth_default ON work_item_containers;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_wic_level_depth_default_function;")
