"""Functions concerning the levels in the Settings."""

from okrs_api.model_helpers.common import commit_db_session
from okrs_api.model_helpers.objectives import (
    decrement_objective_level_depths,
    increment_objective_level_depths,
)
from okrs_api.model_helpers.work_item_containers import (
    decrement_objective_editing_levels,
    decrement_level_depth_defaults,
    increment_objective_editing_levels,
    increment_level_depth_defaults,
)


def relevel_after_deletion(
    db_session, tenant_id_str, tenant_group_id_str, deleted_level_depth, level_config
):
    """
    Rewrite appropriate levels on WICs and Objectives.

    :param db_session db_session: the database session
    :param str tenant_id_str: the tenant_id_str for the org
    :param int deleted_level_depth: the level depth that was deleted

    - Rewrite the WICs `objective_editing_levels`
    - Rewrite the WICs `level_depth_default`
    - Rewrite the Objectives `level_depth`
    """
    modified_wics = decrement_objective_editing_levels(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        tenant_group_id_str=tenant_group_id_str,
        deleted_level_depth=deleted_level_depth,
    )
    if modified_wics:
        db_session.add_all(modified_wics)
        commit_db_session(db_session)

    decrement_objective_level_depths(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        tenant_group_id_str=tenant_group_id_str,
        deleted_level_depth=deleted_level_depth,
    )
    decrement_level_depth_defaults(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        tenant_group_id_str=tenant_group_id_str,
        deleted_level_depth=deleted_level_depth,
        level_config=level_config,
    )


def relevel_after_insert(
    db_session, tenant_id_str, tenant_group_id_str, inserted_level_depth
):
    """
    Rewrite appropriate levels on WICs and Objectives.

    :param db_session db_session: the database session
    :param str tenant_id_str: the tenant_id_str for the org
    :param int deleted_level_depth: the level depth that was inserted

    - Rewrite the WICs `objective_editing_levels`
    - Rewrite the WICs `level_depth_default`
    - Rewrite the Objectives `level_depth`
    """
    modified_wics = increment_objective_editing_levels(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        tenant_group_id_str=tenant_group_id_str,
        inserted_level_depth=inserted_level_depth,
    )
    if modified_wics:
        db_session.add_all(modified_wics)
        commit_db_session(db_session)

    increment_objective_level_depths(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        tenant_group_id_str=tenant_group_id_str,
        inserted_level_depth=inserted_level_depth,
    )
    increment_level_depth_defaults(
        db_session=db_session,
        tenant_id_str=tenant_id_str,
        tenant_group_id_str=tenant_group_id_str,
        inserted_level_depth=inserted_level_depth,
    )
