"""Change existing settings to new default value

Revision ID: 20210413114056
Revises: 20210412175023
Create Date: 2021-04-13 11:40:58.530271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20210413114056"
down_revision = "20210412175023"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "UPDATE settings set level_config = "
        '\'[{ "depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": false },'
        '{ "depth": 1, "name": "Portfolio", "color": "#f87b55", "is_default": false },'
        '{ "depth": 2, "name": "Program", "color": "#8ab98e", "is_default": false },'
        '{ "depth": 3, "name": "Team", "color": "#608eb6", "is_default": true }]\';'
    )
    op.execute(
        "ALTER TABLE settings ALTER COLUMN level_config SET DEFAULT "
        '\'[{ "depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": false },'
        '{ "depth": 1, "name": "Portfolio", "color": "#f87b55", "is_default": false },'
        '{ "depth": 2, "name": "Program", "color": "#8ab98e", "is_default": false },'
        '{ "depth": 3, "name": "Team", "color": "#608eb6", "is_default": true }]\';'
    )


def downgrade():
    op.execute(
        "UPDATE settings set level_config = "
        '\'[{ "depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": false },'
        '{ "depth": 1, "name": "Value Stream", "color": "#f87b55", "is_default": false },'
        '{ "depth": 2, "name": "Program", "color": "#8ab98e", "is_default": false },'
        '{ "depth": 3, "name": "Team", "color": "#608eb6", "is_default": true }]\';'
    )
    op.execute(
        "ALTER TABLE settings ALTER COLUMN level_config SET DEFAULT "
        '\'[{ "depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": false },'
        '{ "depth": 1, "name": "Value Stream", "color": "#f87b55", "is_default": false },'
        '{ "depth": 2, "name": "Program", "color": "#8ab98e", "is_default": false },'
        '{ "depth": 3, "name": "Team", "color": "#608eb6", "is_default": true }]\';'
    )
