"""repopulate actions in activity logs

Revision ID: 20210326104550
Revises: 20210322174639
Create Date: 2021-03-26 10:45:52.029986

"""
import pathlib

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session

from open_alchemy import init_yaml, models

ROOT_DIR = pathlib.Path(__file__).parent.parent.parent
SPECIFICATION_DIR = ROOT_DIR / "openapi"

init_yaml(SPECIFICATION_DIR / "openapi.yml")


# revision identifiers, used by Alembic.
revision = "20210326104550"
down_revision = "20210322174639"
branch_labels = None
depends_on = None

BASIC_ACTION_TRANSLATIONS = {
    "created": "insert",
    "updated": "update",
    "deleted": "delete",
}

OTHER_ACTION_TRANSLATIONS = {
    "connected": "insert",
    "disconnected": "delete",
}


def transpose_dict(dict):
    """Transpose key/values in a dict and return the new dict."""
    return {v: k for (k, v) in dict.items()}


def deduce_table(log):
    if log.action in ["connected", "disconnected"]:
        return "key_result_work_item_mappings"

    base_ids = [log.objective_id, log.key_result_id, log.progress_point_id]
    ids_used = len([id for id in base_ids if id])
    if ids_used == 3:
        return "progress_points"

    if ids_used == 2:
        return "key_results"

    if ids_used == 1:
        return "objectives"


def upgraded_action_from_log(log):
    """Return the action name for upgrading."""
    table = deduce_table(log)
    all_translations = BASIC_ACTION_TRANSLATIONS | OTHER_ACTION_TRANSLATIONS
    action = all_translations.get(log.action)
    if all([action, table]):
        return f"{action}.{table}"


def downgraded_action_from_log(upgraded_action):
    """Return the action name for downgrading."""
    if "." not in upgraded_action:
        return

    action_name, table = upgraded_action.split(".")
    if table == "key_result_work_item_mappings":
        translations = transpose_dict(OTHER_ACTION_TRANSLATIONS)
    else:
        translations = transpose_dict(BASIC_ACTION_TRANSLATIONS)

    return translations.get(action_name)


def upgrade():
    # session = Session(bind=op.get_bind())
    # logs = session.query(models.ActivityLog).all()
    # for log in logs:
    #     print(f"Upgrading log #{log.id} from deprecated action '{log.action}'")
    #     new_action = upgraded_action_from_log(log)
    #     if new_action:
    #         log.action = new_action
    #         session.add(log)
    #         print(f"- upgraded to '{new_action}'")
    #     else:
    #         print(
    #             f"!! COULD NOT find upgradable translations for the log action '{log.action}'"
    #         )
    #
    # session.commit()
    return


def downgrade():
    # session = Session(bind=op.get_bind())
    # logs = session.query(models.ActivityLog).all()
    # for log in logs:
    #     print(f"Downgrading log #{log.id} with upgraded action '{log.action}'")
    #     old_action = downgraded_action_from_log(log.action)
    #     if old_action:
    #         log.action = old_action
    #         session.add(log)
    #         print(f"- downgraded to '{old_action}'")
    #     else:
    #         print(
    #             f"!! COULD NOT find downgradable translations for the log action '{log.action}'"
    #         )
    #
    # session.commit()
    return
