"""delete_event_trigger_for_settings-lev

Revision ID: 20210330155813
Revises: 20210330151624
Create Date: 2021-03-30 15:58:14.614912

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210330155813"
down_revision = "20210330151624"
branch_labels = None
depends_on = None


TRIGGERS = [
    "settings-level_config",
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
