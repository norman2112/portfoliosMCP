"""Set of adapters to adapt API response to further add new information."""


def adapt_users_response_with_pvid(pvid_response_data, response_data):
    """Add planview_user_id along with id (tenant user id)."""

    if pvid_response_data and ("users" in pvid_response_data):
        pv_user_map = pvid_response_data.get("users", {})
    elif pvid_response_data and ("userIds" in pvid_response_data):
        pv_user_map = pvid_response_data.get("userIds", {})
    else:
        pv_user_map = {}

    return [
        {**user_response, "planview_user_id": pv_user_map.get(user_response["id"])}
        for user_response in response_data
    ]


def adapt_user_details_response(user_details):
    """Add user details along with planview_user_id."""
    return [
        {
            "avatar": user.get("avatarUrl"),
            "email_address": user.get("email"),
            "first_name": user.get("firstName"),
            "last_name": user.get("lastName"),
            "is_deleted": not user.get("planview_user_id", False),
            "id": user.get("id"),
            "planview_user_id": user.get("planview_user_id"),
        }
        for user in user_details
    ]
