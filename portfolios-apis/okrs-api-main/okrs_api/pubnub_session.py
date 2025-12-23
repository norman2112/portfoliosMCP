"""Setup for the pubnub."""
import os

from pubnub.enums import PNReconnectionPolicy

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


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


async def init(app):
    """Initialize the pubnub connection."""

    # Retrieve the pubnub settings.
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = get_subscriber_key()
    pnconfig.publish_key = get_publish_key()
    pnconfig.ssl = True
    pnconfig.secret_key = get_secret_key()
    pnconfig.user_id = get_pubnub_uuid()
    pnconfig.reconnect_policy = PNReconnectionPolicy.NONE
    pubnub = PubNub(pnconfig)

    # Retrieve the application.
    # Connexion adds a default subapp.
    sub_app = app._subapps[0]

    # Store the information in the application context.
    sub_app["pubnub"] = pubnub
    yield

    # Delete the PubNub object on quit().
    try:
        del sub_app["pubnub"]
    except AttributeError as e:
        print(f"cannot delete the pubnub connexion object: {e}")
