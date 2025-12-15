"""delete all orphaned work items

Revision ID: 20210520153255
Revises: 20210516104250
Create Date: 2021-05-20 15:32:56.609722

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210520153255"
down_revision = "20210516104250"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure that there are no "illegal" work items (ones without a
    # `work_item_container_id`) before we proceed to the next migration and
    # make the work_item_container_id non-nullable.
    op.execute("DELETE from work_items where work_items.work_item_container_id IS NULL")


def downgrade():
    pass
    # IRREVERSIBLE migration
