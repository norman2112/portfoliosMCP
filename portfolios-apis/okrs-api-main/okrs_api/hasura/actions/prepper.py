"""Preps the input from Hasura to hand off to Hasura Actions."""
# pylint:disable=R0902
import json
from functools import wraps, partial
from http import HTTPStatus
import importlib
from inspect import signature

from inflection import camelize

from okrs_api.api.controller.helpers import is_pvadmin_connected_okrs
from okrs_api.hasura.actions.auth import (
    JWTParser,
)
from okrs_api import utils
from okrs_api.service_proxies.pvid import get_current_user
from okrs_api.utils import normalise

BASE_VALIDATION_PATH = "okrs_api.validators"
# The Portfolios version from which connected work OKRs is supported
PORTFOLIOS_SUPPORTED_VERSION_FOR_WORK = "2024.6.0"


def prep_input(controller_func=None, *, validators=None):
    """
    Decorate a controller function.

    Controllers for custom Hasura actions all have similar needs.
    This will construct an `input_prepper` and return it back to the`
    controller function as an argument, so it can be used in the controller code.

    This also allows for a `validators` list of names. The validator names
    correspond to module name in the `validators` directory. Validators all
    have a common structure and have a `validate` function which is called.

    param function controller_func: the controller function
    param [str] validators: a list of module names for validators to be run

    Example of partial application used in this decorator here:
    https://pybit.es/articles/decorator-optional-argument/
    """

    if controller_func is None:
        return partial(prep_input, validators=validators)

    @wraps(controller_func)
    async def wrapper_prep_input(*args, **kwargs):  # pylint: disable=too-many-branches
        request = _get_value_at_index(args, 0) or kwargs.get("request")
        body = _get_value_at_index(args, 1) or kwargs.get("body")
        input_prepper = prepper_factory(request, body)
        if input_prepper:
            print(
                f"api/{controller_func.__name__} "
                f"- admin_url: {input_prepper.planview_admin_url}"
                f" - planview_user_id: {input_prepper.planview_user_id}"
                f" - user_id: {input_prepper.user_id}"
                f" - tenant_group_id: {input_prepper.tenant_group_id}"
                f" - original_tenant_group_id: {input_prepper.tenant_group_id_original}"
            )
        if input_prepper.has_errors:
            return {
                "errors": input_prepper.serializable_errors
            }, input_prepper.error_status_code

        # Feature Toggle - Connected Apps
        feature_connected_apps = is_pvadmin_connected_okrs(input_prepper)
        if input_prepper.action_name == "connected_apps":
            feature_connected_apps = feature_connected_apps and bool(
                (input_prepper.input_parser.enabled is True)
                or (input_prepper.input_parser.enabled is None)
            )

        print("Feature connected apps - ", feature_connected_apps)

        # If any validators were specified, run them. If any fail, return an
        # (error, status code) tuple.
        if validators:
            for validator in validators:
                validator_cls = _get_validator_cls(validator)
                validator_instance = validator_cls(input_prepper=input_prepper)
                if not validator_instance.validate():
                    return (
                        {
                            "errors": validator_instance.serializable_errors,
                            "message": validator_instance.error_message,
                        },
                        HTTPStatus.UNPROCESSABLE_ENTITY,
                    )

        sig = signature(controller_func)
        all_args = {
            "db_session": input_prepper.db_session,
            "request": request,
            "body": body,
            "client_session": input_prepper.client_session,
            "app_settings": input_prepper.app_settings,
            "input_prepper": input_prepper,
            "applications": {},
        }
        parameters = sig.parameters

        if "applications" in parameters:
            if feature_connected_apps:
                all_supported_apps = ["leankit", "e1_prm"]
                api_response = await get_current_user(input_prepper)
                all_connected_apps = []
                for a in api_response["applications"]:
                    if a["appName"] in all_supported_apps:
                        all_connected_apps.append(a)

                apps = [a["appName"] for a in all_connected_apps]
                domain_info = [
                    {"app": a["appName"], "domain": normalise(a["url"])}
                    for a in all_connected_apps
                ]
                env_selectors = {
                    a["appName"]: a["envSelector"] for a in all_connected_apps
                }
                app_users = {
                    a["appName"]: a.get("tenantUserId", "") for a in all_connected_apps
                }
                for each_app in domain_info:
                    if each_app[
                        "app"
                    ] == "e1_prm" and await _verify_portfolios_version_for_work(
                        input_prepper
                    ):
                        domain_info.append(
                            {"app": "e1_work", "domain": each_app["domain"]}
                        )
                        apps.append("e1_work")
                        env_selectors["e1_work"] = env_selectors[each_app["app"]]
                        app_users["e1_work"] = app_users[each_app["app"]]
                        break

                applications = dict(
                    all_data=api_response,
                    apps=apps,
                    domain_info=domain_info,
                    domains={d["app"]: d["domain"] for d in domain_info},
                    env_selectors=env_selectors,
                    app_users=app_users,
                )

            else:
                apps = [input_prepper.app_name]
                domain_info = [
                    {"app": input_prepper.app_name, "domain": input_prepper.app_domain}
                ]

                if input_prepper.app_name == "e1_prm":
                    domain_info.append(
                        {"app": "e1_work", "domain": input_prepper.app_domain}
                    )

                    apps.append("e1_work")
                domains = {d["app"]: d["domain"] for d in domain_info}
                applications = dict(
                    all_apps={},
                    apps=apps,
                    domain_info=domain_info,
                    domains=domains,
                    env_selectors={},
                    app_users={},
                )
            all_args["applications"] = applications
            input_prepper.applications = applications

        passed_in_args = {
            called_arg: all_args.get(called_arg) for called_arg in parameters
        }

        return await controller_func(**passed_in_args)

    return wrapper_prep_input


def prepper_factory(request, body):
    """
    Create an input prepper from the request and body objects.

    The Prepper can perform a sanity check on the input and return errors back
    to the client quickly.

    This prepper factory creates a custom input prepper that uses many
    collaborator objects to help it to validate and organize the incoming
    input data.

    :param WebRequest request: the request itself
    :param dict body: the request body
    """
    action_name = body.get("action", {}).get("name")
    input_data = body.get("input", {})

    jwt_parser = JWTParser(request_headers=request.headers)
    db_session = request.app.get("db_session")
    input_parser = utils.Map(**input_data)
    prepper = InputPrepper(
        input_parser=input_parser,
        jwt_parser=jwt_parser,
        db_session=db_session,
        client_session=request.app.get("client_session"),
        app_settings=request.config_dict.get("settings"),
        action_name=action_name,
    )
    prepper.validate_jwt()
    return prepper


class InputPrepper:
    """
    Takes in a JWTParser and an input parser.

    Validates the JWT and adds any special input validations that were not
    taken care of by the Hasura GraphQL schema or the openapi.yml spec.
    """

    DEFAULT_ERROR_STATUS_CODE = HTTPStatus.UNPROCESSABLE_ENTITY

    # pylint:disable=R0913
    def __init__(
        self,
        input_parser,
        jwt_parser,
        db_session,
        client_session,
        app_settings,
        action_name,
        applications=None,
    ):
        """
        Initialize the InputPrepper.

        :param InputParser input_parser:
        :param JWTParser jwt_parser:
        :param session db_session:
        :param session client_session:
        :param dict app_settings:
        :param str action_name: the name of the controller action
        :param [str] validators: list of names of validators to validate against
        """
        self.__applications = applications
        self.input_parser = input_parser
        self.jwt_parser = jwt_parser
        self.db_session = db_session
        self.client_session = client_session
        self.app_settings = app_settings
        self.action_name = action_name
        # To be filled in on validation
        self.errors = []
        self.error_status_code = None
        self.input_parser.domain = self.app_domain
        self.domains = {}

    def validate_jwt(self):
        """Validate the JWT is correct."""
        if self.jwt_parser.validate():
            return True

        self._add_errors(self.jwt_parser.errors, HTTPStatus.UNAUTHORIZED)
        return False

    @property
    def serializable_errors(self):
        """Return the errors as dict objects for serialization."""
        return [error.to_dict() for error in self.errors]

    @property
    def has_errors(self):
        """Return true if any errors exist."""
        return bool(self.errors)

    @property
    def user_id(self):
        """Return the user id for the product_type we're querying."""
        return self.jwt_parser.user_id

    @property
    def planview_user_id(self):
        """Return the planview user if for the current user."""
        return self.jwt_parser.planview_user_id

    @property
    def org_id(self):
        """Return the Hasura Org Id from the JWT."""
        return self.jwt_parser.hasura_org_id

    @property
    def tenant_group_id(self):
        """Return the Hasura Tenant Group Id from the JWT."""
        return self.jwt_parser.hasura_tenant_group_id

    @property
    def tenant_group_id_original(self):
        """Return the original tenant group id."""
        return self.jwt_parser.hasura_tenant_group_id_original

    @property
    def org_id_original(self):
        """Return the original org id."""
        return self.jwt_parser.hasura_org_id_original

    @property
    def app_tenant_id_original(self):
        """Return the original app tenant id."""
        return self.jwt_parser.hasura_app_tenant_id_original

    @property
    def app_name(self):
        """Return the App Name."""
        return self.jwt_parser.hasura_app_name

    @property
    def app_domain(self):
        """Return the App Domain."""
        return self.jwt_parser.app_domain

    @property
    def hasura_jwt(self):
        """Return the Hasura JWT passed to this API."""
        return self.jwt_parser.hasura_jwt

    @property
    def planview_admin_url(self):
        """Return planview admin url if present in JWT token."""
        return self.jwt_parser.planview_admin_url

    def _add_errors(self, new_errors, status_code=None):
        """Add errors. Change the error status code."""
        self.error_status_code = status_code or self.DEFAULT_ERROR_STATUS_CODE
        if new_errors:
            self.errors = self.errors + new_errors

    def clone(self):
        """Return a clone of the current object without changing common properties."""
        return InputPrepper(
            input_parser=utils.Map(**self.input_parser),
            jwt_parser=self.jwt_parser,
            db_session=self.db_session,
            client_session=self.client_session,
            app_settings=self.app_settings,
            action_name=self.action_name,
            applications=self.applications,
        )

    @property
    def applications(self):
        """Set applications for this user."""
        return self.__applications

    @applications.setter
    def applications(self, apps):
        """Set applications for this user."""
        self.__applications = apps

    def __str__(self):
        """Make a printable input prepper."""

        s = json.dumps(
            dict(
                input_parser=self.input_parser,
                jwt=dict(
                    token=self.jwt_parser.hasura_jwt,
                    tenant_id=self.jwt_parser.hasura_org_id,
                    tenant_group_id=self.jwt_parser.hasura_tenant_group_id,
                    tenant_group_id_orig=self.jwt_parser.hasura_tenant_group_id_original,
                    app_name=self.jwt_parser.hasura_app_name,
                    user_id=self.jwt_parser.user_id,
                    planview_user_id=self.jwt_parser.planview_user_id,
                ),
            )
        )

        return s

    def __repr__(self):
        """Return a stringified version of prepper."""

        return self.__str__()


def _get_validator_cls(module_name):
    """Return the validator class or an error."""
    full_module_path = f"{BASE_VALIDATION_PATH}.{module_name}"
    module = importlib.import_module(full_module_path)
    validator_cls_name = f"{camelize(module_name)}Validator"
    return getattr(module, validator_cls_name)


def _get_value_at_index(iterable, index):
    """
    Return a value at an index of an iterable.

    Do not error out if index is out of range; simply return None.

    param iterable iterable: any iterable
    param index: the index at that iterable
    """
    if 0 <= index < len(iterable):
        return iterable[index]

    return None


async def _verify_portfolios_version_for_work(input_prepper):
    """
    Return the comparison of Portfolios version with expected.

    version for connected work support.
    """
    all_supported_apps = ["leankit", "e1_prm"]
    api_response = await get_current_user(input_prepper)
    current_portfolios_version = None
    for a in api_response["applications"]:
        if a["appName"] in all_supported_apps:
            if a["appName"] == "e1_prm":
                current_portfolios_version = a["softwareVersion"]
    if not current_portfolios_version:
        return None
    # Split the version strings into components and convert them to integers
    current_version = [int(x) for x in current_portfolios_version.split(".")]
    supported_version = [
        int(x) for x in PORTFOLIOS_SUPPORTED_VERSION_FOR_WORK.split(".")
    ]

    # Compare version
    for v1, v2 in zip(current_version, supported_version):
        if v1 > v2:
            return True
        if v1 < v2:
            return False

    # If all components are equal
    return True
