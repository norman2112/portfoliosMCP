"""update_platforma_check_key_results_dates

Revision ID: 20240802104628
Revises: 20240629093204
Create Date: 2024-08-02 10:46:29.697510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240802104628"
down_revision = "20240629093204"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_key_results_dates_trigger ON key_results"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_key_results_dates_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_key_results_dates_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Make sure of the following regarding key_result starts_at and ends_at: - starts_at must be before ends_at - starts_at must not be before objective starts_at - ends_at must not be after objective ends_at

    */
    DECLARE date_invalid boolean; BEGIN IF NEW.starts_at :: timestamp > NEW.ends_at :: timestamp THEN RAISE EXCEPTION 'key_result starts_at must be before ends_at.'; END IF; SELECT
  EXISTS INTO date_invalid (
    SELECT
      id
    FROM
      objectives o
    WHERE
      o.starts_at :: timestamp > NEW.starts_at :: timestamp
      AND o.id = NEW.objective_id AND NEW.deleted_at_epoch = 0
  );
IF date_invalid THEN RAISE EXCEPTION 'Key result cannot start before related objective.'; END IF; SELECT
  EXISTS INTO date_invalid (
    SELECT
      id
    FROM
      objectives o
    WHERE
      o.ends_at :: timestamp < NEW.ends_at :: timestamp
      AND o.id = NEW.objective_id AND NEW.deleted_at_epoch = 0
  );
IF date_invalid THEN RAISE EXCEPTION 'Key result cannot end after related objective.'; END IF; RETURN NEW; END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_key_results_dates_trigger` on `key_results`
    op.execute(
        """
    CREATE TRIGGER platforma_check_key_results_dates_trigger
    BEFORE INSERT OR UPDATE ON key_results
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_key_results_dates_func();
    ALTER TABLE key_results ENABLE TRIGGER platforma_check_key_results_dates_trigger;
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_key_results_dates_trigger ON key_results"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_key_results_dates_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_key_results_dates_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Make sure of the following regarding key_result starts_at and ends_at: - starts_at must be before ends_at - starts_at must not be before objective starts_at - ends_at must not be after objective ends_at

    */
    DECLARE date_invalid boolean; BEGIN IF NEW.starts_at :: timestamp > NEW.ends_at :: timestamp THEN RAISE EXCEPTION 'key_result starts_at must be before ends_at.'; END IF; SELECT
  EXISTS INTO date_invalid (
    SELECT
      id
    FROM
      objectives o
    WHERE
      o.starts_at :: timestamp > NEW.starts_at :: timestamp
      AND o.id = NEW.objective_id
  );
IF date_invalid THEN RAISE EXCEPTION 'Key result cannot start before related objective.'; END IF; SELECT
  EXISTS INTO date_invalid (
    SELECT
      id
    FROM
      objectives o
    WHERE
      o.ends_at :: timestamp < NEW.ends_at :: timestamp
      AND o.id = NEW.objective_id
  );
IF date_invalid THEN RAISE EXCEPTION 'Key result cannot end after related objective.'; END IF; RETURN NEW; END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_key_results_dates_trigger` on `key_results`
    op.execute(
        """
    CREATE TRIGGER platforma_check_key_results_dates_trigger
    BEFORE INSERT OR UPDATE ON key_results
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_key_results_dates_func();
    ALTER TABLE key_results ENABLE TRIGGER platforma_check_key_results_dates_trigger;
    """
    )
