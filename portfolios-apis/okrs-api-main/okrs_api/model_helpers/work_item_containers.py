"""Model helpers involving the WorkItemContainers."""

from open_alchemy import models
from sqlalchemy import or_, and_

from okrs_api.model_helpers.common import commit_db_session


def decrement_level_depth_defaults(
    db_session, tenant_id_str, tenant_group_id_str, deleted_level_depth, level_config
):
    """
    Decrement level_depth_defaults where applicable.

    All level_depth_defaults that are greater than the level_depth supplied
    should be decremented by 1.
    """

    try:
        if deleted_level_depth >= len(level_config):  # if it is last level
            db_session.query(models.WorkItemContainer).filter(
                models.WorkItemContainer.level_depth_default >= deleted_level_depth
            ).filter(
                or_(
                    and_(
                        models.WorkItemContainer.tenant_id_str == tenant_id_str,
                        models.WorkItemContainer.tenant_id_str != "",
                    ),
                    models.WorkItemContainer.tenant_group_id_str == tenant_group_id_str,
                )
            ).update(
                {"level_depth_default": fetch_default_level_index(level_config)},
                synchronize_session="fetch",
            )
        else:
            db_session.query(models.WorkItemContainer).filter(
                models.WorkItemContainer.level_depth_default > deleted_level_depth
            ).filter(
                or_(
                    and_(
                        models.WorkItemContainer.tenant_id_str == tenant_id_str,
                        models.WorkItemContainer.tenant_id_str != "",
                    ),
                    models.WorkItemContainer.tenant_group_id_str == tenant_group_id_str,
                )
            ).update(
                {
                    "level_depth_default": models.WorkItemContainer.level_depth_default
                    - 1
                },
                synchronize_session="fetch",
            )
        commit_db_session(db_session)
    except Exception as e:
        db_session.rollback()
        raise e


def decrement_objective_editing_levels(
    db_session, tenant_id_str, tenant_group_id_str, deleted_level_depth
):
    """
    Decrement objective_editing_levels on WorkItemContainers.

    Return a list of modified WorkItemContainers.
    """
    all_wics = (
        db_session.query(models.WorkItemContainer)
        .filter(
            or_(
                and_(
                    models.WorkItemContainer.tenant_id_str == tenant_id_str,
                    models.WorkItemContainer.tenant_id_str != "",
                ),
                models.WorkItemContainer.tenant_group_id_str == tenant_group_id_str,
            )
        )
        .all()
    )
    modified_wics = []
    for wic in all_wics:
        if wic.objective_editing_levels and (
            max(wic.objective_editing_levels) >= deleted_level_depth
        ):
            # First, delete the [deleted] level from the editing levels.
            new_levels = wic.objective_editing_levels.copy()
            if deleted_level_depth in new_levels:
                new_levels.remove(deleted_level_depth)

            # Second, decrement any values higher than the deleted level.
            wic.objective_editing_levels = _reindexed_objective_editing_levels(
                depths=new_levels,
                deleted_level_depth=deleted_level_depth,
            )
            modified_wics.append(wic)

    return modified_wics


def increment_level_depth_defaults(
    db_session, tenant_id_str, tenant_group_id_str, inserted_level_depth
):
    """
    Increment level_depth_defaults where applicable.

    All level_depth_defaults that are greater than the level_depth supplied
    should be incremented by 1.
    """
    try:
        db_session.query(models.WorkItemContainer).filter(
            models.WorkItemContainer.level_depth_default >= inserted_level_depth
        ).filter(
            or_(
                and_(
                    models.WorkItemContainer.tenant_id_str == tenant_id_str,
                    models.WorkItemContainer.tenant_id_str != "",
                ),
                models.WorkItemContainer.tenant_group_id_str == tenant_group_id_str,
            )
        ).update(
            {"level_depth_default": models.WorkItemContainer.level_depth_default + 1},
            synchronize_session="fetch",
        )
        commit_db_session(db_session)
    except Exception as e:
        db_session.rollback()
        raise e


def fetch_default_level_index(config):
    """Retrieve index id of the default level from level config."""
    for each in config:
        if each["is_default"]:
            return each["depth"]
    return 0


def increment_objective_editing_levels(
    db_session, tenant_id_str, tenant_group_id_str, inserted_level_depth
):
    """
    Increment objective_editing_levels on WorkItemContainers.

    Return a list of modified WorkItemContainers.
    """
    all_wics = (
        db_session.query(models.WorkItemContainer)
        .filter(
            or_(
                and_(
                    models.WorkItemContainer.tenant_id_str == tenant_id_str,
                    models.WorkItemContainer.tenant_id_str != "",
                ),
                models.WorkItemContainer.tenant_group_id_str == tenant_group_id_str,
            )
        )
        .all()
    )
    modified_wics = []
    for wic in all_wics:
        if wic.objective_editing_levels and (
            max(wic.objective_editing_levels) >= inserted_level_depth
        ):
            new_levels = wic.objective_editing_levels.copy()

            # Increment any values higher than or equal to the inserted level.
            wic.objective_editing_levels = (
                _reindexed_objective_editing_levels_for_insert(
                    depths=new_levels,
                    inserted_level_depth=inserted_level_depth,
                )
            )
            modified_wics.append(wic)

    return modified_wics


def _reindexed_objective_editing_levels(depths, deleted_level_depth):
    """
    Reindex and return the depths based on the deleted_level_depth.

    Accommodate for duplicate values. Return the new, deprecated depths.
    """
    new_depths = set()
    for depth in depths:
        if depth > deleted_level_depth:
            depth = depth - 1
        new_depths.add(depth)

    new_depths = list(new_depths)
    new_depths.sort()
    return new_depths


def _reindexed_objective_editing_levels_for_insert(depths, inserted_level_depth):
    """
    Reindex and return the depths based on the deleted_level_depth.

    Accommodate for duplicate values. Return the new, deprecated depths.
    """
    new_depths = set()
    for depth in depths:
        if depth >= inserted_level_depth:
            depth = depth + 1
        new_depths.add(depth)

    new_depths = list(new_depths)
    new_depths.sort()
    return new_depths
