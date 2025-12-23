"""disabled wrong trigger

Revision ID: 20210614080351
Revises: 20210607150141
Create Date: 2021-06-14 08:03:54.084489

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210614080351"
down_revision = "20210607150141"
branch_labels = None
depends_on = None


def upgrade():
    # mistake was made in this file: 20210607150141_objective_level_depth_trigger_update.py
    # I meant to disable the trigger for `check_objective_level_depth`,
    # not `check_parent_objective_level_depth`.
    # It was bad copy/paste.
    op.execute(
        "ALTER TABLE objectives ENABLE TRIGGER check_parent_objective_level_depth;"
    )


def downgrade():
    print("!! NO-OP IRREVERSIBLE MIGRATION !!")
