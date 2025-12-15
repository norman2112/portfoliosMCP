"""Utilities for Pubnub implementation."""

import os
import hashlib


def get_container_channel_name(
    tenant_id_str, tenant_group_id_str, app_name, container_id
):
    """Get a channel name from the current container context."""

    channel_name_str = (
        f"channel560068_{tenant_id_str}_{tenant_group_id_str}_{app_name}_{container_id}"
    )

    channel_name = hashlib.md5(channel_name_str.encode("utf-8")).hexdigest()

    return f"chn_{channel_name}"


def get_tenant_channel_name(tenant_group_id_str):
    """Get a global channel name for the current_tenant_group_id."""

    channel_name_str = f"channel560068_{tenant_group_id_str}"
    channel_name = hashlib.md5(channel_name_str.encode("utf-8")).hexdigest()

    return f"chn_{channel_name}"


def get_user_channel_name(user_id):
    """Get a global channel name for the user_id."""

    channel_name_str = f"channel560068_{user_id}"
    channel_name = hashlib.md5(channel_name_str.encode("utf-8")).hexdigest()

    return f"chn_{channel_name}"


def get_subscriber_key():
    """Retrieve Pubnub subscriber key."""

    return os.environ.get("PUBNUB_SUBSCRIBER_KEY", "")


def get_publish_key():
    """Retrieve Pubnub publish key."""

    return os.environ.get("PUBNUB_PUBLISH_KEY", "")


def get_secret_key():
    """Retrieve Pubnub secret key."""

    return os.environ.get("PUBNUB_SECRET_KEY", "")


def get_pubnub_uuid():
    """
    Get the preconfigured UUID.

    This might eventually be configured separately for different environments.
    """

    return os.environ.get("PUBNUB_UUID", "default_pubnub_user_id_uuid")


def get_pubnub_object():
    """Get a new pubnub object which was initialised at the start of app."""
    from okrs_api.main import application  # pylint: disable=import-outside-toplevel

    pubnub = application._subapps[0]["pubnub"]
    return pubnub


def pubnub_push(channel_name, message):
    """Push an event to pubnub channel."""

    try:
        pubnub_obj = get_pubnub_object()
        envelop = pubnub_obj.publish().channel(channel_name).message(message).sync()
        print("Pubnub event pushed:", str(envelop.result))
    except BaseException as pubnub_ex:
        print(pubnub_ex)
        return False

    return True


def send_pubnub_event_for_user(user_id, action_name):
    """Push an event to user pubnub channel."""
    supported_action_names = ["current_user_async", "list_activity_containers_async"]
    if action_name in supported_action_names:
        channel_name = get_user_channel_name(user_id)
        message = dict(id=user_id, type=action_name, action="get")
        pubnub_push(channel_name, message)
