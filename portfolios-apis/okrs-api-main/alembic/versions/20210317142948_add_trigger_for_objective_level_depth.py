"""Add trigger for objective level_depth

Revision ID: 20210317142948
Revises: 20210317115339
Create Date: 2021-03-17 14:29:50.603975

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210317142948"
down_revision = "20210317115339"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_objective_level_depth_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "level_okay boolean; "
        "BEGIN "
        "SELECT EXISTS INTO level_okay ( "
        "SELECT lc.depth "
        "FROM ( "
        "SELECT CAST(obj.val->>'depth' AS INTEGER) AS depth "
        "FROM settings "
        "JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val->>'depth' AS INTEGER) > -1 "
        "WHERE tenant_id_str = NEW.tenant_id_str "
        ") lc "
        "WHERE lc.depth = NEW.level_depth "
        "); "
        "IF NOT level_okay THEN "
        "RAISE EXCEPTION "
        "'objective (id: %, level_depth: %) level_depth is invalid', "
        "NEW.id, NEW.level_depth; "
        "END IF; "
        "RETURN NEW; "
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_objective_level_depth "
        "BEFORE INSERT OR UPDATE OF level_depth ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_objective_level_depth_function();"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_parent_objective_level_depth on objectives;"
    )
    op.execute(
        "CREATE TRIGGER check_parent_objective_level_depth "
        "BEFORE INSERT OR UPDATE OF parent_objective_id, level_depth ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_parent_objective_level_depth_function();"
    )
    op.execute("ALTER TABLE objectives ENABLE TRIGGER check_objective_level_depth;")


def downgrade():
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_parent_objective_level_depth;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_parent_objective_level_depth on objectives;"
    )
    op.execute(
        "CREATE TRIGGER check_parent_objective_level_depth "
        "BEFORE INSERT OR UPDATE OF parent_objective_id ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_parent_objective_level_depth_function();"
    )
    op.execute("DROP TRIGGER IF EXISTS check_objective_level_depth ON objectives;")
    op.execute("DROP FUNCTION IF EXISTS check_objective_level_depth_function;")
