"""Adapters for converting responses into a conforming data structure."""
# pylint:disable=R0903, W0613

from okrs_api.model_helpers.common import clean_wi_and_kr_wi_mapping


def errors(response_data, custom_errors=None, reason=None):
    """Return adapted errors for errors returned from Leankit."""
    error_messages = custom_errors or []
    api_error_message = response_data.get("message")
    if api_error_message:
        error_messages.append(api_error_message)
    return {"errors": error_messages, "reason": reason}


EXTERNAL_TYPE = "leankit"
CONTAINER_TYPE = "lk_board"


class AdapterLauncher:
    """Call the appropriate function, based on the request action."""

    def __init__(self, response_data, input_prepper=None, adapter_kwargs=None):
        """
        Initialize the launcher.

        :param dict response_data: the data of the response
        :param InputPrepper input_prepper: the input prepper for the request
        :param dict adapter_kwargs: additional kwargs that the adapter func
        can use.
        """
        self.response_data = response_data
        self.input_prepper = input_prepper
        self.adapter_kwargs = adapter_kwargs

    def search_activities(self):
        """Return adapted data for the `search_activities` action."""
        return CardListAdapter(self.response_data).adapt()

    def list_activities(self):
        """Return adapted data for the `list_activities` action."""
        return CardListWithAccessAdapter(self.response_data, self.input_prepper).adapt()

    def search_activity_containers(self):
        """Return adapted data for the `search_activity_containers` action."""
        return BoardListAdapter(self.response_data).adapt()

    def list_activity_containers(self):
        """Return adapted data for the `list_activity_containers` action."""
        return BoardListWithAccessAdapter(
            self.response_data, self.input_prepper
        ).adapt()

    def create_activity(self):
        """Return adapted data for the `create_activity` action."""
        return CardToWorkItemAdapter(self.response_data).adapt()

    def current_user(self):
        """Adapt the Leankit user response to the data we want."""
        return UserInfoAdapter(
            response_data=self.response_data,
            org_id=self.input_prepper.org_id,
            context_ids=self.input_prepper.input_parser.context_ids,
            available_work_item_containers=self.adapter_kwargs[
                "available_work_item_containers"
            ],
        ).adapt()

    def list_activity_types(self):
        """Return adapted data for the `list_activity_types` action."""
        return ActivityTypesAdapter(self.response_data).adapt()

    def search_users(self):
        """Return adapted data for the `list_users` action."""
        return UsersAdapter(self.response_data).adapt()


# The collaborator classes for the callable adapter functions.


class BaseAdapter:
    """Base Adapter for all adapters."""

    def __init__(self, response_data):
        """
        Initialize data from the external api response.

        :param dict data: the incoming data to be adapted
        """
        self.response_data = response_data or {}


class ActivityTypesAdapter(BaseAdapter):
    """
    Adapt a Leankit Activity List response into a list of activity_types.

    More info here:
    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/list
    """

    def adapt(self):
        """
        Return an array of card types.

        Types will be in the format of::

            {
                "id": "<the leankit id of the card type>",
                "name": "<the name of the card type>"
            }
        """
        return [
            {"id": card_type["id"], "name": card_type["name"]}
            for card_type in self._card_types_data
            if card_type["isCardType"]
        ]

    @property
    def _card_types_data(self):
        """Return the `cardTypes` data in the response dict."""
        return self.response_data.get("cardTypes", [])


class BoardListAdapter(BaseAdapter):
    """
    Adapt and convert a list of boards to a set of WorkItemContainer attribs.

    More info here:
    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/list
    """

    def adapt(self):
        """Adapt all boards data into WorkItemContainer-friendly dicts."""
        return [
            BoardToWorkItemContainerAdapter(board).adapt() for board in self.boards_data
        ]

    @property
    def boards_data(self):
        """Return the `boards` data in the response dict."""
        return self.response_data.get("boards", [])


class BoardListWithAccessAdapter(BoardListAdapter):
    """
    Adapt and convert a list of boards to a set of WorkItemContainer attribs.

    More info here:
    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/list
    """

    def __init__(self, response_data, input_prepper):
        """Initialize with input prepper."""
        super().__init__(response_data)
        self.input_prepper = input_prepper

    def adapt(self):
        """Adapt all boards (accessible and inaccessible) to WorkItemContainer attribs."""
        boards_with_access = [
            BoardToWorkItemContainerAdapter(board).adapt() for board in self.boards_data
        ]

        boards_without_access = []
        if not self.input_prepper.input_parser.exclude_no_access:
            boards_without_access = [
                BoardToWorkItemContainerAdapter(board).adapt()
                for board in self.inaccessible_boards_data
            ]

        return boards_with_access + boards_without_access

    @property
    def inaccessible_boards_data(self):
        """Retun the `boards` without access."""
        return self.response_data.get("inaccessibleBoards", [])


class CardListWithAccessAdapter(BaseAdapter):
    """
    Adapt and convert a cards list response to a set of work item attribs.

    More info here:
    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/card/list
    """

    def __init__(self, response_data, input_prepper):
        """Initialize with input_prepper."""
        super().__init__(response_data)
        self.input_prepper = input_prepper

    def adapt(self):
        """
        Adapt all cards data into work item-friendly dicts.

        The `self.response_data` should come in the form of::

          {
            "card_list": [<lk card details>]
          }

        This will take the data and put it back together in a format that the
        `CardToWorkItemAdapter` can use.
        """
        output = []
        card_list = self.response_data["card_list"]["cards"]
        deleted_cards = []
        for card in card_list:
            full_data = {"card_details": card, "board_details": card.get("board", {})}
            output.append(CardToWorkItemWithAccessAdapter(full_data).adapt())

        if not self.input_prepper.input_parser.exclude_no_access:
            card_list = self.response_data["card_list"].get("inaccessibleCards", [])
            for card in card_list:
                if not card.get("isDeleted", False) is True:
                    full_data = {
                        "card_details": card,
                        "board_details": card.get("board", {}),
                    }
                    output.append(CardToWorkItemWithAccessAdapter(full_data).adapt())
                else:
                    deleted_cards.append(card["id"])
        if deleted_cards:
            clean_wi_and_kr_wi_mapping(self.input_prepper, deleted_cards)
        return output


class CardListAdapter(BaseAdapter):
    """
    Adapt and convert a cards list response to a set of work item attribs.

    More info here:
    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/card/list
    """

    def adapt(self):
        """
        Adapt all cards data into work item-friendly dicts.

        The `self.response_data` should come in the form of::

          {
            "board_details": <lk board details>,
            "card_list": [<lk card details>]
          }

        This will take the data and put it back together in a format that the
        `CardToWorkItemAdapter` can use.
        """
        output = []
        board = self.response_data["board_details"]
        card_list = self.response_data["card_list"]["cards"]

        for card in card_list:
            full_data = {"board_details": board, "card_details": card}
            output.append(CardToWorkItemAdapter(full_data).adapt())

        return output


class CardToWorkItemAdapter(BaseAdapter):
    """
    Adapter for a single LeanKit Card.

    self.response_data should be in the form of::

      {
        "board_details: <leankit board details>,
        "card_details": <leankit card details>
      }

    """

    CARD_STATUSES = {
        "notStarted": "not_started",
        "started": "in_progress",
        "finished": "finished",
    }

    def adapt(self):
        """Convert a card attribute to a set of WorkItem attributes."""
        return {
            "title": self._card_details.get("title"),
            "external_type": "leankit",
            "container_type": CONTAINER_TYPE,
            "external_id": self._card_details.get("id"),
            "item_type": self._card_type,
            "state": self._card_status(),
            "planned_start": self._card_details.get("plannedStart"),
            "planned_finish": self._card_details.get("plannedFinish"),
        }

    @property
    def _card_type(self):
        type_obj = self._card_details.get("type")
        if not type_obj:
            return None
        return type_obj.get("title")

    @property
    def _card_details(self):
        """Return the leankit card details data from leankit."""
        return self.response_data.get("card_details", {})

    @property
    def _board_details(self):
        """Return the leankit board details data from leankit."""
        return self.response_data.get("board_details", {})

    @property
    def _actual_finish(self):
        return self.response_data.get("actualFinish")

    @property
    def _actual_start(self):
        return self.response_data.get("actualStart")

    def _board_lanes(self):
        """Return all the lanes for the board."""
        return self._board_details.get("lanes")

    def _current_card_lane(self):
        """Return the current card lane for the board."""
        card_lane_id = self._card_details["lane"]["id"]
        for lane in self._board_lanes():
            if str(lane["id"]) == str(card_lane_id):
                return lane

        return None

    def _card_status(self):
        """Return the card status for this card."""
        current_lane = self._current_card_lane()
        if not current_lane:
            return None
        return self.CARD_STATUSES[current_lane["cardStatus"]]


class CardToWorkItemWithAccessAdapter(CardToWorkItemAdapter):
    """Adapt specifically for card list API."""

    def _current_card_lane(self):
        return self._card_details.get("lane")


class BoardToWorkItemContainerAdapter(BaseAdapter):
    """Adapter for a single LeanKit Board."""

    def adapt(self):
        """Convert a card attribute to a set of WorkItem attributes."""
        return {
            "title": self.response_data.get("title"),
            "external_type": EXTERNAL_TYPE,
            "app_name": EXTERNAL_TYPE,
            "external_id": self.response_data.get("id"),
        }


class UsersAdapter(BaseAdapter):
    """
    Adapt Leankit Users into Platforma usable users.

    More info here:
    https://success.planview.com/Planview_LeanKit/LeanKit_API/01_v2/board/user-roles
    """

    def adapt(self):
        """
        Return an array of users.

        Users will be in the format of::

            {
                "id": <the leankit id of the user>,
                "first_name": <the first name of the user>,
                "last_name": <the last name of the user>,
                "email_address": <the email address of the user>,
                "role": <the role of the user>,
                "administrator": <boolean value if user is an admin of this board>
            }
        """
        return [
            {
                "id": str(user["userId"]),
                "first_name": user["firstName"],
                "last_name": user["lastName"],
                "email_address": user["emailAddress"],
                "role": user["role"]["label"],
                "administrator": user["administrator"],
            }
            for user in self._board_users_data
        ]

    @property
    def _board_users_data(self):
        """Return the `boardUsers` data in the response dict."""
        return self.response_data.get("boardUsers", [])


class UserInfoAdapter(BaseAdapter):
    """
    Adapter for a single user's info.

    Will return all the board roles that have existing WorkItemContainers. The
    format is as follows::

        {
            id,
            first_name,
            last_name,
            email_address,
            work_item_containers: [{ context_id, okr_role, app_role }]
        }

    """

    ROLE_MAPPINGS = {
        "boardReader": "read",
        "boardUser": "edit",
        "boardManager": "manage",
        "boardAdministrator": "manage",
        "boardCreator": "manage",
    }

    def __init__(self, *args, **kwargs):
        """
        Initialize additional params for the UserInfoAdapter.

        :param str org_id: the hasura org id
        :param list context_ids: the list of context ids to limit the roles
        returned. If this is blank, then roles for all available wics are
        returned.
        """
        super().__init__(response_data=kwargs["response_data"])
        self.org_id = kwargs["org_id"]
        self.context_ids = kwargs.get("context_ids") or []
        self.available_work_item_containers = (
            kwargs.get("available_work_item_containers") or []
        )

    def adapt(self):
        """Convert leankit user data into standardized data."""
        return {
            "id": self.response_data.get("id"),
            "first_name": self.response_data.get("firstName"),
            "last_name": self.response_data.get("lastName"),
            "email_address": self.response_data.get("emailAddress"),
            "work_item_container_roles": self._adapted_work_item_container_roles(),
        }

    def _adapted_work_item_container_roles(self):
        """
        Adapt wic roles into a format of our choosing.

        ```
        [{context_id, okr_role, app_role}]
        ```
        """
        # Merge sets (unique) together of wic.external_ids and context_ids
        available_context_ids = list(
            set(self.context_ids)
            | {wic.external_id for wic in self.available_work_item_containers}
        )
        return [
            self._make_role_data(context_id) for context_id in available_context_ids
        ]

    def _find_role(self, context_id):
        board_roles = self.response_data.get("boardRoles", [])
        for board_role in board_roles:
            if board_role.get("boardId") == context_id:
                return board_role

        return None

    def _make_role_data(self, context_id):
        role_data = self._find_role(context_id)
        if role_data:
            return {
                "context_id": role_data.get("boardId"),
                "okr_role": self._translated_role(role_data["role"]),
                "app_role": role_data["role"]["key"],
            }

        return {
            "context_id": context_id,
            "okr_role": "none",
            "app_role": "noAccess",
        }

    def _translated_role(self, role_permissions):
        """Translate role permissions from a Leankit role."""
        return self.ROLE_MAPPINGS.get(role_permissions["key"])
