"""drop_objectives_dates_trigger

Revision ID: 20241004134758
Revises: 20240930073728
Create Date: 2024-10-04 13:47:59.663547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241004134758"
down_revision = "20240930073728"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_objectives_dates_trigger ON objectives;"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_objectives_dates_func CASCADE;"
    )


def downgrade():
    op.execute(
        """
  CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_objectives_dates_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    DECLARE date_invalid boolean; BEGIN IF NEW.starts_at :: timestamp > NEW.ends_at :: timestamp THEN RAISE EXCEPTION 'objective starts_at must be before ends_at.'; END IF; SELECT
  EXISTS INTO date_invalid (
    SELECT
      id
    FROM
      key_results kr
    WHERE
      kr.starts_at :: timestamp < NEW.starts_at :: timestamp
      AND NEW.id = kr.objective_id and kr.deleted_at_epoch = 0
  );
IF date_invalid THEN RAISE EXCEPTION 'Objective cannot start after any related key_results.'; END IF; SELECT
  EXISTS INTO date_invalid (
    SELECT
      id
    FROM
      key_results kr
    WHERE
      kr.ends_at :: timestamp > NEW.ends_at :: timestamp
      AND NEW.id = kr.objective_id and kr.deleted_at_epoch = 0
  );
IF date_invalid THEN RAISE EXCEPTION 'Objective cannot end before any related key_results.'; END IF; RETURN NEW; END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_key_results_dates_trigger` on `key_results`
    op.execute(
        """
        CREATE TRIGGER platforma_check_objectives_dates_trigger
        BEFORE INSERT OR UPDATE ON objectives
        FOR EACH ROW
        EXECUTE PROCEDURE platforma_functions.platforma_check_objectives_dates_func();
        ALTER TABLE objectives ENABLE TRIGGER platforma_check_objectives_dates_trigger;
        """
    )
