"""update unique index for settings

Revision ID: 20220819124157
Revises: 20220818215244
Create Date: 2022-08-19 12:42:03.394329

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20220819124157"
down_revision = "20220819083414"
branch_labels = None
depends_on = None


def index_exists(name):
    connection = op.get_bind()
    result = connection.execute(
        "SELECT exists(SELECT 1 from pg_indexes where indexname = '{}') as ix_exists;".format(
            name
        )
    ).first()
    return result.ix_exists


def upgrade():
    if index_exists("ix_settings_tenant_id_str"):
        op.drop_index("ix_settings_tenant_id_str", table_name="settings")

    if index_exists("ix_settings_tenant_id_group_id"):
        op.drop_index("ix_settings_tenant_id_group_id", table_name="settings")

    op.create_index(
        op.f("ix_settings_tenant_id_group_id"),
        "settings",
        ["tenant_id_str", "tenant_group_id_str"],
        unique=True,
    )


def downgrade():
    if index_exists("ix_settings_tenant_id_str"):
        op.drop_index("ix_settings_tenant_id_str", table_name="settings")

    if index_exists("ix_settings_tenant_id_group_id"):
        op.drop_index("ix_settings_tenant_id_group_id", table_name="settings")

    op.create_index(
        op.f("ix_settings_tenant_id_str"), "settings", ["tenant_id_str"], unique=True
    )
