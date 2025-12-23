"""Adapters for converting responses into a conforming data structure."""
# pylint:disable=R0903, W0613


def errors(response_data, custom_errors=None, reason=None):
    """Return adapted errors for errors returned from PRM."""
    error_messages = custom_errors or []
    api_error_message = response_data.get("message")
    if api_error_message:
        error_messages.append(api_error_message)
    return {"errors": error_messages, "reason": reason}


EXTERNAL_TYPE = "e1_prm"
CONTAINER_TYPE = "e1_strategy"


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
        return ProjectListAdapter(self.response_data, self.input_prepper).adapt()

    def search_activity_containers(self):
        """Return adapted data for the `search_activity_containers` action."""
        return StrategyListAdapter(self.response_data, self.input_prepper).adapt()

    def list_activities(self):
        """Return adapted data for the `list_activities` action."""
        return ProjectListAdapter(self.response_data, self.input_prepper).adapt()

    def list_activity_containers(self):
        """Return adapted data for the `list_activity_containers` action."""
        return StrategyListAdapter(self.response_data, self.input_prepper).adapt()

    def create_activity(self):
        """Return adapted data for the `create_activity` action."""
        raise ValueError("This operation is not supported")

    def current_user(self):
        """Adapt the PRM user response to the data we want."""

        apps = self.input_prepper.applications["all_data"]
        current_user = dict(
            email_address=apps["email"],
            first_name=apps["firstName"],
            last_name=apps["lastName"],
        )

        return UserInfoAdapter(
            response_data=self.response_data,
            context_ids=self.input_prepper.input_parser.context_ids,
            available_work_item_containers=self.adapter_kwargs[
                "available_work_item_containers"
            ],
            user_id=self.input_prepper.user_id,
            planview_user_id=self.input_prepper.planview_user_id,
            current_user=current_user,
        ).adapt()

    def list_activity_types(self):
        """Return adapted data for the `list_activity_types` action."""
        raise ValueError("This operation is not supported")

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


class StrategyListAdapter(BaseAdapter):
    """Adapt and convert a list of boards to a set of WorkItemContainer attribs."""

    def __init__(self, response_data, input_prepper):
        """Initialize with input prepper."""
        super().__init__(response_data)
        self.input_prepper = input_prepper

    @property
    def strategies(self):
        """Return the `strategy` data in the response dict."""
        return self.response_data.get("Entities", [])

    @property
    def no_access_stretegies(self):
        """Return the `no access strategy` data in the response dict."""
        return self.response_data.get("NoAccessEntities", [])

    @property
    def missing_strategies(self):
        """Return the `missing strategy` data in the response dict."""
        return self.response_data.get("MissingEntities", [])

    def adapt(self):
        """Adapt all strategies (accessible and inaccessible) to WorkItemContainer attribs."""
        with_access = [
            StrategyToWorkItemContainerAdapter(strategy).adapt()
            for strategy in self.strategies
        ]

        without_access = []
        if not self.input_prepper.input_parser.exclude_no_access:
            without_access = [
                StrategyToWorkItemContainerAdapter(strategy).adapt()
                for strategy in self.no_access_stretegies
            ]

        missing_data = []
        if not self.input_prepper.input_parser.exclude_no_access:
            missing_data = [
                StrategyToWorkItemContainerAdapter(strategy).adapt()
                for strategy in self.missing_strategies
            ]

        return with_access + without_access + missing_data


class ProjectListAdapter(BaseAdapter):
    """Adapt and convert a project list response to a set of work item attribs."""

    def __init__(self, response_data, input_prepper):
        """Initialize with input_prepper."""
        super().__init__(response_data)
        self.input_prepper = input_prepper

    @property
    def projects(self):
        """Return the `strategy` data in the response dict."""
        return self.response_data["project_details"].get("Entities", [])

    @property
    def no_access_projects(self):
        """Return the `no access strategy` data in the response dict."""
        return self.response_data["project_details"].get("NoAccessEntities", [])

    def adapt(self):
        """Adapt all cards data into work item-friendly dicts."""
        output = []

        strategy = self.response_data.get("strategy_details", {})

        with_access = self.projects
        for project in with_access:
            full_data = {"project_details": project, "strategy_details": strategy}
            output.append(ProjectToWorkItemAdapter(full_data).adapt())

        if not self.input_prepper.input_parser.exclude_no_access:
            for project_list in [self.no_access_projects]:
                for project in project_list:
                    full_data = {
                        "project_details": project,
                        "strategy_details": strategy,
                    }
                    output.append(
                        ProjectToWorkItemAdapter(full_data, inaccessible=True).adapt()
                    )
        return output


class ProjectToWorkItemAdapter(BaseAdapter):
    """Adapter for a single PRM Card."""

    STATUS_MAP = {
        "not_started": ["request"],
        "finished": ["complete", "cancel", "denied"],
    }

    def __init__(self, response_data, inaccessible=False):
        """Initialize a project to work item adapter."""
        super().__init__(response_data)
        self.inaccessible = inaccessible

    def adapt(self):
        """Convert a card attribute to a set of WorkItem attributes."""
        return {
            "title": self._project_details.get("Description")
            if not self.inaccessible
            else None,
            "external_type": EXTERNAL_TYPE,
            "container_type": CONTAINER_TYPE,
            "external_id": self._project_details.get("StructureCode")
            if not self.inaccessible
            else self._project_details,
            "item_type": self.get_project_type(),
            "state": self.get_project_status(),
            "planned_start": self._project_details.get("ScheduleStart")
            if not self.inaccessible
            else None,
            "planned_finish": self._project_details.get("ScheduleFinish")
            if not self.inaccessible
            else None,
        }

    @property
    def _project_details(self):
        """Return the project details data from E1."""
        return self.response_data.get("project_details", {})

    @property
    def _strategy_details(self):
        """Return the strategy details data from E1."""
        return self.response_data.get("strategy_details", {})

    def get_project_status(self):
        """Return project status mapped to OKR state."""
        if self.inaccessible:
            return None

        project_status = self._project_details["Status"]["Description"]

        for okr_state in self.STATUS_MAP:
            prm_statuses = self.STATUS_MAP[okr_state]
            matched = any([x in project_status.lower() for x in prm_statuses])
            if matched:
                return okr_state

        if project_status:
            return "in_progress"

        return None

    def get_project_type(self):
        """Return the project type."""
        if self.inaccessible or (not self._project_details):
            return ""
        try:
            project_type = self._project_details["Attributes"]["ExecType"][
                "Description"
            ]
            return project_type
        except BaseException:
            return ""


class StrategyToWorkItemContainerAdapter(BaseAdapter):
    """Adapter for a single PRM strategy."""

    def adapt(self):
        """Convert a card attribute to a set of WorkItem attributes."""
        if isinstance(self.response_data, dict):
            return {
                "title": self.response_data.get("Description"),
                "external_type": EXTERNAL_TYPE,
                "app_name": EXTERNAL_TYPE,
                "external_id": self.response_data.get("StructureCode"),
            }

        return {
            "title": None,
            "external_type": EXTERNAL_TYPE,
            "external_id": self.response_data,
        }


class UsersAdapter(BaseAdapter):
    """Adapt PRM Users into Platforma usable users."""

    def adapt(self):
        """Return an array of users."""
        return [
            {
                "id": str(user["UserId"]),
                "first_name": user["FullName"],
                "last_name": "",
                "email_address": user["Email"],
                "role": "user",
                "administrator": False,
            }
            for user in self.response_data
            if user.get("Email")
        ]


class UserInfoAdapter(BaseAdapter):
    """Adapter for a single user's info."""

    def __init__(self, *args, **kwargs):
        """
        Initialize additional params for the UserInfoAdapter.

        :param str org_id: the hasura org id
        :param list context_ids: the list of context ids to limit the roles
        returned. If this is blank, then roles for all available wics are
        returned.
        """
        super().__init__(response_data=kwargs["response_data"])
        self.context_ids = kwargs.get("context_ids") or []
        self.available_work_item_containers = (
            kwargs.get("available_work_item_containers") or []
        )
        self.user_id = kwargs.get("user_id", "")
        self.planview_user_id = kwargs.get("planview_user_id", "")
        self.strategies = self.response_data.get("strategies_info", {}).get(
            "Entities", []
        )
        self.current_user = kwargs.get("current_user", {})

    def adapt(self):
        """Convert PRM user data into standardized data."""
        current_user = self.current_user
        current_user["id"] = self.user_id
        current_user[
            "work_item_container_roles"
        ] = self._adapted_work_item_container_roles()

        return current_user

    def _find_user(self, strategy_users):
        matching_users = [
            user for user in strategy_users if user["UserId"] == self.user_id
        ]
        if not matching_users:
            return {}
        return matching_users[0]

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
        """Find matching role."""
        for strategy in self.strategies:
            if strategy.get("StructureCode") == context_id:
                return {
                    "context_id": context_id,
                    "role": strategy.get("Attributes", {}).get("AccessLevel"),
                }

        return None

    def _make_role_data(self, context_id):
        """Make role column."""
        role_data = self._find_role(context_id)
        if role_data:
            return {
                "context_id": role_data.get("context_id"),
                "okr_role": self._translated_role(role_data["role"]),
                "app_role": role_data["role"],
            }

        return {
            "context_id": context_id,
            "okr_role": "none",
            "app_role": "noAccess",
        }

    def _translated_role(self, role):
        """Translate role permissions from a E1 role."""
        okr_role = "none"

        if role == 1:
            okr_role = "read"
        elif role == 2:
            okr_role = "edit"
        elif role >= 3:
            okr_role = "manage"

        return okr_role
