"""Set of functions for testing pubnub implementation."""

import os
import sys

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import SubscribeListener, PubNub

from okrs_api.pubnub.utils import (
    get_pubnub_object,
    get_pubnub_uuid,
)


class PrintListener(SubscribeListener):
    """Listens to subscribed messages and prints on the stdout."""

    def message(self, pubnub, data):
        """Handle new message."""
        print("Received: ", data.message)


def subscribe_and_show_messages(channel_name):
    """Subscribe for new message."""
    pubnub_obj = get_pubnub_object()
    pubnub_obj.add_listener(PrintListener())
    pubnub_obj.subscribe().channels(channel_name).execute()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(1)

    channel_name = sys.argv[1]
    print(channel_name)
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = os.environ.get("PUBNUB_SUBSCRIBER_KEY", "")
    pnconfig.ssl = True
    pnconfig.user_id = get_pubnub_uuid()
    pubnub = PubNub(pnconfig)
    pubnub.add_listener(PrintListener())
    pubnub.subscribe().channels(channel_name).execute()
