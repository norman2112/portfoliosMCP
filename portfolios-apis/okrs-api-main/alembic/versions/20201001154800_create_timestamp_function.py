"""create timestamp function

Revision ID: 20201001154800
Revises: 20201001100516
Create Date: 2020-10-01 15:48:00.954776

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20201001154800"
down_revision = "20201001100516"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "CREATE OR REPLACE FUNCTION trigger_set_timestamp() "
        "RETURNS TRIGGER AS $$ "
        "BEGIN "
        "NEW.updated_at = NOW();"
        "RETURN NEW;"
        "END; "
        "$$ LANGUAGE plpgsql;"
    )


def downgrade():
    op.execute("DROP FUNCTION IF EXISTS trigger_set_timestamp")
