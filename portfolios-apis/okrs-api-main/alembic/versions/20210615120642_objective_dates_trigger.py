"""objective dates trigger

Revision ID: 20210615120642
Revises: 20210615113028
Create Date: 2021-06-15 12:06:44.320510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210615120642"
down_revision = "20210615113028"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_objectives_dates_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "date_invalid boolean; "
        "BEGIN "
        "IF NEW.starts_at::timestamp > NEW.ends_at::timestamp THEN "
        "RAISE EXCEPTION "
        "'objective starts_at must be before ends_at.'; "
        "END IF;"
        "SELECT EXISTS INTO date_invalid ( "
        "SELECT id "
        "FROM key_results kr "
        "WHERE kr.starts_at::timestamp < NEW.starts_at::timestamp "
        "AND NEW.id = kr.objective_id "
        "); "
        "IF date_invalid THEN "
        "RAISE EXCEPTION "
        "'Objective cannot start after any related key_results.'; "
        "END IF; "
        "SELECT EXISTS INTO date_invalid ( "
        "SELECT id "
        "FROM key_results kr "
        "WHERE kr.ends_at::timestamp > NEW.ends_at::timestamp "
        "AND NEW.id = kr.objective_id "
        "); "
        "IF date_invalid THEN "
        "RAISE EXCEPTION "
        "'Objective cannot end before any related key_results.'; "
        "END IF; "
        "RETURN NEW; "
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_objectives_dates "
        "BEFORE INSERT OR UPDATE ON objectives "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_objectives_dates_function();"
    )
    op.execute("ALTER TABLE objectives ENABLE TRIGGER check_objectives_dates;")


def downgrade():
    op.execute(
        "ALTER TABLE objectives DISABLE TRIGGER check_objectives_dates;"
        "DROP TRIGGER IF EXISTS check_objectives_dates ON objectives;"
        "DROP FUNCTION IF EXISTS check_objectives_dates_function;"
    )
