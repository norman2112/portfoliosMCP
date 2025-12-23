"""cleanup old orphaned work items

Revision ID: 20210407121533
Revises: 20210407092008
Create Date: 2021-04-07 12:15:36.395112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210407121533"
down_revision = "20210407092008"
branch_labels = None
depends_on = None


def upgrade():
    print("Deleting orphaned WorkItems")
    op.execute(
        "DELETE FROM work_items WHERE id IN "
        "("
        "SELECT wi.id FROM work_items AS wi "
        "LEFT JOIN key_result_work_item_mappings AS krwim ON wi.id = krwim.work_item_id "
        "WHERE krwim.id IS NULL"
        ")"
    )


def downgrade():
    print("!!! Irreversible Migration !!! ")
