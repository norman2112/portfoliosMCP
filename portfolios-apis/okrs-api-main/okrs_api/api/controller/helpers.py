"""Helpers for the controllers."""

import json

E1_WORK = "e1_work"
E1_STRATEGY = "e1_strategy"
LK_BOARD = "lk_board"
scope_type_product_map = {
    "e1_strategy": "e1_prm",
    "e1_work": "work",
    "lk_board": "leankit",
}

# pylint:disable=W0613


def extract_hasura_payload(body):
    """
    Extract the Hasura payload, accommodating for Hasura bug.

    For Cron actions and one-time actions, Hasura sends a payload. This
    payload should not have to be parsed as json, but seems to have been
    double-escaped by Hasura when it is sent over. This method ensures that
    when Hasura fixes the issue, we will still be able to read the 'payload'
    key properly.
    """
    try:
        return json.loads(body["payload"])
    except TypeError:
        return body["payload"]


def sanitise_product_type(product_type):
    """
    Sanitise product type name.

    This is applicable for Portfolios as they send two types of product type e1 and e1_prm.
    We convert anything that starts with e1 to e1_prm. For others it is the same value.
    """

    product_type_str = str(product_type).lower()
    if product_type_str in ["e1", "e1_prm"]:
        return "e1_prm"

    return product_type_str.lower()


def is_pvadmin_connected_okrs(input_prepper):
    """Determine if we are in a PVAdmin connected context."""

    tenant_group_id = input_prepper.tenant_group_id_original

    if not tenant_group_id:
        return False

    return True


def get_app_name_for_product_type(product_type):
    """Convert Product type to app_name."""

    if product_type in ["e1_prm", "e1", "e1_work", "e1_strategy"]:
        return "e1_prm"
    return "leankit"


def get_container_type_for_product_type(product_type):
    """Convert Product type to container_type."""
    container_map = {
        E1_STRATEGY: ["e1_prm", "e1", "e1_strategy"],
        LK_BOARD: ["leankit", "lk_board"],
        E1_WORK: ["work", "e1_work"],
    }
    for key in container_map:
        if product_type in container_map[key]:
            return key
    return None


def get_product_type_for_connected_app(product_type):
    """Convert Product type to connected app_name."""
    app_map = {
        "e1_prm": ["e1_prm", "e1", "e1_strategy"],
        "leankit": ["leankit", "lk_board"],
        "e1_work": ["work", "e1_work"],
    }
    for key in app_map:
        if product_type in app_map[key]:
            return key
    return None


def get_product_types_for_connected_app(product_types):
    """Convert Product types to connected app_names."""
    return [get_product_type_for_connected_app(each) for each in product_types]


def get_wrangler_product_type(input_prepper):
    """Get scope type if there is no product type given in payload."""
    if input_prepper.input_parser.get("scope_type", None):
        input_product_type = scope_type_product_map[
            input_prepper.input_parser.scope_type
        ]
    else:
        input_product_type = sanitise_product_type(
            input_prepper.input_parser.product_type
        )
        if input_product_type == "e1_work":
            input_product_type = "work"
    return input_product_type


def get_product_type(input_prepper):
    """Get scope type if there is no product type given in payload."""
    if input_prepper.input_parser.get("scope_type", None):
        input_product_type = input_prepper.input_parser.scope_type
    else:
        input_product_type = sanitise_product_type(
            input_prepper.input_parser.product_type
        )
        # if input_product_type == "e1_work":
        #     input_product_type = "work"
    return input_product_type


def get_product_types(input_prepper):
    """Get scope types if there are no product types given in payload."""
    if input_prepper.input_parser.get("scope_types", None):
        return input_prepper.input_parser.scope_types
    if input_prepper.input_parser.get("product_types", None):
        product_list = []
        for each in input_prepper.input_parser.product_types:
            product = sanitise_product_type(each)
            # if product == "e1_work":
            #     product = "work"
            product_list.append(product)
        return product_list
    return []


def get_container_type(product_type):
    """Get container_type for fetching WIC."""
    container_type = get_container_type_for_product_type(product_type)
    if container_type in [E1_STRATEGY, LK_BOARD]:
        return None
    return container_type


def get_context_id(input_prepper, models, key_result_id):
    """Get external_id from WIC."""
    with input_prepper.db_session() as db_session:
        work_item_containers = (
            db_session.query(models.WorkItemContainer)
            .join(models.Objective)
            .join(models.KeyResult)
            .filter(
                models.WorkItemContainer.id == models.Objective.work_item_container_id
            )
            .filter(models.Objective.id == models.KeyResult.objective_id)
            .filter(models.KeyResult.id == key_result_id)
            .all()
        )
        if work_item_containers:
            return work_item_containers[0].external_id
    return None
