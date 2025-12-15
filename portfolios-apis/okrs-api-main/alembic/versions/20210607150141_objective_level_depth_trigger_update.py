"""objective level_depth trigger update

Revision ID: 20210607150141
Revises: 20210607122625
Create Date: 2021-06-07 15:01:43.185562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210607150141"
down_revision = "20210607122625"
branch_labels = None
depends_on = None


def upgrade():
    # drop old trigger from here:
    # 20210317142948_add_trigger_for_objective_level_depth.py
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_parent_objective_level_depth;"
    )
    op.execute("DROP TRIGGER IF EXISTS check_objective_level_depth ON objectives;")
    op.execute("DROP FUNCTION IF EXISTS check_objective_level_depth_function;")

    # create new trigger functions and add triggers:

    # this function checks that the objective level_depth is within the
    # objective_editing_levels upon creation
    op.execute(
        "CREATE OR REPLACE FUNCTION check_objective_level_depth_insert_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "level_okay boolean; "
        "BEGIN "
        "SELECT EXISTS INTO level_okay ( "
        "SELECT lc.level "
        "FROM ( "
        "SELECT UNNEST(CONCAT('{',d.list,'}')::int[]) AS level "
        "FROM work_item_containers w, LATERAL ( "
        "SELECT string_agg(value::text, ', ') AS list "
        "FROM json_array_elements_text(w.objective_editing_levels) "
        ") d "
        "WHERE id = NEW.work_item_container_id "
        ") lc "
        "WHERE lc.level = NEW.level_depth "
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
        "CREATE TRIGGER check_objective_level_depth_insert "
        "BEFORE INSERT ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_objective_level_depth_insert_function();"
    )
    op.execute(
        "ALTER TABLE objectives ENABLE TRIGGER check_objective_level_depth_insert;"
    )

    # this function checks that the objective level_depth is within the
    # settings levels upon update
    op.execute(
        "CREATE OR REPLACE FUNCTION check_objective_level_depth_update_function() "
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
        "CREATE TRIGGER check_objective_level_depth_update "
        "BEFORE INSERT ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_objective_level_depth_update_function();"
    )
    op.execute(
        "ALTER TABLE objectives ENABLE TRIGGER check_objective_level_depth_update;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_objective_level_depth_insert;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_objective_level_depth_insert on objectives;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_objective_level_depth_insert_function;")

    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_objective_level_depth_update;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_objective_level_depth_update on objectives;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_objective_level_depth_update_function;")

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
    op.execute("ALTER TABLE objectives ENABLE TRIGGER check_objective_level_depth;")
