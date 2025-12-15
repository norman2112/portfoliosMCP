"""triggers

Revision ID: 20230601132218
Revises: 20230220163157
Create Date: 2023-06-01 13:22:19.967549

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20230601132218"
down_revision = "20230220163157"
branch_labels = None
depends_on = None


def _clear_all_functions(conn):
    """
    Clear all functions from platforma_functions schema.

    Clear only functions beginning with `platforma_`.
    """
    select_function_sql = """
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_type='FUNCTION'
        AND specific_schema='platforma_functions'
        AND routine_name like 'platforma_%';
        """
    func_res = conn.execute(sa.text(select_function_sql))
    func_rows = func_res.fetchall()
    if not func_rows:
        return

    drop_functions_sql_statements = [
        f"DROP FUNCTION IF EXISTS platforma_functions.{func_name} CASCADE;"
        for [func_name] in func_rows
    ]
    drop_functions_sql = " ".join(drop_functions_sql_statements)
    op.execute(drop_functions_sql)


def _clear_all_triggers(conn):
    """
    Delete all triggers in the public schema starting with platforma_.
    """
    trigger_query_sql = """
        SELECT DISTINCT event_object_table, trigger_name
        FROM INFORMATION_SCHEMA.triggers
        WHERE trigger_name LIKE 'platforma__%'
        """
    res = conn.execute(sa.text(trigger_query_sql))
    result_rows = res.fetchall()
    if not result_rows:
        return

    drop_trigger_statements = [
        f"DROP TRIGGER IF EXISTS {trigger_name} ON {table};"
        for [table, trigger_name] in result_rows
    ]
    drop_trigger_sql = "\n".join(drop_trigger_statements)
    op.execute(drop_trigger_sql)


def upgrade():
    # Idempotent migration to reapply triggers.
    conn = op.get_bind()
    _clear_all_functions(conn)
    _clear_all_triggers(conn)

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_set_timestamp_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Set created_at and updated_at timestamp triggers for these fields

    */
    BEGIN NEW.updated_at = NOW();RETURN NEW;END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `activity_logs`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON activity_logs
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE activity_logs ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `key_results`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON key_results
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE key_results ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `progress_points`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON progress_points
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE progress_points ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `settings`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON settings
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE settings ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `work_items`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON work_items
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE work_items ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    # Drop and Recreate the trigger `platforma_set_timestamp_trigger` on `work_item_containers`
    op.execute(
        """
    CREATE TRIGGER platforma_set_timestamp_trigger
    BEFORE INSERT OR UPDATE ON work_item_containers
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_timestamp_func();
    ALTER TABLE work_item_containers ENABLE TRIGGER platforma_set_timestamp_trigger;
    """
    )

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_wic_level_depth_default_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Check the work_item_container level_depth_default field to make sure the value is within levels from the settings

    */
    DECLARE level_okay boolean; BEGIN IF NEW.level_depth_default IS NOT NULL THEN SELECT
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
          tenant_id_str = NEW.tenant_id_str OR tenant_group_id_str = NEW.tenant_group_id_str
      ) lc
    WHERE
      lc.depth = NEW.level_depth_default
  );
IF NOT level_okay THEN RAISE EXCEPTION 'work_item_container (id: %, level_depth_default: %) level_depth_default is invalid', NEW.id, NEW.level_depth_default; END IF; END IF; RETURN NEW; END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_wic_level_depth_default_trigger` on `work_item_containers`
    op.execute(
        """
    CREATE TRIGGER platforma_check_wic_level_depth_default_trigger
    BEFORE INSERT OR UPDATE OF level_depth_default ON work_item_containers
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_wic_level_depth_default_func();
    ALTER TABLE work_item_containers ENABLE TRIGGER platforma_check_wic_level_depth_default_trigger;
    """
    )

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_set_wic_objective_editing_levels_and_level_depth_default_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Automatically set the objective_editing_levels and level_depth_default when created

    */
    DECLARE
    default_level_depth TEXT;
BEGIN
    IF NEW.objective_editing_levels IS NOT NULL OR NEW.level_depth_default IS NOT NULL THEN
    RAISE EXCEPTION
        'work_item_containers objective_editing_levels and level_depth_default must both be null on insert.';
    END IF;
    SELECT CAST(obj.val->>'depth' AS TEXT) INTO default_level_depth
        FROM settings
        JOIN LATERAL json_array_elements(level_config) obj(val) ON CAST(obj.val->>'depth' AS INTEGER) > -1
        WHERE (tenant_id_str = NEW.tenant_id_str OR tenant_group_id_str = NEW.tenant_group_id_str)
        AND CAST(obj.val->>'is_default' AS BOOLEAN) IS TRUE;
    NEW.level_depth_default = default_level_depth::int;
    NEW.objective_editing_levels = CONCAT('[', default_level_depth, ']');
    RETURN NEW;
END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_set_wic_objective_editing_levels_and_level_depth_default_trigger` on `work_item_containers`
    op.execute(
        """
    CREATE TRIGGER platforma_set_wic_objective_editing_levels_and_level_depth_default_trigger
    BEFORE INSERT ON work_item_containers
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_set_wic_objective_editing_levels_and_level_depth_default_func();
    ALTER TABLE work_item_containers ENABLE TRIGGER platforma_set_wic_objective_editing_levels_and_level_depth_default_trigger;
    """
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

    # Drop and Recreate the trigger `platforma_check_parent_objective_level_depth_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_parent_objective_level_depth_trigger
    BEFORE INSERT OR UPDATE OF parent_objective_id, level_depth ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_parent_objective_level_depth_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_parent_objective_level_depth_trigger;
    """
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

    # Drop and Recreate the trigger `platforma_check_level_depth_for_child_objective_trigger` on `objectives`
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
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_parent_objective_insert_access_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: a parent objective is to be added to a `work_item_container` ENSURE: the `work_item_container_role` for this user on this `work_item_contianer` is not "none"

    */
    DECLARE access_denied boolean; parent_work_item_container_id int; BEGIN IF NEW.parent_objective_id IS NOT NULL THEN SELECT
  EXISTS INTO access_denied (
    SELECT
      o.work_item_container_id
    FROM
      objectives o
      LEFT JOIN work_item_container_roles w ON o.work_item_container_id = w.work_item_container_id
    WHERE
      o.id = NEW.parent_objective_id
      AND (w.app_created_by = NEW.app_created_by OR w.created_by = NEW.created_by)
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

    # Drop and Recreate the trigger `platforma_check_parent_objective_insert_access_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_parent_objective_insert_access_trigger
    BEFORE INSERT ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_parent_objective_insert_access_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_parent_objective_insert_access_trigger;
    """
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

    op.execute(
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_objective_level_depth_insert_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      WHEN: an objective is being inserted ENSURE: the objective's `level_depth` is in the associated `work_item_containers` `objective_editing_levels`

    */
    DECLARE level_okay boolean; BEGIN SELECT
  EXISTS INTO level_okay (
    SELECT
      lc.level
    FROM
      (
        SELECT
          UNNEST(
            CONCAT('{', d.list, '}'):: int[]
          ) AS level
        FROM
          work_item_containers w,
          LATERAL (
            SELECT
              string_agg(value :: text, ', ') AS list
            FROM
              json_array_elements_text(w.objective_editing_levels)
          ) d
        WHERE
          id = NEW.work_item_container_id
      ) lc
    WHERE
      lc.level = NEW.level_depth
  );
IF NOT level_okay THEN RAISE EXCEPTION 'objective (id: %, level_depth: %) level_depth is invalid', NEW.id, NEW.level_depth; END IF; RETURN NEW; END;
 $$;
    """
    )

    # Drop and Recreate the trigger `platforma_check_objective_level_depth_insert_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_objective_level_depth_insert_trigger
    BEFORE INSERT ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_objective_level_depth_insert_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_objective_level_depth_insert_trigger;
    """
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
        """
    CREATE OR REPLACE FUNCTION platforma_functions.platforma_check_objectives_dates_func() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      Make sure of the following regarding key_result starts_at and ends_at: - starts_at must be before ends_at - starts_at must not be before objective starts_at - ends_at must not be after objective ends_at

    */
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

    # Drop and Recreate the trigger `platforma_check_objectives_dates_trigger` on `objectives`
    op.execute(
        """
    CREATE TRIGGER platforma_check_objectives_dates_trigger
    BEFORE INSERT OR UPDATE ON objectives
    FOR EACH ROW
    EXECUTE PROCEDURE platforma_functions.platforma_check_objectives_dates_func();
    ALTER TABLE objectives ENABLE TRIGGER platforma_check_objectives_dates_trigger;
    """
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


def downgrade():
    # Not reversible migration.
    pass
