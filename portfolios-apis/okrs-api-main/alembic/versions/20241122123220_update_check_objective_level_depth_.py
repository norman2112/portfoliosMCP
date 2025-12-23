"""update_check_objective_level_depth_update

Revision ID: 20241122123220
Revises: 20241024093534
Create Date: 2024-11-22 12:32:25.456101

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241122123220"
down_revision = "20241024093534"
branch_labels = None
depends_on = None


def upgrade():
    # Drop and Recreate the trigger `platforma_check_objective_level_depth_update_trigger` on `objectives`
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_objective_level_depth_update_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_objective_level_depth_update_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_objective_level_depth_update_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: an objective is updated ENSURE: that the `level_depth` specified is within the range of levels in `settings.level_config`
To re-iterate, on UPDATE ONLY, we are checking the settings to see if the objectives.level is within the settings levels.

    */
    DECLARE level_okay boolean; BEGIN IF NEW.deleted_at_epoch = 0 OR OLD.level_depth <> NEW.level_depth THEN SELECT
  EXISTS INTO level_okay (
    SELECT
      lc.depth
    FROM
      (
        SELECT
          CAST(obj.val ->> 'depth' AS INTEGER) AS depth
        FROM
          settings
          JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val ->> 'depth' AS INTEGER) > -1
        WHERE
          (tenant_id_str = NEW.tenant_id_str OR tenant_group_id_str = NEW.tenant_group_id_str)
      ) lc
    WHERE
      lc.depth = NEW.level_depth
  );
IF NOT level_okay THEN RAISE EXCEPTION 'objective (id: %, level_depth: %) level_depth is invalid', NEW.id, NEW.level_depth; END IF; END IF; RETURN NEW; END;
 $$;
    """
    )
    op.execute(
        """
    CREATE TRIGGER platforma_check_objective_level_depth_update_trigger
    BEFORE UPDATE ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_objective_level_depth_update_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_objective_level_depth_update_trigger;
    """
    )

    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_level_depth_for_child_objective_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_level_depth_for_child_objective_func CASCADE;"
    )

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_level_depth_for_child_objective_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Check objective level_depth vs levels in settings level_config.
This function is only concerned with objectives that have parent objectives.
The following conditions must be met in order to avoid raising an exception.
- The level depth of the child must be greater than the level depth of the parent. - The parent_id of the objective must be different than the id of the objective.

    */
    DECLARE level_not_okay boolean; level_depth_id int; BEGIN
  IF NEW.parent_objective_id IS NOT NULL AND (NEW.deleted_at_epoch = 0 OR OLD.parent_objective_id IS NULL OR OLD.parent_objective_id <> NEW.parent_objective_id) THEN
    SELECT EXISTS INTO level_not_okay (
      SELECT 1 FROM objectives
        WHERE id = NEW.parent_objective_id
          AND (level_depth >= NEW.level_depth OR id = NEW.id)
    );
    IF level_not_okay THEN
      SELECT level_depth INTO level_depth_id
        FROM objectives
        WHERE id = NEW.parent_objective_id;
      RAISE EXCEPTION
        'Parent objective (id: %, level_depth: %) must have lower
         level depth than child objective (id: %, level_depth: %)',
        NEW.parent_objective_id, level_depth_id, NEW.id, NEW.level_depth;
    END IF;
  END IF;
  RETURN NEW;
END;
 $$;
    """
    )

    op.execute(
        """
    CREATE TRIGGER platforma_check_level_depth_for_child_objective_trigger
    BEFORE INSERT OR UPDATE OF level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_level_depth_for_child_objective_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_level_depth_for_child_objective_trigger;
    """
    )

    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_parent_objective_level_depth_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_parent_objective_level_depth_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_parent_objective_level_depth_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: objectives have a `parent_objective_id` ENSURE: the parent objective's `level_depth` is a lower value than the child objective's `level_depth`.

    */
    DECLARE level_okay boolean; level_depth_id int; BEGIN
  IF NEW.parent_objective_id IS NOT NULL AND (NEW.deleted_at_epoch = 0 OR OLD.parent_objective_id IS NULL OR OLD.parent_objective_id <> NEW.parent_objective_id) THEN
    SELECT EXISTS INTO level_okay (
      SELECT 1 FROM objectives
        WHERE id = NEW.parent_objective_id AND level_depth < NEW.level_depth
    );
    IF NOT level_okay THEN
      SELECT level_depth INTO level_depth_id FROM objectives
        WHERE id = NEW.parent_objective_id;
    RAISE EXCEPTION
      'Parent objective (id: %, level_depth: %) must have lower level depth than child objective (id: %, level_depth: %)',
      NEW.parent_objective_id, level_depth_id, NEW.id, NEW.level_depth;
    END IF;
  END IF;
  RETURN NEW;
END;
 $$;
    """
    )

    op.execute(
        """
    CREATE TRIGGER platforma_check_parent_objective_level_depth_trigger
    BEFORE INSERT OR UPDATE OF parent_objective_id, level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_parent_objective_level_depth_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_parent_objective_level_depth_trigger;
    """
    )


def downgrade():
    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_objective_level_depth_update_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_objective_level_depth_update_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_objective_level_depth_update_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: an objective is updated ENSURE: that the `level_depth` specified is within the range of levels in `settings.level_config`
To re-iterate, on UPDATE ONLY, we are checking the settings to see if the objectives.level is within the settings levels.

    */
    DECLARE level_okay boolean; BEGIN SELECT
  EXISTS INTO level_okay (
    SELECT
      lc.depth
    FROM
      (
        SELECT
          CAST(obj.val ->> 'depth' AS INTEGER) AS depth
        FROM
          settings
          JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val ->> 'depth' AS INTEGER) > -1
        WHERE
          (tenant_id_str = NEW.tenant_id_str OR tenant_group_id_str = NEW.tenant_group_id_str)
      ) lc
    WHERE
      lc.depth = NEW.level_depth
  );
IF NOT level_okay THEN RAISE EXCEPTION 'objective (id: %, level_depth: %) level_depth is invalid', NEW.id, NEW.level_depth; END IF; RETURN NEW; END;
 $$;
    """
    )
    # Drop and Recreate the trigger `platforma_check_objective_level_depth_update_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_objective_level_depth_update_trigger
    BEFORE UPDATE ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_objective_level_depth_update_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_objective_level_depth_update_trigger;
    """
    )

    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_level_depth_for_child_objective_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_level_depth_for_child_objective_func CASCADE;"
    )

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_level_depth_for_child_objective_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Check objective level_depth vs levels in settings level_config.
This function is only concerned with objectives that have parent objectives.
The following conditions must be met in order to avoid raising an exception.
- The level depth of the child must be greater than the level depth of the parent. - The parent_id of the objective must be different than the id of the objective.

    */
    DECLARE level_not_okay boolean; level_depth_id int; BEGIN
  IF NEW.parent_objective_id IS NOT NULL THEN
    SELECT EXISTS INTO level_not_okay (
      SELECT 1 FROM objectives
        WHERE id = NEW.parent_objective_id
          AND (level_depth >= NEW.level_depth OR id = NEW.id)
    );
    IF level_not_okay THEN
      SELECT level_depth INTO level_depth_id
        FROM objectives
        WHERE id = NEW.parent_objective_id;
      RAISE EXCEPTION
        'Parent objective (id: %, level_depth: %) must have lower
         level depth than child objective (id: %, level_depth: %)',
        NEW.parent_objective_id, level_depth_id, NEW.id, NEW.level_depth;
    END IF;
  END IF;
  RETURN NEW;
END;
 $$;
    """
    )

    op.execute(
        """
    CREATE TRIGGER platforma_check_level_depth_for_child_objective_trigger
    BEFORE INSERT OR UPDATE OF level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_level_depth_for_child_objective_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_level_depth_for_child_objective_trigger;
    """
    )

    op.execute(
        "DROP TRIGGER IF EXISTS platforma_check_parent_objective_level_depth_trigger ON objectives"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS platforma_functions.platforma_check_parent_objective_level_depth_func CASCADE;"
    )
    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_parent_objective_level_depth_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: objectives have a `parent_objective_id` ENSURE: the parent objective's `level_depth` is a lower value than the child objective's `level_depth`.

    */
    DECLARE level_okay boolean; level_depth_id int; BEGIN
  IF NEW.parent_objective_id IS NOT NULL THEN
    SELECT EXISTS INTO level_okay (
      SELECT 1 FROM objectives
        WHERE id = NEW.parent_objective_id AND level_depth < NEW.level_depth
    );
    IF NOT level_okay THEN
      SELECT level_depth INTO level_depth_id FROM objectives
        WHERE id = NEW.parent_objective_id;
    RAISE EXCEPTION
      'Parent objective (id: %, level_depth: %) must have lower level depth than child objective (id: %, level_depth: %)',
      NEW.parent_objective_id, level_depth_id, NEW.id, NEW.level_depth;
    END IF;
  END IF;
  RETURN NEW;
END;
 $$;
    """
    )

    op.execute(
        """
    CREATE TRIGGER platforma_check_parent_objective_level_depth_trigger
    BEFORE INSERT OR UPDATE OF parent_objective_id, level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_parent_objective_level_depth_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_parent_objective_level_depth_trigger;
    """
    )
