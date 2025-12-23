"""
This file contains,
 - Payloads for Hasura actions such as create activity, search activity, connect activity.
"""

DEFAULT_CONTEXT_ID = "10121496436"
DEFAULT_ACTIVITY_TYPE_ID = "10121496438"
DEFAULT_DOMAIN = "d08.leankit.io"
DEFAULT_PRODUCT_TYPE = "leankit"


def make_payload(action_name, with_context_id=True, input_merge=None):
    """
    Make hasura payloads dynamically.

    :param str action_name: the name of the Hasura action
    :param bool with_context_id: use the default context id
    :param dict input_merge: merge a dict into the input section
    """
    body = {
        "input": {
            "product_type": DEFAULT_PRODUCT_TYPE,
            "domain": DEFAULT_DOMAIN,
        },
        "action": {"name": action_name},
    }

    if with_context_id:
        body["context_id"] = DEFAULT_CONTEXT_ID

    if input_merge:
        body = {**body, **input_merge}

    return body


def connect_leankit_activities(key_result, work_item):
    """
    Payload from Hasura to connect a Leankit card for a key_result.
    Will connect only one work_item, for testing purposes.
    """
    wic = key_result.objective.work_item_container
    return {
        "input": {
            "product_type": "leankit",
            "domain": "d08.leankit.io",
            "key_result_id": key_result.id,
            "work_item_container": {
                "external_id": wic.external_id,
                "external_type": wic.external_type,
                "external_title": wic.external_title,
            },
            "work_items": [
                {
                    "item_type": work_item.item_type,
                    "planned_start": work_item.planned_start,
                    "planned_finish": work_item.planned_finish,
                    "title": work_item.title,
                    "external_id": work_item.external_id,
                    "external_type": work_item.external_type,
                    "container_type": work_item.container_type,
                    "state": work_item.state,
                }
            ],
        },
        "action": {"name": "connect_activities"},
    }


def create_leankit_activity(key_result=None):
    """
    Payload from Hasura to create a Leankit card
    """

    kr_id = key_result.id if key_result else 1
    return {
        "input": {
            "key_result_id": kr_id,
            "context_id": "10121496436",
            "context_title": "New OKRs board",
            "product_type": "leankit",
            "domain": "d08.leankit.io",
            "title": "Go-Kart Extravaganza",
            "planned_start": "2020-01-01",
            "planned_finish": "2024-01-01",
            "external_activity_type_id": "10121496438",
        },
        "action": {"name": "create_activity"},
    }


def search_leankit_activities_containers():
    """
    Payload from Hasura to search a leankit card/board
    """
    return {
        "input": {
            "product_type": "leankit",
            "domain": "d08.leankit.io",
            "search_string": "Test",
        },
        "action": {"name": "search_activity_containers"},
    }


def search_leankit_activities():
    """
    Payload from Hasura to search a board for a leankit card.
    """
    return {
        "input": {
            "product_type": "leankit",
            "domain": DEFAULT_DOMAIN,
            "context_id": DEFAULT_CONTEXT_ID,
            "search_string": "Test",
        },
        "action": {"name": "search_activities"},
    }


def update_level_config_request():
    """Return the request body for updating the level config."""
    body = {
        "input": {
            "level_config": [
                {
                    "depth": 0,
                    "name": "Enterprise",
                    "color": "#ba8aa4",
                    "is_default": False,
                },
                {
                    "depth": 1,
                    "name": "Portfolio",
                    "color": "#f87b55",
                    "is_default": False,
                },
                {
                    "depth": 2,
                    "name": "Program",
                    "color": "#8ab98e",
                    "is_default": False,
                },
                {"depth": 3, "name": "Team", "color": "#608eb6", "is_default": True},
            ],
        },
        "action": {"name": "update_level_config"},
    }
    return body


def insert_level_config_middle_request():
    """Return the request body for inserting a level config in the middle."""
    body = {
        "input": {
            "new_level": {
                "depth": 2,
                "name": "Team 0",
                "color": "#ba8aa3",
                "is_default": False,
            }
        },
        "action": {"name": "insert_level_config"},
    }
    return body


def insert_level_config_beginning_request():
    """Return the request body for inserting a level config in the beginning."""
    body = {
        "input": {
            "new_level": {
                "depth": 0,
                "name": "Super Enterprise",
                "color": "#ba8aa3",
                "is_default": False,
            }
        },
        "action": {"name": "insert_level_config"},
    }
    return body


def insert_level_config_middle_request2():
    """Return the request body for inserting a level config in the middle."""
    body = {
        "input": {
            "new_level": {
                "depth": 1,
                "name": "Minimum Support",
                "color": "#ba8aa3",
                "is_default": False,
            }
        },
        "action": {"name": "insert_level_config"},
    }
    return body


def insert_level_config_last_request():
    """Return the request body for inserting a level config at last."""
    body = {
        "input": {
            "new_level": {
                "depth": 3,
                "name": "QA",
                "color": "#ba8aa3",
                "is_default": False,
            }
        },
        "action": {"name": "insert_level_config"},
    }
    return body


def insert_level_config_invalid_request1():
    """Return the request body for inserting a level config at last."""
    body = {
        "input": {
            "new_level": {
                "depth": 4,
                "name": "QA",
                "color": "#ba8aa3",
                "is_default": False,
            }
        },
        "action": {"name": "insert_level_config"},
    }
    return body


def insert_level_config_invalid_request2():
    """Return the request body for inserting a level config at last."""
    body = {
        "input": {
            "new_level": {
                "depth": -1,
                "name": "QA",
                "color": "#ba8aa3",
                "is_default": False,
            }
        },
        "action": {"name": "insert_level_config"},
    }
    return body
