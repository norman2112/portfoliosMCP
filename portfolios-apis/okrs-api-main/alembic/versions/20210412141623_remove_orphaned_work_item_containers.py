"""remove orphaned work item containers

Revision ID: 20210412141623
Revises: 20210408134132
Create Date: 2021-04-12 14:16:26.444089

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210412141623"
down_revision = "20210408134132"
branch_labels = None
depends_on = None


def upgrade():
    print("Deleting orphaned WorkItemContainers")
    op.execute(
        "DELETE FROM work_item_containers WHERE id IN "
        "("
        "SELECT wic.id FROM work_item_containers AS wic "
        "LEFT JOIN objectives ON wic.id = objectives.work_item_container_id "
        "LEFT JOIN work_items on wic.id = work_items.work_item_container_id "
        "WHERE work_items.id IS NULL and objectives.id IS NULL"
        ")"
    )


def downgrade():
    print("!!! Irreversible Migration !!! ")
