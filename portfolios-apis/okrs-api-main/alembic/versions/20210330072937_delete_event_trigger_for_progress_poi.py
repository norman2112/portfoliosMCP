"""delete_event_trigger_for_progress_poi

Revision ID: 20210330072937
Revises: 20210329081202
Create Date: 2021-03-30 07:29:41.603269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210330072937"
down_revision = "20210329081202"
branch_labels = None
depends_on = None


TRIGGERS = [
    "progress_points",
    "key_results",
    "work_items",
    "work_item_containers",
    "settings",
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
