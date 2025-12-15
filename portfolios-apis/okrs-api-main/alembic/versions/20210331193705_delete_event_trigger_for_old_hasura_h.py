"""delete_event_trigger_for_old_hasura_h

Revision ID: 20210331193705
Revises: 20210330155813
Create Date: 2021-03-31 19:37:08.292567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210331193705"
down_revision = "20210330155813"
branch_labels = None
depends_on = None


TRIGGERS = [
    "key_result_work_item_mappings-activity_log",
    "key_results-activity_log",
    "key_results-progress_percentage",
    "objectives-activity_log",
    "progress_points-activity_log",
    "progress_points-progress_percentage",
    "settings-global_tenant",
    "work_item_containers-level_config",
    "work_items-ih_subscription",
]


def drop_trigger_sql(trigger_name):
    return (
        "DO $$ "
        "BEGIN "
        "IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = 'hdb_catalog' AND table_name = 'event_invocation_logs') "
        "THEN "
        "DELETE FROM hdb_catalog.event_invocation_logs "
        "WHERE event_id IN ( "
        "SELECT id FROM hdb_catalog.event_log "
        f"WHERE trigger_name = '{trigger_name}' ); "
        "DELETE FROM hdb_catalog.event_log "
        f"WHERE trigger_name = '{trigger_name}';"
        "END IF; "
        "END "
        "$$"
    )


# Begin Alembic Migrations


def upgrade():
    for trigger_name in TRIGGERS:
        op.execute(drop_trigger_sql(trigger_name))


def downgrade():
    print("!! NO-OP IRREVERSIBLE MIGRATION !!")
