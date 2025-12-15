"""Add check_child_objectives_level_depth trigger

Revision ID: 20210328121220
Revises: 20210322174639
Create Date: 2021-03-28 12:12:22.016145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210328121220"
down_revision = "20210322174639"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_child_objectives_level_depth_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "levels_violation boolean; "
        "BEGIN "
        "SELECT EXISTS INTO levels_violation ( "
        "SELECT 1 "
        "FROM objectives "
        "WHERE parent_objective_id = NEW.id "
        "AND level_depth <= NEW.level_depth "
        "); "
        "IF levels_violation THEN "
        "RAISE EXCEPTION "
        "'Changing Objective (id: %, level_depth: %) to (level_depth: %) is not allowed as at least one "
        "child objective would have an equal or lower level_depth', "
        "NEW.id, OLD.level_depth, NEW.level_depth; "
        "END IF; "
        "RETURN NEW;"
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_child_objectives_level_depth "
        "BEFORE UPDATE OF level_depth ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_child_objectives_level_depth_function();"
    )
    op.execute(
        "ALTER TABLE objectives ENABLE TRIGGER check_child_objectives_level_depth;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_child_objectives_level_depth;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_child_objectives_level_depth ON objectives;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_child_objectives_level_depth_function;")
