"""add platforma_functions schema

Revision ID: 20210830094752
Revises: 20210818101646
Create Date: 2021-08-30 09:47:58.196871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210830094752"
down_revision = "20210818101646"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS platforma_functions;")


def downgrade():
    op.execute("DROP SCHEMA IF EXISTS platforma_functions;")
