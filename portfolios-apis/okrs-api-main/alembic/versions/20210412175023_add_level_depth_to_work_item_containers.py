"""add level depth to work item containers

Revision ID: 20210412175023
Revises: 20210412141623
Create Date: 2021-04-12 17:50:26.021219

"""
import pathlib

from alembic import op
import sqlalchemy as sa

# from sqlalchemy.orm.session import Session
#
# from open_alchemy import init_yaml, models
#
# from okrs_api.model_helpers.settings import LevelConfigParser

# ROOT_DIR = pathlib.Path(__file__).parent.parent.parent
# SPECIFICATION_DIR = ROOT_DIR / "openapi"
#
# init_yaml(SPECIFICATION_DIR / "openapi.yml")

# revision identifiers, used by Alembic.
revision = "20210412175023"
down_revision = "20210412141623"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass


#  This has done it's job as being a one-time migration. It remains commented
# now that it is no longer needed.
# Keeping this in migrations is unsustainable, as the generated models might
# differ the actual database state; this would cause an error when migrating
# from scratch.
#
# def _get_or_create_setting(db_session, tenant_id_str):
#     """Find the setting for this tenant_id_str, or create one."""
#     setting = (
#         db_session.query(models.Setting).filter_by(tenant_id_str=tenant_id_str).first()
#     )
#     if setting:
#         return setting
#
#     setting = models.Setting(tenant_id_str=tenant_id_str)
#     db_session.add(setting)
#     try:
#         db_session.commit()
#         return setting
#     except Exception as e:
#         db_session.rollback()
#         print(f"Could not create setting for {tenant_id_str=}", e)
#
#
# def upgrade():
#     db_session = Session(bind=op.get_bind())
#     wics_to_update = (
#         db_session.query(models.WorkItemContainer)
#         .filter_by(level_depth_default=None)
#         .all()
#     )
#     if not wics_to_update:
#         print("No WorkItemContainers need updating. Continuing.. ")
#
#     for wic in wics_to_update:
#         setting = _get_or_create_setting(db_session, wic.tenant_id_str)
#         if not setting:
#             # We could not create the Setting for some reason.
#             # Better to not hold up the migration rather than raise an error.
#             continue
#
#         parser = LevelConfigParser(setting.level_config)
#         depth = parser.default_depth()
#         wic.level_depth_default = depth
#         db_session.add(wic)
#         print(f"WorkItemContainer {wic.id} now has default depth of {depth}")
#         try:
#             db_session.commit()
#         except Exception as e:
#             db_session.rollback()
#             print(
#                 "!!! ERROR: could not update the level depths of work item containers.",
#                 e,
#             )
#
#
# def downgrade():
#     print("!!! Irreversible Migration!")
