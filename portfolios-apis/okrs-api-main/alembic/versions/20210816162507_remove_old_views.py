"""remove old views

Revision ID: 20210816162507
Revises: 20210816113628
Create Date: 2021-08-16 16:25:11.124766

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210816162507"
down_revision = "20210816113628"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP VIEW IF EXISTS space_work_item_containers_view")
    op.execute("DROP VIEW IF EXISTS work_item_container_spaces_view")


def downgrade():
    op.execute(
        """
        CREATE OR REPLACE VIEW space_work_item_containers_view
        AS SELECT mappings.space_id,
        wics.id,
        wics.created_at,
        wics.updated_at,
        wics.external_title,
        wics.external_id,
        wics.external_type,
        wics.tenant_id_str
        FROM space_work_item_container_mappings mappings
        LEFT JOIN work_item_containers wics ON mappings.work_item_container_id = wics.id
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW work_item_container_spaces_view
        AS SELECT mappings.work_item_container_id,
        spaces.id,
        spaces.name,
        spaces.created_at,
        spaces.updated_at,
        spaces.tenant_id_str
        FROM space_work_item_container_mappings mappings
        LEFT JOIN spaces ON mappings.space_id = spaces.id
        """
    )
