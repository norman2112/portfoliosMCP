"""Remove all non hasura functions and triggers

Revision ID: 20210830095204
Revises: 20210830094752
Create Date: 2021-08-30 09:52:06.910007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210830095204"
down_revision = "20210830094752"
branch_labels = None
depends_on = None

CURRENT_USER_DEFINED_FUNCTIONS = [
    "check_child_objectives_level_depth_function",
    "check_key_results_dates_function",
    "check_objective_level_depth_insert_function",
    "check_objective_level_depth_update_function",
    "check_objectives_dates_function",
    "check_parent_objective_insert_access_function",
    "check_parent_objective_level_depth_function",
    "check_parent_objective_update_access_function",
    "check_wic_level_depth_default_function",
    "set_wic_objective_editing_levels_and_level_depth_default_function",
    "trigger_set_timestamp",
]


def _clear_all_functions():
    """
    Clear all user-defined functions from the public schema.

    Clear only functions that do not start with `hasura_notify_`.
    The CASCADE option will automatically remove the related triggers as well.
    """
    drop_functions_sql_statements = [
        f"DROP FUNCTION IF EXISTS public.{func_name} CASCADE;"
        for func_name in CURRENT_USER_DEFINED_FUNCTIONS
    ]
    drop_functions_sql = " ".join(drop_functions_sql_statements)
    op.execute(drop_functions_sql)


def upgrade():
    _clear_all_functions()


def downgrade():
    # Irreversible Migration. Use `inv migration.apply-triggers` task to
    # create a migration that will re-create all triggers and functions.
    pass
