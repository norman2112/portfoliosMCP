"""key_results dates trigger

Revision ID: 20210615113028
Revises: 20210614080351
Create Date: 2021-06-15 11:30:30.354212

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210615113028"
down_revision = "20210614080351"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION check_key_results_dates_function() "
        "RETURNS TRIGGER "
        "LANGUAGE PLPGSQL "
        "AS $$ "
        "DECLARE "
        "date_invalid boolean; "
        "BEGIN "
        "IF NEW.starts_at::timestamp > NEW.ends_at::timestamp THEN "
        "RAISE EXCEPTION "
        "'key_result starts_at must be before ends_at.'; "
        "END IF;"
        "SELECT EXISTS INTO date_invalid ( "
        "SELECT id "
        "FROM objectives o "
        "WHERE o.starts_at::timestamp > NEW.starts_at::timestamp "
        "AND o.id = NEW.objective_id "
        "); "
        "IF date_invalid THEN "
        "RAISE EXCEPTION "
        "'Key result cannot start before related objective.'; "
        "END IF; "
        "SELECT EXISTS INTO date_invalid ( "
        "SELECT id "
        "FROM objectives o "
        "WHERE o.ends_at::timestamp < NEW.ends_at::timestamp "
        "AND o.id = NEW.objective_id "
        "); "
        "IF date_invalid THEN "
        "RAISE EXCEPTION "
        "'Key result cannot end after related objective.'; "
        "END IF; "
        "RETURN NEW; "
        "END; "
        "$$;"
    )
    op.execute(
        "CREATE TRIGGER check_key_results_dates "
        "BEFORE INSERT OR UPDATE ON key_results "
        "FOR EACH ROW "
        "EXECUTE PROCEDURE check_key_results_dates_function();"
    )
    op.execute("ALTER TABLE key_results ENABLE TRIGGER check_key_results_dates;")


def downgrade():
    op.execute(
        "ALTER TABLE key_results DISABLE TRIGGER check_key_results_dates;"
        "DROP TRIGGER IF EXISTS check_key_results_dates ON key_results;"
        "DROP FUNCTION IF EXISTS check_key_results_dates_function;"
    )
