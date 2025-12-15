"""fix broken work item container restraint

Revision ID: 20210204082127
Revises: 20210203140535
Create Date: 2021-02-04 08:21:30.610500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210204082127"
down_revision = "20210203140535"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint(
        "ux_work_item_container_external", "work_item_containers", type_="unique"
    )
    op.create_unique_constraint(
        "ux_work_item_container_external",
        "work_item_containers",
        ["external_type", "external_id"],
    )
    op.drop_constraint("ux_work_item_external", "work_items", type_="unique")
    op.create_unique_constraint(
        "ux_work_item_external", "work_items", ["external_type", "external_id"]
    )


def downgrade():
    print("!!! Already reversed in the upgrade !!!")
