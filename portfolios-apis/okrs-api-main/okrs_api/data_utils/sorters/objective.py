"""For sorting the objectives into an insertion order."""


def traverse_parent_objectives(objective, traversal_path=None):
    """Return the traversal path of the parent objectives."""
    traversal_path = traversal_path or []
    traversal_path.append(objective)
    if objective.parent_objective:
        traverse_parent_objectives(objective.parent_objective, traversal_path)

    return traversal_path


def parent_objective_order(objective):
    """Return a list of objectives, in the order they should be inserted."""
    traversal_list = traverse_parent_objectives(objective)
    traversal_list.reverse()
    return traversal_list


def objective_sorter(objectives):
    """
    Sort objectives into a working insertion order.

    :param [Objective] objectives: all the objectives

    Returns: the final list of the correct insertion order of all the
    objectives.
    """
    final_list = []
    for objective in objectives:
        insertion_list = parent_objective_order(objective)
        final_list = append_if_new(final_list, insertion_list)

    return final_list


def append_if_new(current_list, add_list):
    """
    Add all items from one list to the other, if unique.

    This utility will make it so that items are added to the
    current_list from the new_list. Any duplicates are disregarded. This
    returned the current_list.
    """

    for item in add_list:
        if item not in current_list:
            current_list.append(item)

    return current_list
