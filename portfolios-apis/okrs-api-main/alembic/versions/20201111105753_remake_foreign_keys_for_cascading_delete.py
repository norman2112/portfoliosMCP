"""remake foreign keys for cascading delete

Revision ID: 20201111105753
Revises: 20201110114429
Create Date: 2020-11-11 10:57:53.790892

"""
from alembic import op
import re


# revision identifiers, used by Alembic.
revision = "20201111105753"
down_revision = "20201110114429"
branch_labels = None
depends_on = None

FOREIGN_KEY_DATA = [
    {
        "key": "key_results_objective_id_fkey",
        "child": "key_results",
        "parent": "objectives",
    },
    {
        "key": "key_result_work_item_mappings_key_result_id_fkey",
        "child": "key_result_work_item_mappings",
        "parent": "key_results",
    },
    {
        "key": "progress_points_key_result_id_fkey",
        "child": "progress_points",
        "parent": "key_results",
    },
]


def derive_fk_column_from_parent(parent_table):
    singular = re.sub(r"s$", "", parent_table)
    return f"{singular}_id"


def fk_attribs_for_data(fk_data):
    return [
        fk_data["key"],
        fk_data["child"],
        fk_data["parent"],
        [derive_fk_column_from_parent(fk_data["parent"])],
        ["id"],
    ]


def upgrade():
    for fk_data in FOREIGN_KEY_DATA:
        op.drop_constraint(fk_data["key"], fk_data["child"], type_="foreignkey")
        op.create_foreign_key(*fk_attribs_for_data(fk_data), ondelete="CASCADE")


def downgrade():
    for fk_data in FOREIGN_KEY_DATA:
        op.drop_constraint(fk_data["key"], fk_data["child"], type_="foreignkey")
        op.create_foreign_key(
            *fk_attribs_for_data(fk_data),
        )
