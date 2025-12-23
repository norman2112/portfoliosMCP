"""delete_event_trigger_for_work_item_co

Revision ID: 20210407092008
Revises: 20210331193705
Create Date: 2021-04-07 09:20:10.354535

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210407092008"
down_revision = "20210331193705"
branch_labels = None
depends_on = None


TRIGGERS = [
    "work_item_containers-level_config",
    "objectives-activity_log",
    "key_result_work_item_mappings-activity_log",
    "settings-level_config",
    "key_results-progress_percentage",
    "work_items-ih_subscription",
    "progress_points-activity_log",
    "progress_points-progress_percentage",
    "key_results-activity_log",
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
