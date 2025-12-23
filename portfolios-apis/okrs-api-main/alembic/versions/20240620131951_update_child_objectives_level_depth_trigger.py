"""triggers

Revision ID: 20240620131951
Revises: 20240404153418
Create Date: 2024-06-20 13:19:56.512263

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20240620131951"
down_revision = "20240404153418"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_child_objectives_level_depth_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_child_objectives_level_depth_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_child_objectives_level_depth_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: a [child] objective has a parent_objective_id ENSURE: the [child] objective's `level_depth` has a greater value than the parent objective's `level_depth`.

    */
    DECLARE levels_violation boolean; BEGIN
  SELECT EXISTS INTO levels_violation (
    SELECT 1 FROM objectives
      WHERE parent_objective_id = NEW.id AND level_depth <= NEW.level_depth AND deleted_at_epoch = 0
  );
  IF levels_violation
    THEN RAISE EXCEPTION
      'Changing Objective (id: %, level_depth: %) to (level_depth: %) is not allowed as at
       least one child objective would have an equal or lower level_depth',
      NEW.id, OLD.level_depth, NEW.level_depth;
  END IF;
  RETURN NEW;
END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_child_objectives_level_depth_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_child_objectives_level_depth_trigger
    BEFORE UPDATE OF level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_child_objectives_level_depth_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_child_objectives_level_depth_trigger;
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_child_objectives_level_depth_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_child_objectives_level_depth_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_child_objectives_level_depth_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: a [child] objective has a parent_objective_id ENSURE: the [child] objective's `level_depth` has a greater value than the parent objective's `level_depth`.

    */
    DECLARE levels_violation boolean; BEGIN
  SELECT EXISTS INTO levels_violation (
    SELECT 1 FROM objectives
      WHERE parent_objective_id = NEW.id AND level_depth <= NEW.level_depth
  );
  IF levels_violation
    THEN RAISE EXCEPTION
      'Changing Objective (id: %, level_depth: %) to (level_depth: %) is not allowed as at
       least one child objective would have an equal or lower level_depth',
      NEW.id, OLD.level_depth, NEW.level_depth;
  END IF;
  RETURN NEW;
END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_child_objectives_level_depth_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_child_objectives_level_depth_trigger
    BEFORE UPDATE OF level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_child_objectives_level_depth_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_child_objectives_level_depth_trigger;
    """
    )
