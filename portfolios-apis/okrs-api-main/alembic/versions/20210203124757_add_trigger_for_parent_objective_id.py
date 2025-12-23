"""Add trigger for parent_objective_id

Revision ID: 20210203124757
Revises: 20210202105126
Create Date: 2021-02-03 12:47:58.902946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210203124757"
down_revision = "20210202105126"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_parent_objective_level_depth_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "level_okay boolean; "
        "level_depth_id int; "
        "BEGIN "
        "IF NEW.parent_objective_id IS NOT NULL THEN "
        "SELECT EXISTS INTO level_okay ( "
        "SELECT 1 "
        "FROM objectives "
        "WHERE id = NEW.parent_objective_id "
        "AND level_depth < NEW.level_depth "
        "); "
        "IF NOT level_okay THEN "
        "SELECT level_depth INTO level_depth_id "
        "FROM objectives "
        "WHERE id = NEW.parent_objective_id; "
        "RAISE EXCEPTION "
        "'Parent objective (id: %, level_depth: %) must have lower level depth "
        "than child objective (id: %, level_depth: %)', "
        "NEW.parent_objective_id, level_depth_id, NEW.id, NEW.level_depth; "
        "END IF; "
        "END IF; "
        "RETURN NEW;"
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_parent_objective_level_depth "
        "BEFORE INSERT OR UPDATE OF parent_objective_id ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_parent_objective_level_depth_function();"
    )
    op.execute(
        "ALTER TABLE objectives ENABLE TRIGGER check_parent_objective_level_depth;"
    )


def downgrade():
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_parent_objective_level_depth;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS check_parent_objective_level_depth ON objectives;"
    )
    op.execute("DROP FUNCTION IF EXISTS check_parent_objective_level_depth_function;")
