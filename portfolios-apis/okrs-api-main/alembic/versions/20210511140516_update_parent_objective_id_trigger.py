"""Update parent_objective_id trigger

Revision ID: 20210511140516
Revises: 20210511085700
Create Date: 2021-05-11 14:05:22.787424

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210511140516"
down_revision = "20210511085700"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_parent_objective_level_depth_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "level_not_okay boolean; "
        "level_depth_id int; "
        "BEGIN "
        "IF NEW.parent_objective_id IS NOT NULL THEN "
        "SELECT EXISTS INTO level_not_okay ( "
        "SELECT 1 "
        "FROM objectives "
        "WHERE id = NEW.parent_objective_id "
        "AND (level_depth >= NEW.level_depth OR id = NEW.id)"
        "); "
        "IF level_not_okay THEN "
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


def downgrade():
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
