<%
  trigger_prefix = context.get("trigger_prefix", "platforma_")
  func_schema = context.get("function_schema", "public")
  triggers = context.get("triggers")
%>

def _clear_all_functions(conn):
    """
    Clear all functions from ${function_schema} schema.

    Clear only functions beginning with `${trigger_prefix}`.
    """
    select_function_sql = """
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_type='FUNCTION'
        AND specific_schema='${function_schema}'
        AND routine_name like '${trigger_prefix}%';
        """
    func_res = conn.execute(sa.text(select_function_sql))
    func_rows = func_res.fetchall()
    if not func_rows:
        return

    drop_functions_sql_statements = [
        f"DROP FUNCTION IF EXISTS ${function_schema}.{func_name} CASCADE;"
        for [func_name] in func_rows
    ]
    drop_functions_sql = " ".join(drop_functions_sql_statements)
    op.execute(drop_functions_sql)

def _clear_all_triggers(conn):
    """
    Delete all triggers in the public schema starting with ${trigger_prefix}.
    """
    trigger_query_sql = """
        SELECT DISTINCT event_object_table, trigger_name
        FROM INFORMATION_SCHEMA.triggers
        WHERE trigger_name LIKE '${trigger_prefix}_%'
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

% for trigger_data in triggers:
<%
  trigger_basename = trigger_data["name"]
  func_name = f"{func_schema}.{trigger_prefix}{trigger_basename}_func"
  description = trigger_data.get("description", "Function for trigger")
%>
    op.execute(
    """
    CREATE OR REPLACE FUNCTION ${func_name}() RETURNS TRIGGER LANGUAGE PLPGSQL as $$
    /*
      ${description}
    */
    ${trigger_data["function_src"]} $$;
    """
    )
% for table in trigger_data["tables"]:
<%
  trigger_name = f"{trigger_prefix}{trigger_basename}_trigger"
%>
    # Drop and Recreate the trigger `${trigger_name}` on `${table}`
    op.execute(
    """
    CREATE TRIGGER ${trigger_name}
    ${trigger_data["condition"]} ON ${table}
    FOR EACH ROW
    EXECUTE PROCEDURE ${func_name}();
    ALTER TABLE ${table} ENABLE TRIGGER ${trigger_name};
    """
    )
% endfor
% endfor

def downgrade():
    # Not reversible migration.
    pass
