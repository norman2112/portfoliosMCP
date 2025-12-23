"""
Leankit Response Payloads.

These payloads are from Leankit's API.
"""


def leankit_search_activities_response():
    """
    Response payload from Leankit cards search API
    """
    return {"activity_name": "Test", "message": "OK"}


def leankit_search_activity_containers_response():
    """
    Response payload from Leankit boards search API.
    """
    return {"board_name": "Test", "message": "OK"}


def leankit_list_activity_types_response():
    """
    Response payload from Leankit for listing activity types.
    """
    return {"activity_type": "defect", "message": "OK"}


def search_users_response():
    return {
        "pageMeta": {
            "totalRecords": 3,
            "offset": 0,
            "limit": 25,
            "startRow": 1,
            "endRow": 3,
        },
        "boardUsers": [
            {
                "userId": "1234",
                "firstName": "Bob",
                "lastName": "Smith",
                "emailAddress": "Bob@myco.com",
                "boardId": "10113285944",
                "administrator": False,
                "WIP": 0,
                "id": "10113991953",
                "licenseType": "focused",
                "role": {"key": "boardReader", "value": 1, "label": "Reader"},
                "assignedBoards": [
                    {"id": "10113986361", "title": "Hey I made a board from a template"}
                ],
            },
        ],
    }


def user_info_response(
    board_role_key="boardCreator", board_id="1234", board_role_data=None
):
    """
    Return a valid leankit user info response.

    :param str board_role_key: a valid Leankit board role
    :param str board_id: the id of the leankit board
    :param [(board_id, board_role_key)] board_role_data:

    The `board_role_data` param will override all board roles.
    This allows for multiple board roles to be created, simply by supplying
    a list of (board_id, board_role_key) tuples.
    """
    board_role_data = board_role_data or [(board_id, board_role_key)]
    return {
        "id": "1234",
        "username": "pstiles@planview.com",
        "firstName": "Patti",
        "lastName": "Stiles",
        "fullName": "Patti Stiles",
        "emailAddress": "pstiles@planview.com",
        "lastAccess": "2021-03-30T17:20:46.900Z",
        "dateFormat": "MM/dd/yyyy",
        "administrator": False,
        "enabled": True,
        "deleted": False,
        "organizationId": "10100000101",
        "boardCreator": False,
        "timeZone": "America/Chicago",
        "licenseType": "full",
        "externalUserName": None,
        "boardRoles": [_construct_board_role(*data) for data in board_role_data],
    }


def _construct_board_role(board_id, board_role_key):
    return {
        "boardId": board_id,
        "WIP": None,
        "role": {
            "key": board_role_key,
            "value": 5,
            "label": board_role_key,
        },
    }
