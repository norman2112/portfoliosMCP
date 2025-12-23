"""update_parent_objective_check_trigger

Revision ID: 20240417113648
Revises: 20231122173205
Create Date: 2024-04-17 11:36:49.436752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240417113648"
down_revision = "20231122173205"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_parent_objective_update_access_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_parent_objective_update_access_func CASCADE;"
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_parent_objective_update_access_func()
        RETURNS TRIGGER
        LANGUAGE PLPGSQL
        AS $$
        /*
          WHEN: a parent objective is to be updated on specific `work_item_container`
          ENSURE: the user's `work_item_container_role` for that `work_item_container` is not "none".
        */
        DECLARE
            access_denied boolean;
            parent_work_item_container_id int;
        BEGIN
            IF NEW.parent_objective_id IS NOT NULL THEN
                IF NEW.parent_objective_id = NEW.id THEN
                    RAISE EXCEPTION 'parent_objective_id cannot be current objective id: %', NEW.parent_objective_id;
                END IF;

                SELECT EXISTS INTO access_denied (
                    SELECT
                        o.work_item_container_id
                    FROM
                        objectives o
                        LEFT JOIN work_item_container_roles w ON o.work_item_container_id = w.work_item_container_id
                    WHERE
                        o.id = NEW.parent_objective_id
                        AND (w.app_created_by = NEW.app_last_updated_by OR w.created_by = NEW.last_updated_by)
                        AND w.okr_role = 'none'
                        AND (OLD.parent_objective_id IS NULL OR OLD.parent_objective_id <> NEW.parent_objective_id)
                );

                IF access_denied THEN
                    SELECT work_item_container_id INTO parent_work_item_container_id
                    FROM objectives
                    WHERE id = NEW.parent_objective_id;

                    RAISE EXCEPTION 'Cannot save parent_objective_id: %. No access to parent objective work_item_container: %', NEW.parent_objective_id, parent_work_item_container_id;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$;
        """
    )

    # Drop and Recreate the trigger `platforma_check_parent_objective_update_access_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_parent_objective_update_access_trigger
    BEFORE UPDATE ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_parent_objective_update_access_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_parent_objective_update_access_trigger;
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_parent_objective_update_access_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_parent_objective_update_access_func CASCADE;"
    )

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_parent_objective_update_access_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: a parent objective is to be updated on specific `work_item_container` ENSURE: the user's `work_item_container_role` for that `work_item_container` is not "none".

    */
    DECLARE access_denied boolean; parent_work_item_container_id int; BEGIN IF NEW.parent_objective_id IS NOT NULL THEN IF NEW.parent_objective_id = NEW.id THEN RAISE EXCEPTION 'parent_objective_id cannot be current objective id: %', NEW.parent_objective_id; END IF; SELECT
  EXISTS INTO access_denied (
    SELECT
      o.work_item_container_id
    FROM
      objectives o
      LEFT JOIN work_item_container_roles w ON o.work_item_container_id = w.work_item_container_id
    WHERE
      o.id = NEW.parent_objective_id
      AND (w.app_created_by = NEW.app_last_updated_by OR w.created_by = NEW.last_updated_by)
      AND w.okr_role = 'none'
  );
IF access_denied THEN SELECT
  work_item_container_id INTO parent_work_item_container_id
FROM
  objectives
WHERE
  id = NEW.parent_objective_id;
RAISE EXCEPTION 'Cannot save parent_objective_id: %. No access to parent objective work_item_container: %', NEW.parent_objective_id, parent_work_item_container_id; END IF; END IF; RETURN NEW; END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_parent_objective_update_access_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_parent_objective_update_access_trigger
    BEFORE UPDATE ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_parent_objective_update_access_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_parent_objective_update_access_trigger;
    """
    )
