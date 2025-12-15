"""Call Planview Admin API and adapt user service response with PV user ids."""
from okrs_api.external_apis.pvadmin.adapters import (
    adapt_users_response_with_pvid,
    adapt_user_details_response,
)
from okrs_api.external_apis.pvadmin.services import PVAdminUserService


async def add_pvid_to_response_data(input_prepper, response_data, env_selector=None):
    """Stitch in planview_user_id in response data."""

    user_admin_service = PVAdminUserService(input_prepper)

    tenant_user_ids = [response["id"] for response in response_data]
    pvid_response = await user_admin_service.planview_user_ids(
        tenant_user_ids, env_selector=env_selector
    )

    if pvid_response.ok:
        pvid_response_data = await pvid_response.json()
    else:
        pvid_response_data = {}

    return adapt_users_response_with_pvid(pvid_response_data, response_data)


async def add_pvid_user_details_to_response_data(input_prepper, response_data):
    """Stitch in planview users info in response data."""

    user_admin_service = PVAdminUserService(input_prepper)
    all_user_details = []

    for user in response_data:
        pv_user_id = user["planview_user_id"]
        app_user_id = user["id"]
        user_details_response = {
            "id": pv_user_id,
            "email": None,
            "firstName": None,
            "lastName": None,
        }
        if pv_user_id:
            api_response = await user_admin_service.planview_user_details(pv_user_id)
            if api_response.ok:
                user_details_response = await api_response.json()
        all_user_details.append(user | user_details_response | {"id": app_user_id})

    return adapt_user_details_response(all_user_details)


async def get_current_user(input_prepper):
    """Get current user details."""

    user_service = PVAdminUserService(input_prepper)
    api_response = await user_service.planview_user_current_details()
    current_user_details = {}

    if api_response.ok:
        current_user_details = await api_response.json()

    return current_user_details
