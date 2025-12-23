"""Utility methods for pubnub handlers."""

from open_alchemy import models
from okrs_api.pubnub.utils import pubnub_push, get_container_channel_name


MAX_DEPTH_LEVEL = 10


def send_events_to_objective_tree(
    db_session, objective_id, message, depth=1, visited_objectives=None
):
    """Send a message to all objectives in the hierarchy **recursively**."""
    print(
        "Send pubnub for {} at depth {}, visited {}, message {}".format(
            objective_id, depth, visited_objectives, message
        )
    )

    # Check if we have already sent event for this objective
    if visited_objectives and (objective_id in visited_objectives):
        print("Event already sent for {}, nothing to do here".format(objective_id))
        return

    if depth > MAX_DEPTH_LEVEL:
        print(
            "WARNING: maximum OKR level ({}) has been reached, won't send any more events".format(
                MAX_DEPTH_LEVEL
            )
        )
        return

    current_objective = db_session.query(models.Objective).get(objective_id)
    if not current_objective:
        return

    current_obj_channel_name = get_container_channel_name(
        current_objective.tenant_id_str,
        current_objective.tenant_group_id_str,
        current_objective.work_item_container.app_name,
        current_objective.work_item_container.external_id,
    )

    if not current_obj_channel_name:
        return

    message["id"] = objective_id
    if not visited_objectives:
        visited_objectives = set()

    visited_objectives.add(current_objective.id)
    pubnub_push(current_obj_channel_name, message)

    # parents = (
    #     db_session.query(models.Objective)
    #     .filter_by(id=current_objective.parent_objective_id)
    #     .filter_by(deleted_at_epoch=0)
    #     .all()
    # )
    # children = (
    #     db_session.query(models.Objective)
    #     .filter(models.Objective.parent_objective_id == current_objective.id)
    #     .filter_by(deleted_at_epoch=0)
    #     .all()
    # )
    #
    # for obj in parents:
    #     if visited_objectives and (obj.id in visited_objectives):
    #         # We have already sent the event
    #         print("Event already sent for {}, nothing to do here".format(obj.id))
    #         continue
    #     send_events_to_objective_tree(
    #         db_session,
    #         obj.id,
    #         message,
    #         depth=depth + 1,
    #         visited_objectives=visited_objectives,
    #     )
    #
    # for obj in children:
    #     if visited_objectives and (obj.id in visited_objectives):
    #         # We have already sent the event
    #         print("Event already sent for {}, nothing to do here".format(obj.id))
    #         continue
    #     send_events_to_objective_tree(
    #         db_session,
    #         obj.id,
    #         message,
    #         depth=depth + 1,
    #         visited_objectives=visited_objectives,
    #     )
