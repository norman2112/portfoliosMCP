"""Define the actions controller."""
import asyncio
import time
from http import HTTPStatus
import json
from connexion import NoContent
from open_alchemy import models
from sqlalchemy import or_, and_
from okrs_api import utils
from okrs_api.api.controller.helpers import (
    sanitise_product_type,
    is_pvadmin_connected_okrs,
    get_app_name_for_product_type,
    get_container_type_for_product_type,
    get_product_type,
    get_product_types,
    get_container_type,
    get_product_types_for_connected_app,
    get_product_type_for_connected_app,
    get_context_id,
)
from okrs_api.api.managers.list_activity_containers import (
    ListActivitityContainersManager,
)
from okrs_api.api.managers.work_item_containers import WorkItemContainersManager
from okrs_api.hasura.actions.prepper import (
    prep_input,
    _verify_portfolios_version_for_work,
)
from okrs_api.api.controller.error_helpers import (
    bad_request_error,
    internal_server_error,
)
from okrs_api.hasura.actions.service_wranglers import service_wrangler_factory
from okrs_api.model_helpers.activity_logger import DeletionLogger
from okrs_api.model_helpers.ca_configs import (
    create_default_configurations,
    ca_configs_response_adapter,
    remove_default_configurations,
    fetch_all_configurations,
    DEFAULT_FIELDS_NUM,
    MAX_ACTIVE_CA_FIELD,
    add_ca_option_ids,
    create_new_configuration,
    validate_configuration,
    adapt_error_for_hasura,
    fetch_configuration,
    validate_update_configuration,
    update_configuration,
    ca_config_response_adapter,
    fetch_all_active_configurations,
)
from okrs_api.model_helpers.ca_settings import (
    create_new_custom_attributes_settings,
    CUSTOM_ATTRIBUTES_DB_FIELDS,
    get_existing_custom_attributes_settings,
)
from okrs_api.model_helpers.ca_values import (
    fetch_custom_attributes,
    ca_values_response_adapter,
    get_okr_role_for_object,
    create_new_ca_value,
    get_wic_role,
    validate_and_fix_ca_values,
    update_ca_values,
)
from okrs_api.model_helpers.objectives import (
    create_new_objective,
    fetch_objective,
    MODIFIABLE_DB_FIELDS,
    validate_app_owned_by,
    validate_and_format_dates,
)
from okrs_api.model_helpers.key_results import (
    create_new_keyresult,
    fetch_key_result,
    KEYRESULT_DB_FIELDS,
    validate_objective_and_update_kr_daterange,
)

from okrs_api.model_helpers.history import fetch_history
from okrs_api.model_helpers.common import dictify_model, commit_db_session
from okrs_api.model_helpers.activity_mappings import ActivitiesConnectionCreator
from okrs_api.model_helpers.deleter import Deleter
from okrs_api.model_helpers.levels import relevel_after_deletion, relevel_after_insert
from okrs_api.model_helpers.objectives import (
    list_container_objectives,
)
from okrs_api.model_helpers.settings import SettingsManager
from okrs_api.model_helpers.targets import (
    validate_targets,
    validate_input_and_generate_targets,
)
from okrs_api.model_helpers.work_items import WorkItemCreator
from okrs_api.model_helpers.work_item_container_roles import (
    WorkItemContainerRoleBuilder,
)
from okrs_api.pubnub.utils import (
    get_container_channel_name,
    get_user_channel_name,
    get_tenant_channel_name,
    get_subscriber_key,
    get_pubnub_uuid,
)
from okrs_api.service_proxies.pvid import (
    add_pvid_to_response_data,
    add_pvid_user_details_to_response_data,
)
from okrs_api.validators.errors import ValidationError
from okrs_api.validators.level_config import (
    LevelConfigDeletionValidator,
    LevelConfigInsertValidator,
)
from okrs_api.api.managers.activity_logs import (
    KeyResultsActivityLogs,
    ObjectivesActivityLogs,
)
from okrs_api.api.managers.activities_okrs import ActivityOKRManager
from okrs_api.api.managers.key_result_targets import KeyResultTargetsManager
from okrs_api.api.managers.objectives import ObjectivesManager
from okrs_api.api.managers.key_results import KeyResultsManager
from okrs_api.api.managers.progress_points import ProgressPointsManager
from okrs_api.api.managers.current_user import CurrentUserManager
from okrs_api.api.managers.user_settings import UserSettingsManager
from okrs_api.api.managers.multi_level_okrs import (
    MultiLevelOKRManager,
    MultiLevelOKRListsManager,
)
from okrs_api.pubnub.utils import send_pubnub_event_for_user

# pylint:disable=W0613,C0302,R0911

STDOUT_LOG_API = False


def log_api(api, *args, **kargs):
    """Log the arguments to stdout if it is enabled."""

    if STDOUT_LOG_API:
        print(f"++++++ API LOG {api} ++++++")
        print(args)
        print(kargs)
        print(f"------ API LOG {api} ------")


async def hello_world():
    """Return a simple Hello World endpoint that can be used for testing."""
    return {"greeting": "hello world"}, HTTPStatus.OK


@prep_input
async def create_activity(request, body, input_prepper):  # pylint:disable=W0613
    """
    Define the create activity operation.

    Responsible for:
    1. Parsing the incoming JWT and authentication the user
    2. Passing the request data to the proper Service Wrangler
    3. Returning the formatted return results from the newly created work item
    """
    wrangler = service_wrangler_factory(input_prepper)
    response_data, response_status = await wrangler.call_service()

    with input_prepper.db_session() as db_session:
        if wrangler.action_was_successful:
            product_type = get_product_type(input_prepper)
            container_type = get_container_type_for_product_type(product_type)

            attribs = response_data | {
                "tenant_id_str": input_prepper.org_id,
                "tenant_group_id_str": input_prepper.tenant_group_id,
                "created_by": input_prepper.planview_user_id,
                "app_created_by": input_prepper.user_id,
                "app_name": input_prepper.app_name,
                "container_type": container_type,
            }

            creator = WorkItemCreator(
                work_item_attribs=attribs,
                input_parser=input_prepper.input_parser,
                db_session=db_session,
            )
            work_item = creator.create()
            response_data = dictify_model(
                work_item,
                [
                    "id",
                    "title",
                    "item_type",
                    "external_type",
                    "external_id",
                    "state",
                    "planned_start",
                    "planned_finish",
                ],
            )
    return response_data, response_status


@prep_input
async def connect_activities(request, body, input_prepper):
    """Define the connect activity operation."""
    with input_prepper.db_session() as db_session:
        key_result = db_session.query(models.KeyResult).get(
            input_prepper.input_parser.key_result_id
        )
        if not key_result:
            print("Cannot find a key result for it")
            return NoContent, HTTPStatus.BAD_REQUEST

        if key_result.objective.work_item_container.app_name != input_prepper.app_name:
            print("Cannot add cross app activities yet")
            return NoContent, HTTPStatus.BAD_REQUEST
        kwargs = {
            "app_name": input_prepper.app_name,
            "is_pvadmin": is_pvadmin_connected_okrs(input_prepper),
        }
        connector = ActivitiesConnectionCreator(
            db_session=db_session,
            input_parser=input_prepper.input_parser,
            org_id=input_prepper.org_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            user_id=input_prepper.user_id,
            **kwargs,
        )
        mappings = connector.connect()
        mappings_as_attribs = [
            dictify_model(mapping, ["id", "key_result_id", "work_item_id"])
            for mapping in mappings
        ]

    return mappings_as_attribs, HTTPStatus.OK


# TODO: When merging with work update this method to filter out by container_type
@prep_input
async def list_activity_containers_v2(request, body, input_prepper, applications):
    """Define list activity containers action without calling external systems."""
    # just goto db and give the response back same as list_activity_containers
    input_product_types = get_product_types(input_prepper) or []
    product_types = [sanitise_product_type(p) for p in input_product_types]

    apps = applications["apps"]
    # Now take the unique ones only
    product_types = list(set(product_types))
    product_types = get_product_types_for_connected_app(product_types)
    product_types = [p for p in product_types if p in apps]
    if not product_types:
        product_types = applications["apps"]
    lacm = ListActivitityContainersManager(input_prepper)
    containers = lacm.get_work_item_container(product_types)
    return containers, HTTPStatus.OK


@prep_input
async def basic_current_user(request, body, input_prepper, applications):
    """Return only current users info."""

    context_ids = input_prepper.input_parser.context_ids or []
    domains = applications["domains"]
    response_data, response_status = await basic_current_user_for_product_type(
        request,
        body,
        input_prepper.clone(),
        domains,
        applications if is_pvadmin_connected_okrs(input_prepper) else None,
        context_ids,
    )
    roles = response_data.get("work_item_container_roles", [])
    if not roles or roles[0].get("okr_role") == "none":
        return bad_request_error(
            "User does not have access to this work item container", "CANNOT_FETCH_OKRS"
        )
    return response_data, response_status


async def basic_current_user_for_product_type(
    request,
    body,
    input_prepper,
    domain=None,
    applications=None,
    context_ids=None,
):
    """
    Retrieve info for the supplied user.

    Convert the [board] roles into generalized WIC roles.
    Also store these WorkItemContainerRoles in the database as a sort of cache.

    Return the following data::

        {
            id,
            first_name,
            last_name,
            email_address,
            work_item_containers: [{ context_id, okr_role, app_role }]
        }

    """
    with input_prepper.db_session() as db_session:
        available_work_item_containers = CurrentUserManager(input_prepper).get_wics(
            context_ids, db_session
        )
        if not available_work_item_containers:
            return {}, 200
        # We pass the wics to the service wrangler, to be used in the adapter.
        container_type = None
        for wic in available_work_item_containers:
            input_prepper.input_parser.context_ids = [wic.external_id]
            container_type = wic.container_type
        if not input_prepper.input_parser.context_ids:
            return {"app": input_prepper.app_name, "response": {}}, HTTPStatus.OK
        product_container_type_map = {
            "e1_strategy": "e1_prm",
            "e1_work": "work",
            "lk_board": "leankit",
        }
        product_type = product_container_type_map[container_type]
        domain = domain[get_app_name_for_product_type(container_type)]
        wrangler = service_wrangler_factory(
            input_prepper,
            adapter_kwargs={
                "available_work_item_containers": [
                    utils.Map(**{"external_id": wic.external_id})
                    for wic in available_work_item_containers
                ]
            },
            override_action=utils.get_valid_action(input_prepper.action_name),
            product_type=product_type,
            domain=domain,
        )
        response_data, response_status = await wrangler.call_service()

    return response_data, response_status


@prep_input
async def current_user(request, body, input_prepper, applications):
    """Retrieve current user info for each product type."""
    print("+++++++ Start Current User +++++++")
    input_product_types = get_product_types(input_prepper) or []
    product_types = [sanitise_product_type(p) for p in input_product_types]
    domains = applications["domains"]
    apps = applications["apps"]
    # Remove un supported product types
    product_types = get_product_types_for_connected_app(product_types)
    product_types = [p for p in product_types if p in apps]
    if not product_types:
        product_types = apps

    # Now take the unique ones only
    product_types = list(set(product_types))
    log_api("current_user", product_types=product_types, apps=apps, domains=domains)

    # 1. Get it for the current app
    response_data, response_status = await current_user_for_product_type(
        request,
        body,
        input_prepper.clone(),
        input_prepper.app_name,
        domains[input_prepper.app_name],
        applications if is_pvadmin_connected_okrs(input_prepper) else None,
    )
    log_api(
        "current_user",
        "Response for current_user_for_product_type",
        [input_prepper.app_name, domains[input_prepper.app_name]],
        reponse_data=response_data,
        response_status=response_status,
    )
    if response_status != HTTPStatus.OK:

        return response_data, response_status

    for role in response_data.get("work_item_container_roles", []):
        role["product_type"] = input_prepper.app_name

    # 2. Now for all other apps gather them sequentially
    if input_prepper.app_name not in product_types:
        # We don't want current app's roles, that's ok
        consolidated_roles = []
    else:
        consolidated_roles = response_data.get("work_item_container_roles", [])

    for product_type in product_types:
        if product_type == input_prepper.app_name:
            continue

        response_app, response_status_app = await current_user_for_product_type(
            request,
            body,
            input_prepper.clone(),
            product_type,
            domains[get_app_name_for_product_type(product_type)],
            applications if is_pvadmin_connected_okrs(input_prepper) else None,
        )
        log_api(
            "current_user",
            "Response for current_user_for_product_type",
            [product_type, domains[get_app_name_for_product_type(product_type)]],
            reponse_data=response_app,
            response_status=response_status_app,
        )

        if response_status_app != HTTPStatus.OK:
            continue

        # We just need roles
        roles = response_app.get("work_item_container_roles", [])
        for role in roles:
            role["product_type"] = product_type

        consolidated_roles += roles

    log_api("current_user", "Consolidated roles", consolidated_roles)

    response_data["work_item_container_roles"] = consolidated_roles
    print("+++++++ End Current User +++++++")
    send_pubnub_event_for_user(input_prepper.user_id, input_prepper.action_name)
    return response_data, response_status


async def current_user_for_product_type(
    request, body, input_prepper, product_type, domain=None, applications=None
):
    """
    Retrieve info for the supplied user.

    Convert the [board] roles into generalized WIC roles.
    Also store these WorkItemContainerRoles in the database as a sort of cache.

    Return the following data::

        {
            id,
            first_name,
            last_name,
            email_address,
            work_item_containers: [{ context_id, okr_role, app_role }]
        }

    """
    container_type = get_container_type(product_type)
    with input_prepper.db_session() as db_session:
        available_work_item_containers = (
            db_session.query(models.WorkItemContainer)
            .filter(
                or_(
                    models.WorkItemContainer.tenant_group_id_str
                    == input_prepper.tenant_group_id,
                    models.WorkItemContainer.tenant_id_str == input_prepper.org_id,
                )
            )
            .filter_by(app_name=get_app_name_for_product_type(product_type))
            .filter(
                or_(
                    models.WorkItemContainer.container_type
                    == get_container_type_for_product_type(product_type),
                    models.WorkItemContainer.container_type == container_type,
                )
            )
            .filter_by(
                deleted_at_epoch=0,
            )
            .all()
        )
        # We pass the wics to the service wrangler, to be used in the adapter.
        input_prepper.input_parser.context_ids = [
            wic.external_id for wic in available_work_item_containers
        ]
        available_work_item_containers_dict = [
            wic.to_dict() for wic in available_work_item_containers
        ]
        if not input_prepper.input_parser.context_ids:
            return {
                "app": get_app_name_for_product_type(product_type),
                "response": {},
            }, HTTPStatus.OK
        wrangler = service_wrangler_factory(
            input_prepper,
            adapter_kwargs={
                "available_work_item_containers": [
                    utils.Map(**{"external_id": wic.external_id})
                    for wic in available_work_item_containers
                ]
            },
            override_action=utils.get_valid_action(input_prepper.action_name),
            product_type=product_type,
            domain=domain,
        )
        start = time.monotonic()
        response_data, response_status = await wrangler.call_service()
        end = time.monotonic()
        print(
            f"call_service_time_current_user:{product_type}: "
            f"{input_prepper.tenant_group_id}: "
            f"{input_prepper.planview_user_id}: {input_prepper.user_id}: {end - start}"
        )
        if not response_status == HTTPStatus.OK:
            return response_data, response_status

        log_api(
            "current_user_for_product_type",
            "Wrangler request",
            input_prepper=input_prepper,
        )
        log_api(
            "current_user_for_product_type",
            "Wrangler response",
            response_data=response_data,
            response_status=response_status,
        )
        adapted_role_data = response_data.get("work_item_container_roles", [])

        if applications:
            product_tenant_id = utils.get_tenant_id(
                applications.get("env_selectors"),
                get_app_name_for_product_type(product_type),
            )
            product_user_id = applications.get("app_users", {}).get(
                get_app_name_for_product_type(product_type)
            )
        else:
            product_tenant_id = input_prepper.org_id
            product_user_id = input_prepper.user_id
        role_factory = WorkItemContainerRoleBuilder(
            db_session=db_session,
            adapted_role_data=adapted_role_data,
            # user_id=input_prepper.user_id,
            # org_id=input_prepper.org_id,
            user_id=product_user_id,
            org_id=product_tenant_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            available_work_item_containers=available_work_item_containers_dict,
            app_name=get_app_name_for_product_type(product_type),
            token_user_id=input_prepper.user_id,
            token_org_id=input_prepper.org_id,
        )
        log_api(
            "current_user_for_product_type",
            "Role factory request",
            [
                product_user_id,
                product_tenant_id,
                available_work_item_containers_dict,
                product_type,
                adapted_role_data,
            ],
        )
        # Get the wic roles, new + updated, and write them to the db
        wic_roles = role_factory.build_roles()
        log_api("current_user_for_product_type", "Roles in DB", wic_roles)
        if wic_roles:
            db_session.add_all(wic_roles)
            commit_db_session(db_session)
    return response_data, response_status


@prep_input
async def delete_objective_and_log(request, body, input_prepper):
    """Delete an Objective based on the ID and log it."""
    with input_prepper.db_session() as db_session:
        objective_id = body["input"]["id"]
        role_filter = or_(
            models.WorkItemContainerRole.created_by == input_prepper.planview_user_id,
            and_(
                models.WorkItemContainerRole.app_created_by == input_prepper.user_id,
                models.WorkItemContainerRole.app_created_by != "",
            ),
        )
        objective = (
            db_session.query(models.Objective)
            .join(
                models.WorkItemContainer,
                (models.Objective.work_item_container_id == models.WorkItemContainer.id)
                & (models.WorkItemContainer.deleted_at_epoch == 0),
            )
            .join(
                models.WorkItemContainerRole,
                (
                    models.WorkItemContainer.id
                    == models.WorkItemContainerRole.work_item_container_id
                )
                & (models.WorkItemContainerRole.okr_role.in_(["edit", "manage"]))
                & role_filter,
            )
            .filter(
                and_(
                    models.Objective.id == objective_id,
                    models.Objective.deleted_at_epoch == 0,
                )
            )
            .first()
        )
        if not objective:
            return (
                {"errors": ["No access to this Objective for this User."]},
                HTTPStatus.NOT_FOUND,
            )

        child_objectives = (
            db_session.query(models.Objective)
            .filter(
                or_(
                    models.Objective.tenant_group_id_str
                    == input_prepper.tenant_group_id,
                    models.Objective.tenant_id_str == input_prepper.org_id,
                )
            )
            .filter(models.Objective.parent_objective_id == objective_id)
        ).all()

        delete_logger = DeletionLogger(
            instance=objective,
            db_session=db_session,
            user_id=input_prepper.user_id,
            planview_user_id=input_prepper.planview_user_id,
        )
        delete_logger.create_log()
        deleter = Deleter(db_session=db_session, model_instance=objective)
        deleter.delete()

        # Make the child objectives orphan, i.e. remove their parent objective id
        for child_objective in child_objectives:
            child_objective.parent_objective_id = None
            db_session.add(child_objective)

        commit_db_session(db_session)

    return ({"id": objective_id}, HTTPStatus.OK)


@prep_input
async def delete_key_result_and_log(request, body, input_prepper):
    """Delete a KeyResult based on the ID and log it."""
    with input_prepper.db_session() as db_session:
        key_result_id = body["input"]["id"]
        key_result = (
            db_session.query(models.KeyResult).filter_by(id=key_result_id).first()
        )

        if not key_result:
            return (
                {"errors": ["No access to this Key Result for this User."]},
                HTTPStatus.NOT_FOUND,
            )

        delete_logger = DeletionLogger(
            instance=key_result,
            db_session=db_session,
            user_id=input_prepper.user_id,
            planview_user_id=input_prepper.planview_user_id,
        )
        delete_logger.create_log()
        deleter = Deleter(db_session=db_session, model_instance=key_result)
        deleter.delete()
        commit_db_session(db_session)

    return ({"id": key_result_id}, HTTPStatus.OK)


@prep_input
async def delete_progress_point_and_log(request, body, input_prepper):
    """Delete a ProgressPoint based on the ID and log it."""
    with input_prepper.db_session() as db_session:
        progress_point_id = body["input"]["id"]
        progress_point = (
            db_session.query(models.ProgressPoint)
            .filter_by(id=progress_point_id)
            .first()
        )
        if not progress_point:
            return (
                {"errors": ["No access to this Progress Point for this User."]},
                HTTPStatus.NOT_FOUND,
            )

        delete_logger = DeletionLogger(
            instance=progress_point,
            db_session=db_session,
            user_id=input_prepper.user_id,
            planview_user_id=input_prepper.planview_user_id,
        )
        delete_logger.create_log()
        deleter = Deleter(db_session=db_session, model_instance=progress_point)
        deleter.delete()
        commit_db_session(db_session)

    return ({"id": progress_point_id}, HTTPStatus.OK)


@prep_input
async def delete_key_result_work_item_mapping_and_log(request, body, input_prepper):
    """Delete a KeyResultWorkItemMapping based on the ID and log it."""
    with input_prepper.db_session() as db_session:
        mapping_id = body["input"]["id"]
        mapping = (
            db_session.query(models.KeyResultWorkItemMapping)
            .filter_by(id=mapping_id)
            .first()
        )
        if not mapping:
            return (
                {"errors": ["No access to this Connection for this User."]},
                HTTPStatus.NOT_FOUND,
            )

        delete_logger = DeletionLogger(
            instance=mapping,
            db_session=db_session,
            user_id=input_prepper.user_id,
            planview_user_id=input_prepper.planview_user_id,
        )
        delete_logger.create_log()
        deleter = Deleter(db_session=db_session, model_instance=mapping)
        deleter.delete()
        commit_db_session(db_session)

    return ({"id": mapping_id}, HTTPStatus.OK)


@prep_input
async def list_activity_types(request, body, input_prepper, applications):
    """Define the list activity types operation."""
    domains = applications.get("domains", {})
    product_type = get_product_type(input_prepper)
    domain = domains.get(get_app_name_for_product_type(product_type))

    wrangler = service_wrangler_factory(input_prepper, domain=domain)
    response_data, response_status = await wrangler.call_service()
    return response_data, response_status


@prep_input
async def search_activities(request, body, input_prepper, applications):
    """Search activities. Return a list of WorkItem compatible objects."""
    domains = applications.get("domains", {})
    product_type = get_product_type(input_prepper)
    domain = domains.get(get_app_name_for_product_type(product_type))

    wrangler = service_wrangler_factory(input_prepper, domain=domain)
    response_data, response_status = await wrangler.call_service()
    return response_data, response_status


@prep_input
async def list_activities(request, body, input_prepper, applications):  # noqa: C901
    """Define list activities operation."""
    activity_ids = input_prepper.input_parser.get("activity_ids", [])
    key_result_id = input_prepper.input_parser.get("key_result_id")
    work_item_container_id = input_prepper.input_parser.get("work_item_container_id")
    states = input_prepper.input_parser.get("states")
    work_items = {}
    available_work_items = []
    key_results_wi_mapping = {}

    # Adorn input prepper with domains info
    domains = applications["domains"]
    container_type = get_product_type(input_prepper)
    product_type = get_product_type_for_connected_app(container_type)
    domain = domains.get(product_type)
    input_prepper.input_parser.context_id = get_context_id(
        input_prepper, models, key_result_id
    )
    with input_prepper.db_session() as db_session:
        if work_item_container_id and (not activity_ids):
            available_work_items = (
                db_session.query(models.WorkItem)
                .filter(
                    or_(
                        models.WorkItem.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                        models.WorkItem.tenant_id_str == input_prepper.org_id,
                    )
                )
                .filter_by(app_name=get_app_name_for_product_type(product_type))
                .filter(
                    or_(
                        models.WorkItem.container_type
                        == get_container_type_for_product_type(product_type),
                        models.WorkItem.container_type == container_type,
                    )
                )
                .filter_by(work_item_container_id=work_item_container_id)
                .all()
            )
            if not available_work_items:
                return [], 200

            activity_ids = [wi.external_id for wi in available_work_items]
        elif key_result_id and (not activity_ids):
            available_work_items = (
                db_session.query(models.WorkItem)
                .filter(
                    or_(
                        models.WorkItem.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                        models.WorkItem.tenant_id_str == input_prepper.org_id,
                    )
                )
                .filter_by(app_name=get_app_name_for_product_type(product_type))
                .filter(
                    or_(
                        models.WorkItem.container_type
                        == get_container_type_for_product_type(product_type),
                        models.WorkItem.container_type == container_type,
                    )
                )
                .join(models.KeyResultWorkItemMapping)
                .filter(models.KeyResultWorkItemMapping.key_result_id == key_result_id)
                .all()
            )
            if not available_work_items:
                return [], 200

            mappings = (
                db_session.query(models.KeyResultWorkItemMapping)
                .filter(models.KeyResultWorkItemMapping.key_result_id == key_result_id)
                .filter(
                    or_(
                        models.KeyResultWorkItemMapping.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                        models.KeyResultWorkItemMapping.tenant_id_str
                        == input_prepper.org_id,
                    )
                )
                .filter(
                    models.KeyResultWorkItemMapping.work_item_id.in_(
                        [wi.id for wi in available_work_items]
                    )
                )
                .all()
            )
            key_results_wi_mapping = {
                mapping.work_item_id: mapping.id for mapping in mappings
            }
            activity_ids = [wi.external_id for wi in available_work_items]
        if not activity_ids:
            available_work_items = (
                db_session.query(models.WorkItem)
                .filter(
                    or_(
                        models.WorkItem.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                        models.WorkItem.tenant_id_str == input_prepper.org_id,
                    )
                )
                .filter_by(app_name=get_app_name_for_product_type(product_type))
                .filter(
                    or_(
                        models.WorkItem.container_type
                        == get_container_type_for_product_type(product_type),
                        models.WorkItem.container_type == container_type,
                    )
                )
                .all()
            )

            if not available_work_items:
                return [], 200

            activity_ids = [wi.external_id for wi in available_work_items]
            input_prepper.input_parser.activity_ids = activity_ids
        else:
            input_prepper.input_parser.activity_ids = activity_ids
        work_items = {
            wi.id: (
                wi.external_id,
                {
                    "id": wi.work_item_container.id,
                    "external_id": wi.work_item_container.external_id,
                    "external_title": wi.work_item_container.external_title,
                },
            )
            for wi in available_work_items
        }
    product_type = get_product_type_for_connected_app(product_type)
    wrangler = service_wrangler_factory(
        input_prepper, product_type=product_type, domain=domain
    )

    response_data, response_status = await wrangler.call_service()
    if response_status == HTTPStatus.OK and work_items:
        external_id_map = {
            response["external_id"]: response for response in response_data
        }
        mapped_response_data = list(
            map(
                lambda wiid: {"id": wiid, "work_item_container": work_items[wiid][1]}
                | external_id_map[work_items[wiid][0]]
                if work_items[wiid][0] in external_id_map
                else None,
                work_items,
            )
        )
        response_data = [data for data in mapped_response_data if data is not None]
    response_data = [
        data
        | {
            "key_result_work_item_mapping_id": key_results_wi_mapping.get(
                data.get("id")
            )
        }
        for data in response_data
        if isinstance(data, dict)
    ]

    if states:
        response_data = [
            data
            for data in response_data
            if (data["state"] in states) or (data["state"] is None)
        ]

    for data in response_data:
        if (data["title"] is None) and (data["state"] is None):
            data["is_accessible"] = False
        else:
            data["is_accessible"] = True
    return response_data, response_status


@prep_input
async def search_activity_containers(request, body, input_prepper, applications):
    """Define the search operation."""
    domains = applications.get("domains", {})
    product_type = get_product_type(input_prepper)
    domain = domains.get(get_app_name_for_product_type(product_type))

    wrangler = service_wrangler_factory(input_prepper, domain=domain)
    response_data, response_status = await wrangler.call_service()
    return response_data, response_status


@prep_input
async def list_activity_containers(request, body, input_prepper, applications):
    """Define list activity containers action."""

    input_product_types = get_product_types(input_prepper) or []
    product_types = [sanitise_product_type(p) for p in input_product_types]

    domains = applications["domains"]
    apps = applications["apps"]
    # Now take the unique ones only
    product_types = list(set(product_types))
    product_types = get_product_types_for_connected_app(product_types)
    product_types = [p for p in product_types if p in apps]
    if not product_types:
        product_types = applications["apps"]
    results = await asyncio.gather(
        *[
            list_activity_containers_for_product_type(
                request, body, input_prepper.clone(), p, domains[p]
            )
            for p in product_types
        ]
    )
    all_responses_lists = [r[0] for r in results if r[1] == HTTPStatus.OK]
    all_responses = [
        response for sublist in all_responses_lists for response in sublist
    ]
    send_pubnub_event_for_user(input_prepper.user_id, input_prepper.action_name)
    return all_responses, HTTPStatus.OK


async def list_activity_containers_for_product_type(
    request, body, input_prepper, product_type, domain=None
):
    """Define list containers operation for a specific product type."""
    container_ids = input_prepper.input_parser.get("container_ids")
    wi_containers = {}
    container_type = get_container_type(product_type)
    if not container_ids:
        with input_prepper.db_session() as db_session:
            available_work_item_containers = (
                db_session.query(models.WorkItemContainer)
                .filter(
                    or_(
                        models.WorkItemContainer.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                        models.WorkItemContainer.tenant_id_str == input_prepper.org_id,
                    )
                )
                .filter_by(app_name=get_app_name_for_product_type(product_type))
                .filter(
                    or_(
                        models.WorkItemContainer.container_type
                        == get_container_type_for_product_type(product_type),
                        models.WorkItemContainer.container_type == container_type,
                    )
                )
                .filter_by(
                    deleted_at_epoch=0,
                )
                .all()
            )
            if not available_work_item_containers:
                return [], HTTPStatus.OK

            container_ids = [wic.external_id for wic in available_work_item_containers]
            wi_containers = {
                wic.id: wic.external_id for wic in available_work_item_containers
            }
            input_prepper.input_parser.container_ids = container_ids

    wrangler = service_wrangler_factory(
        input_prepper,
        product_type=product_type,
        override_action=utils.get_valid_action(input_prepper.action_name),
        domain=domain,
    )
    start = time.monotonic()
    response_data, response_status = await wrangler.call_service()
    end = time.monotonic()
    print(
        f"call_service_time_list_activity_containers:{product_type}: "
        f"{input_prepper.tenant_group_id}: "
        f"{input_prepper.planview_user_id}: {input_prepper.user_id}: {end - start}"
    )
    if response_status == HTTPStatus.OK and wi_containers:
        external_id_map = {
            response["external_id"]: response
            for response in response_data
            if response["title"]
        }
        mapped_response_data = list(
            map(
                lambda wicid: {"id": wicid} | external_id_map[wi_containers[wicid]]
                if wi_containers[wicid] in external_id_map
                else None,
                wi_containers,
            )
        )

        new_response_data = [data for data in mapped_response_data if data is not None]
        lacm = ListActivitityContainersManager(input_prepper)
        lacm.update_container_external_titles(new_response_data)

        return new_response_data, response_status

    return response_data, response_status


@prep_input
async def search_users(request, body, input_prepper, applications):
    """Search users. Return a list of Users."""
    domains = applications.get("domains", {})
    product_type = get_product_type(input_prepper)
    domain = domains.get(get_app_name_for_product_type(product_type))
    product_type = get_product_type_for_connected_app(product_type)
    wrangler = service_wrangler_factory(
        input_prepper, domain=domain, product_type=product_type
    )
    response_data, response_status = await wrangler.call_service()
    # Check if we need to call Planview admin service API
    if is_pvadmin_connected_okrs(input_prepper) and response_status == 200:
        env_selector = applications.get("env_selectors", {}).get(
            get_app_name_for_product_type(product_type)
        )
        response_data = await add_pvid_to_response_data(
            input_prepper, response_data, env_selector=env_selector
        )
        response_data = [
            each for each in response_data if each.get("planview_user_id", None)
        ]
    return response_data, response_status


@prep_input(validators=["level_config"])
async def update_level_config(request, body, input_prepper):
    """Update the level config for the organization."""

    with input_prepper.db_session() as db_session:
        input_parser = input_prepper.input_parser
        # Get or create the Setting
        manager = SettingsManager(
            org_id=input_prepper.org_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            db_session=db_session,
        )
        setting = manager.find_or_build()

        # Update the level_config
        level_config = input_parser.level_config
        setting.level_config = level_config
        setting.last_updated_by = input_prepper.planview_user_id
        db_session.add(setting)
        commit_db_session(db_session)

    return {"errors": [], "level_config": level_config}, HTTPStatus.OK


@prep_input
async def delete_level_from_level_config(request, body, input_prepper=None):
    """Update the level config for the organization."""
    input_parser = input_prepper.input_parser
    with input_prepper.db_session() as db_session:
        # find the setting

        if not input_prepper.tenant_group_id:
            setting = (
                db_session.query(models.Setting)
                .filter(
                    models.Setting.tenant_id_str == input_prepper.org_id,
                )
                .first()
            )
        else:
            setting = (
                db_session.query(models.Setting)
                .filter(
                    or_(
                        and_(
                            models.Setting.tenant_id_str == input_prepper.org_id,
                            models.Setting.tenant_id_str != "",
                        ),
                        models.Setting.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                    )
                )
                .first()
            )

        if not setting:
            return (
                {
                    "errors": [
                        ValidationError(
                            code="setting_not_found",
                            message="Could not find the Setting for this org.",
                        ).to_dict()
                    ]
                },
                HTTPStatus.NOT_FOUND,
            )

        validator = LevelConfigDeletionValidator(
            input_prepper=input_prepper,
            existing_level_config=setting.level_config,
        )
        if not validator.validate():
            return {
                "level_config": setting.level_config,
                "errors": validator.serializable_errors,
            }, HTTPStatus.OK

        level_config = validator.proposed_level_config()
        setting.level_config = level_config
        tenant_id_str = setting.tenant_id_str
        db_session.add(setting)
        commit_db_session(db_session)

    with input_prepper.db_session() as db_session:
        relevel_after_deletion(
            db_session=db_session,
            tenant_id_str=tenant_id_str,
            tenant_group_id_str=input_prepper.tenant_group_id,
            deleted_level_depth=input_parser.level_depth,
            level_config=level_config,
        )

    return {
        "level_config": level_config,
        "errors": [],
    }, HTTPStatus.OK


@prep_input
async def insert_level_config(request, body, input_prepper=None):
    """Update the level config for the organization."""
    with input_prepper.db_session() as db_session:
        # find the setting
        if not input_prepper.tenant_group_id:
            setting = (
                db_session.query(models.Setting)
                .filter(models.Setting.tenant_id_str == input_prepper.org_id)
                .first()
            )
        else:
            setting = (
                db_session.query(models.Setting)
                .filter(
                    or_(
                        and_(
                            models.Setting.tenant_id_str == input_prepper.org_id,
                            models.Setting.tenant_id_str != "",
                        ),
                        models.Setting.tenant_group_id_str
                        == input_prepper.tenant_group_id,
                    )
                )
                .first()
            )

        if not setting:
            return (
                {
                    "errors": [
                        ValidationError(
                            code="setting_not_found",
                            message="Could not find the Setting for this org.",
                        ).to_dict()
                    ]
                },
                HTTPStatus.NOT_FOUND,
            )

        validator = LevelConfigInsertValidator(
            input_prepper=input_prepper,
            existing_level_config=setting.level_config,
        )
        if not validator.validate():
            return (
                {
                    "level_config": validator.proposed_level_config(),
                    "errors": validator.serializable_errors,
                    "message": validator.error_message,
                },
                HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        level_config = validator.proposed_level_config()
        setting.level_config = level_config
        tenant_id_str = setting.tenant_id_str
        db_session.add(setting)
        commit_db_session(db_session)

    with input_prepper.db_session() as db_session:
        relevel_after_insert(
            db_session=db_session,
            tenant_id_str=tenant_id_str,
            tenant_group_id_str=input_prepper.tenant_group_id,
            inserted_level_depth=validator.insert_at,
        )

    return {
        "level_config": level_config,
        "errors": [],
    }, HTTPStatus.OK


@prep_input
async def users_info(request, body, input_prepper=None, applications=None):
    """Find user info from PVAdmin."""
    user_details = [{"id": x} for x in input_prepper.input_parser.user_ids]

    if (
        is_pvadmin_connected_okrs(input_prepper)
        and applications
        and applications["env_selectors"]
    ):
        all_users_info = await asyncio.gather(
            *[
                add_pvid_to_response_data(
                    input_prepper, user_details, env_selector=env_selector
                )
                for env_selector in applications["env_selectors"].values()
            ]
        )

        users_map = {
            x: {"id": x, "planview_user_id": None}
            for x in input_prepper.input_parser.user_ids
        }
        for response_list in all_users_info:
            for response in response_list:
                if response["id"] in users_map:
                    current_value = users_map[response["id"]].get("planview_user_id")
                    response_value = response["planview_user_id"]
                    if (current_value is None) and (response_value is not None):
                        users_map[response["id"]]["planview_user_id"] = response_value

        users_info_with_details = await add_pvid_user_details_to_response_data(
            input_prepper, users_map.values()
        )
        return users_info_with_details, HTTPStatus.OK

    return user_details, HTTPStatus.OK


@prep_input
async def list_objectives(request, body, input_prepper=None):
    """List all objectives in a container."""

    def get_progress_points_props(progress_dict):
        return {
            key: progress_dict.get(key)
            for key in [
                "id",
                "value",
                "measured_at",
                "comment",
                "key_result_id",
                "objective_progress_percentage",
                "key_result_progress_percentage",
            ]
        }

    def get_key_results_props(kr_dict):
        kr = {
            key: kr_dict.get(key)
            for key in [
                "id",
                "name",
                "progress_percentage",
                "starts_at",
                "ends_at",
                "starting_value",
                "value_type",
                "target_value",
                "created_at",
                "app_owned_by",
                "owned_by",
                "objective_id",
            ]
        }

        kr["progress_points"] = [
            get_progress_points_props(p) for p in kr_dict.get("progress_points", [])
        ]

        kr["activities"] = kr_dict.get("activities", [])
        return kr

    def get_objective_props(objective_dict):
        objective = {
            key: objective_dict.get(key)
            for key in [
                "id",
                "name",
                "parent_objective_id",
                "level_depth",
                "starts_at",
                "ends_at",
                "created_at",
                "app_owned_by",
                "owned_by",
                "progress_percentage",
                "container",
            ]
        }
        objective["key_results"] = [
            get_key_results_props(kr) for kr in objective_dict["key_results"]
        ]

        return objective

    response_objectives = await list_container_objectives(input_prepper)

    return [get_objective_props(o) for o in response_objectives], HTTPStatus.OK


@prep_input
async def get_channel(request, body, input_prepper=None):
    """Create a new channel from input data and return with subscriber id."""

    tenant_id_str = input_prepper.org_id
    tenant_group_id_str = input_prepper.tenant_group_id
    app_name = input_prepper.app_name
    container_id = input_prepper.input_parser.container_id
    return (
        dict(
            container_channel=get_container_channel_name(
                tenant_id_str, tenant_group_id_str, app_name, container_id
            ),
            tenant_channel=get_tenant_channel_name(tenant_group_id_str),
            user_channel=get_user_channel_name(input_prepper.user_id),
            subscriber_key=get_subscriber_key(),
            uuid=get_pubnub_uuid(),
        ),
        HTTPStatus.OK,
    )


@prep_input
async def connected_apps(request, body, input_prepper=None, applications=None):
    """Get details of connected apps."""
    is_pvadmin = is_pvadmin_connected_okrs(input_prepper)
    if is_pvadmin:
        e1_new_route = await _verify_portfolios_version_for_work(input_prepper)
        return (
            dict(
                apps=applications["apps"],
                domains=applications["domain_info"],
                is_pvadmin=is_pvadmin,
                e1_new_route=e1_new_route,
            ),
            HTTPStatus.OK,
        )
    return (
        dict(
            apps=applications["apps"],
            domains=applications["domain_info"],
            is_pvadmin=is_pvadmin,
            e1_new_route=None,
        ),
        HTTPStatus.OK,
    )


@prep_input
async def custom_attributes_configurations(request, body, input_prepper):
    """
    Get a list of configurations for custom attributes.

    Pre-conditions:
        1. Must be a PVAdmin customer
    Post-conditions:
        1. Return payload should contain all configurations for CA for this tenant group id.
        2. If the default fields are not created then create those and add in the return payload.
    """

    if not is_pvadmin_connected_okrs(input_prepper):
        return adapt_error_for_hasura(
            [dict(message="Not a pvadmin customer", error_code="NO_PVADMIN_CUSTOMER")],
            HTTPStatus.BAD_REQUEST,
        )

    with input_prepper.db_session() as db_session:
        ca_configs = fetch_all_active_configurations(db_session, input_prepper)

        default_fields = [f for f in ca_configs if f.is_default is True]
        # post-condition 2
        if len(default_fields) != DEFAULT_FIELDS_NUM:
            remove_default_configurations(db_session, input_prepper)
            create_default_configurations(db_session, input_prepper)

        # Re-fetch with options
        ca_configs = fetch_all_configurations(db_session, input_prepper)

        return ca_configs_response_adapter(ca_configs), HTTPStatus.OK

    return [], HTTPStatus.OK


@prep_input
async def insert_custom_attributes_configuration(request, body, input_prepper):
    """
    Insert a new configuration for custom attributes.

    Pre-conditions:
        1. Must be pvadmin user
        2. New config cannot exceed max number of unarchived and undeleted configurations.
        3. New config cannot be a default config.
        4. Cannot create archived or deleted fields via API.
        5. Basic fields validation common for all operations.

    Post-conditions:
        1. singleselect and multiselect options should have unique IDs
    """

    if not is_pvadmin_connected_okrs(input_prepper):
        return adapt_error_for_hasura(
            [dict(message="Not a pvadmin customer", error_code="NOT_PVADMIN_CUSTOMER")],
            HTTPStatus.BAD_REQUEST,
        )

    claims = input_prepper.jwt_parser.payload.hasura_claims()
    default_role = claims.get("x-hasura-default-role")
    if default_role.lower() not in ["manage"]:
        return adapt_error_for_hasura(
            [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
            HTTPStatus.FORBIDDEN,
        )

    with input_prepper.db_session() as db_session:
        active_configs = fetch_all_active_configurations(db_session, input_prepper)
        if len(active_configs) >= MAX_ACTIVE_CA_FIELD:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Cannot create more custom attributes",
                        error_code="MAX_CUSTOM_CONFIGS_REACHED",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        config_args = input_prepper.input_parser
        if config_args.is_default:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Cannot create more default attributes",
                        error_code="CANNOT_CREATE_DEFAULT_ATTRIBUTE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        if config_args.is_deleted or config_args.is_archived:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Only active attributes can be created via API",
                        error_code="CANNOT_CREATE_ARCHIVED_ATTRIBUTE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        errors = validate_configuration(config_args)
        if errors:
            return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)

        processed_config = add_ca_option_ids(config_args)

        config = create_new_configuration(db_session, input_prepper, processed_config)
        return ca_config_response_adapter(config), HTTPStatus.OK


@prep_input
async def update_custom_attributes_configuration(request, body, input_prepper):
    """
    Update a configuration for custom attributes.

    Pre-conditions:
        1. Must be pvadmin user
        2. Must have manager role
        3. Must have a valid ID - cannot updated deleted or archived config
        4. Should not edit certain details for default fields
        5. Can only update selected fields.
        6. Basic fields validation common for all operations.
        7. Unarchive needs to check max number of active fields.
    Post-conditions:
        1. singleselect and multiselect options should have unique IDs
    """

    if not is_pvadmin_connected_okrs(input_prepper):
        return adapt_error_for_hasura(
            [dict(message="Not a pvadmin customer", error_code="NOT_PVADMIN_CUSTOMER")],
            HTTPStatus.BAD_REQUEST,
        )

    claims = input_prepper.jwt_parser.payload.hasura_claims()
    default_role = claims.get("x-hasura-default-role")
    if default_role.lower() not in ["manage"]:
        return adapt_error_for_hasura(
            [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
            HTTPStatus.FORBIDDEN,
        )

    with input_prepper.db_session() as db_session:
        current_config = fetch_configuration(db_session, input_prepper)

        if (not current_config) or current_config.is_deleted:
            return adapt_error_for_hasura("", HTTPStatus.NOT_FOUND)

        config_args = input_prepper.input_parser

        allowed_fields_for_update = [
            "value",
            "is_objective",
            "is_keyresult",
            "is_mandatory_objective",
            "is_mandatory_keyresult",
            "tooltip",
        ]
        if not current_config.is_default:
            allowed_fields_for_update.append("label")
            allowed_fields_for_update.append("is_archived")

        params = {
            k: config_args.get(k)
            for k in config_args.keys()
            if (k in allowed_fields_for_update) and (config_args[k] is not None)
        }

        # If we are unarchiving, verify we will not have more than limited active fields
        active_fields = fetch_all_active_configurations(db_session, input_prepper)
        if "is_archived" in params:
            if (params["is_archived"] is False) and (
                len(active_fields) >= MAX_ACTIVE_CA_FIELD
            ):
                return adapt_error_for_hasura(
                    [
                        dict(
                            message="Cannot reactivate - max field limit exceeded",
                            error_code="MAX_CUSTOM_CONFIGS_REACHED",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )

            if params["is_archived"] is None:
                del params["is_archived"]

        for p in params.keys():
            current_config.__setattr__(p, params[p])

        config_dict = current_config.to_dict()
        errors = validate_update_configuration(config_dict)
        if errors:
            return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)

        config_dict = add_ca_option_ids(config_dict)
        current_config.value = config_dict["value"]
        update_configuration(db_session, current_config)

        # Re-fetch
        config = fetch_configuration(db_session, input_prepper)
        return ca_config_response_adapter(config), HTTPStatus.OK


@prep_input
async def delete_custom_attributes_configuration(request, body, input_prepper):
    """
    Soft deletes a configuration for custom attributes.

    Pre-conditions:
        1. Must be pvadmin user with manage role
        2. Must be valid config, not already deleted.
        3. Cannot be default config.
        4. Must be archived first to be deleted.
    """

    if not is_pvadmin_connected_okrs(input_prepper):
        return adapt_error_for_hasura(
            [dict(message="Not a pvadmin customer", error_code="NOT_PVADMIN_CUSTOMER")],
            HTTPStatus.BAD_REQUEST,
        )

    claims = input_prepper.jwt_parser.payload.hasura_claims()
    default_role = claims.get("x-hasura-default-role")
    if default_role.lower() not in ["manage"]:
        return adapt_error_for_hasura(
            [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
            HTTPStatus.FORBIDDEN,
        )

    with input_prepper.db_session() as db_session:
        current_config = fetch_configuration(db_session, input_prepper)

        if (not current_config) or current_config.is_deleted:
            return adapt_error_for_hasura("", HTTPStatus.NOT_FOUND)

        if current_config.is_default:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Cannot delete default config",
                        error_code="CANNOT_DELETE_DEFAULT_CONFIG",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        if not current_config.is_archived:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Cannot delete unarchived config, first archive then delete",
                        error_code="CANNOT_DELETE_UNARCHIVED_CONFIG",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        current_config.is_deleted = True
        current_config.soft_delete()
        db_session.add(current_config)
        commit_db_session(db_session)
        return ca_config_response_adapter(current_config), HTTPStatus.OK


@prep_input
async def custom_attributes(request, body, input_prepper):
    """
    Get all custom attributes along with their configuration for an object.

    An object is either an Objective or a Key Result.

    Pre-conditions:
        1. Should work only for pvadmin customers.
    """
    # pre-condition 1
    if not is_pvadmin_connected_okrs(input_prepper):
        return adapt_error_for_hasura("", HTTPStatus.BAD_REQUEST)

    with input_prepper.db_session() as db_session:
        okr_role = get_okr_role_for_object(db_session, input_prepper)
        if okr_role == "none":
            return adapt_error_for_hasura(
                dict(
                    message="User not authenticated to access custom attributes",
                    error_code="CANNOT_ACCESS_OBJECT",
                ),
                HTTPStatus.UNAUTHORIZED,
            )

        ca_values = fetch_custom_attributes(db_session, input_prepper)
        # ca_configs = fetch_all_configurations(db_session, input_prepper)
        return (
            ca_values_response_adapter(ca_values),
            HTTPStatus.OK,
        )


@prep_input
async def insert_objective(request, body, input_prepper):
    """
    Insert Objective along with Custom attributes.

    Pre-conditions:
        1. Basic field validation for Objective
        2. Comprehensive fields validation for CA values
    """

    input_data = input_prepper.input_parser

    with input_prepper.db_session() as db_session:
        wic = (
            db_session.query(models.WorkItemContainer)
            .filter_by(external_id=input_data.external_id)
            .filter(
                or_(
                    models.WorkItemContainer.tenant_group_id_str
                    == input_prepper.tenant_group_id,
                    models.WorkItemContainer.tenant_id_str == input_prepper.org_id,
                )
            )
            .filter_by(
                deleted_at_epoch=0,
            )
            .filter_by(app_name=get_app_name_for_product_type(input_data.external_type))
            .first()
        )
        validation_result = validate_app_owned_by(input_data, input_prepper)
        if validation_result is not None:
            return validation_result

        error = validate_and_format_dates(input_data, "CANNOT_CREATE_OBJECTIVE")
        if error:
            return adapt_error_for_hasura(error, HTTPStatus.BAD_REQUEST)

        if not wic:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no work item container found with \
                                    given external_id and external_type",
                        error_code="CANNOT_CREATE_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        wic.external_title = input_data.external_title
        db_session.add(wic)
        commit_db_session(db_session)
        wic_role = get_wic_role(db_session, input_prepper, wic.id)

        if not wic_role or wic_role.okr_role not in ["manage", "edit"]:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no work item container role found",
                        error_code="CANNOT_CREATE_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            input_data["ca_values"] = json.loads(input_data["ca_values"])
            errors = validate_and_fix_ca_values(
                db_session, input_prepper, input_data["ca_values"]
            )
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)
        input_data["work_item_container_id"] = wic.id
        try:
            objective = create_new_objective(db_session, input_prepper, input_data)
        except BaseException as e:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"Could not create objective: {e}",
                        error_code="CANNOT_CREATE_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            try:
                create_new_ca_value(
                    db_session,
                    input_prepper,
                    input_data["ca_values"],
                    {"object_id": objective.id, "object_type": "objective"},
                )
            except BaseException as e:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message=f"Can't create values for objective {objective.id}: {e}",
                            error_code="CANNOT_CREATE_CUSTOM_ATTRIBUTE_VALUES",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
        return {"id": objective.id}, HTTPStatus.OK


@prep_input
async def update_objective_inline(request, body, input_prepper):
    """Update Objective with name and owner_by."""

    input_data = input_prepper.input_parser
    valid_fields = ["name", "owned_by"]
    with input_prepper.db_session() as db_session:
        objective = fetch_objective(db_session, input_prepper)
        if not objective:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no objective found",
                        error_code="CANNOT_FIND_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        for each in valid_fields:
            if each in input_data:
                objective.__setattr__(each, input_data[each])
        db_session.add(objective)
        commit_db_session(db_session)

        return {"id": objective.id}, HTTPStatus.OK


@prep_input
async def update_objective(request, body, input_prepper):
    """
    Update Objective along with Custom attributes.

    Pre-conditions:
        1. Basic fields validation for Objective
        2. Comprehensive fields validation for CA values
    """
    input_data = input_prepper.input_parser
    with input_prepper.db_session() as db_session:
        objective = fetch_objective(db_session, input_prepper)
        if not objective:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no objective found",
                        error_code="CANNOT_FIND_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        previous_starts_at = objective.starts_at
        previous_ends_at = objective.ends_at
        wic_role = get_wic_role(
            db_session, input_prepper, objective.work_item_container.id
        )
        if not wic_role or wic_role.okr_role not in ["manage", "edit"]:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no work item container role found",
                        error_code="CANNOT_UPDATE_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        validation_result = validate_app_owned_by(input_data, input_prepper)
        if validation_result is not None:
            return validation_result

        error = validate_and_format_dates(input_data, "CANNOT_UPDATE_OBJECTIVE")
        if error:
            return adapt_error_for_hasura(error, HTTPStatus.BAD_REQUEST)

        input_data["last_updated_by"] = input_prepper.planview_user_id
        input_data["app_last_updated_by"] = input_prepper.user_id
        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            input_data["ca_values"] = json.loads(input_data["ca_values"])
            errors = validate_and_fix_ca_values(
                db_session, input_prepper, input_data["ca_values"]
            )
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)

        params = {
            k: input_data.get(k)
            for k in input_data.keys()
            if (k in MODIFIABLE_DB_FIELDS)
        }
        for p in params.keys():
            objective.__setattr__(p, params[p])
        db_session.add(objective)

        error = validate_objective_and_update_kr_daterange(
            objective.id,
            previous_starts_at,
            previous_ends_at,
            input_data["starts_at"],
            input_data["ends_at"],
            db_session,
        )
        if error:
            return adapt_error_for_hasura(
                [{"message": error, "error_code": "CANNOT_UPDATE_OBJECTIVE"}],
                HTTPStatus.BAD_REQUEST,
            )

        try:
            commit_db_session(db_session)
        except BaseException as e:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"Could not update objective: {e}",
                        error_code="CANNOT_UPDATE_OBJECTIVE",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            try:
                update_ca_values(
                    db_session,
                    input_prepper,
                    input_data["ca_values"],
                    {"object_id": objective.id, "object_type": "objective"},
                )
            except BaseException as e:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message=f"Can't create values for objective {objective.id}: {e}",
                            error_code="CANNOT_CREATE_CUSTOM_ATTRIBUTE_VALUES",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
        return {"id": objective.id}, HTTPStatus.OK


@prep_input
async def insert_keyresult(request, body, input_prepper):
    """
    Insert Keyresult along with Custom attributes.

    Pre-conditions:
        1. Basic fields validation for Keyresult
        2. Comprehensive fields validation for CA values
    """
    input_data = input_prepper.input_parser
    with input_prepper.db_session() as db_session:
        objective = (
            db_session.query(models.Objective)
            .filter_by(id=input_data.objective_id)
            .filter_by(
                deleted_at_epoch=0,
            )
            .first()
        )

        if not objective:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"There is no objective found with "
                        f"given Id: {input_data.objective_id}",
                        error_code="CANNOT_CREATE_KEY_RESULT",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        validation_result = validate_app_owned_by(input_data, input_prepper)
        if validation_result is not None:
            return validation_result

        # TODO: Remove the else block once the multi targets' feature has been enabled for everyone
        if "targets" in input_data and input_data["targets"]:
            errors, formatted_targets = validate_targets(input_data["targets"])
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)
            input_data["starts_at"] = formatted_targets[0]["starts_at"]
            input_data["ends_at"] = formatted_targets[-1]["ends_at"]
            input_data["target_value"] = formatted_targets[-1]["value"]
            input_data["targets"] = formatted_targets
        else:
            errors, targets_data = validate_input_and_generate_targets(input_data)
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)
            input_data["targets"] = targets_data

        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            input_data["ca_values"] = json.loads(input_data["ca_values"])
            errors = validate_and_fix_ca_values(
                db_session, input_prepper, input_data["ca_values"]
            )
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)
        try:
            key_result = create_new_keyresult(db_session, input_prepper, input_data)
            krt = KeyResultTargetsManager(key_result.id, db_session=db_session)
            krt.create_targets(input_prepper, input_data["targets"])
            commit_db_session(db_session)
        except BaseException as e:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"Could not create key result: {e}",
                        error_code="CANNOT_CREATE_KEY_RESULT",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            try:
                create_new_ca_value(
                    db_session,
                    input_prepper,
                    input_data["ca_values"],
                    {"object_id": key_result.id, "object_type": "keyresult"},
                )
            except BaseException as e:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message=f"Can't create values for key result {key_result.id}: {e}",
                            error_code="CANNOT_CREATE_CUSTOM_ATTRIBUTE_VALUES",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
        return {"id": key_result.id}, HTTPStatus.OK


@prep_input
async def update_keyresult_inline(request, body, input_prepper):
    """Update Key Result by name and owner by."""
    input_data = input_prepper.input_parser
    valid_fields = ["name", "owned_by"]
    with input_prepper.db_session() as db_session:
        key_result = fetch_key_result(db_session, input_prepper)
        if not key_result:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no key result found",
                        error_code="CANNOT_FIND_KEY_RESULT",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        for each in valid_fields:
            if each in input_data:
                key_result.__setattr__(each, input_data[each])
        db_session.add(key_result)
        commit_db_session(db_session)

        return {"id": key_result.id}, HTTPStatus.OK


@prep_input
async def update_keyresult(request, body, input_prepper):
    """
    Update Key Result along with Custom attributes.

    Pre-conditions:
        1. Basic fields validation for Key result
        2. Comprehensive fields validation for CA values
    """
    input_data = input_prepper.input_parser
    with input_prepper.db_session() as db_session:
        key_result = fetch_key_result(db_session, input_prepper)
        if not key_result:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="There is no key result found",
                        error_code="CANNOT_FIND_KEY_RESULT",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        validation_result = validate_app_owned_by(input_data, input_prepper)
        if validation_result is not None:
            return validation_result

        # TODO: Remove the else block once the multi targets' feature has been enabled for everyone
        if "targets" in input_data and input_data["targets"]:
            errors, formatted_targets = validate_targets(input_data["targets"])
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)
            input_data["starts_at"] = formatted_targets[0]["starts_at"]
            input_data["ends_at"] = formatted_targets[-1]["ends_at"]
            input_data["target_value"] = formatted_targets[-1]["value"]
            input_data["targets"] = formatted_targets
        else:
            errors, targets_data = validate_input_and_generate_targets(input_data)
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)
            input_data["targets"] = targets_data

        input_data["last_updated_by"] = input_prepper.planview_user_id
        input_data["app_last_updated_by"] = input_prepper.user_id

        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            input_data["ca_values"] = json.loads(input_data["ca_values"])
            errors = validate_and_fix_ca_values(
                db_session, input_prepper, input_data["ca_values"]
            )
            if errors:
                return adapt_error_for_hasura(errors, HTTPStatus.BAD_REQUEST)

        params = {
            k: input_data.get(k)
            for k in input_data.keys()
            if (k in KEYRESULT_DB_FIELDS)
        }
        for p in params.keys():
            key_result.__setattr__(p, params[p])

        try:
            db_session.add(key_result)
            krt = KeyResultTargetsManager(key_result.id, db_session=db_session)
            krt.manage_targets(input_prepper, input_data["targets"])
            commit_db_session(db_session)
        except BaseException as e:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"Could not update key result: {e}",
                        error_code="CANNOT_UPDATE_KEY_RESULT",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        if "ca_values" in input_data and is_pvadmin_connected_okrs(input_prepper):
            try:
                update_ca_values(
                    db_session,
                    input_prepper,
                    input_data["ca_values"],
                    {"object_id": key_result.id, "object_type": "keyresult"},
                )
            except BaseException as e:
                return adapt_error_for_hasura(
                    [
                        dict(
                            message=f"Can't create values for key result {key_result.id}: {e}",
                            error_code="CANNOT_CREATE_CUSTOM_ATTRIBUTE_VALUES",
                        )
                    ],
                    HTTPStatus.BAD_REQUEST,
                )
        return {"id": key_result.id}, HTTPStatus.OK


@prep_input
async def get_history(request, body, input_prepper=None):
    """Get History of objectives and key results."""
    with input_prepper.db_session() as db_session:
        values = fetch_history(db_session, input_prepper)
        return (values, HTTPStatus.OK)


@prep_input
async def insert_progress_point(request, body, input_prepper=None):
    """Insert Progress Point and re-calculates progress percentages."""
    ppm = ProgressPointsManager(input_prepper)
    return ppm.create_progress_points()


@prep_input
async def update_progress_point(request, body, input_prepper=None):
    """Update Progress Point and re-calculates progress percentages."""
    ppm = ProgressPointsManager(input_prepper)
    return ppm.update_progress_percentage()


@prep_input
async def delete_progress_point(request, body, input_prepper=None):
    """Delete Progress Point and re-calculates progress percentages."""
    ppm = ProgressPointsManager(input_prepper)
    return ppm.delete_progress_percentage()


@prep_input
async def insert_custom_attributes_settings(request, body, input_prepper):
    """
    Insert a new custom attributes settings.

    Pre-conditions:
        1. Must be pvadmin user
        2. Basic fields validation common for all operations.

    """
    with input_prepper.db_session() as db_session:
        input_data = input_prepper.input_parser
        if not is_pvadmin_connected_okrs(input_prepper):
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Not a pvadmin customer",
                        error_code="NOT_PVADMIN_CUSTOMER",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        claims = input_prepper.jwt_parser.payload.hasura_claims()
        default_role = claims.get("x-hasura-default-role")
        if default_role.lower() not in ["manage"]:
            return adapt_error_for_hasura(
                [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
                HTTPStatus.FORBIDDEN,
            )
        if get_existing_custom_attributes_settings(db_session, input_prepper):
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Custom attribute settings already exists for this tenant group",
                        error_code="CUSTOM_ATTRIBUTE_SETTINGS_ALREADY_EXISTS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        try:
            settings = create_new_custom_attributes_settings(
                db_session, input_prepper, input_data
            )
        except BaseException as e:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"Could not create custom attribute settings: {e}",
                        error_code="CANNOT_CREATE_CUSTOM_ATTRIBUTE_SETTINGS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
    return {"id": settings.id}, HTTPStatus.OK


@prep_input
async def update_custom_attributes_settings(request, body, input_prepper):
    """
    Update an existing custom attributes settings.

    Pre-conditions:
        1. Must be pvadmin user
        2. Basic fields validation common for all operations.

    """
    input_data = input_prepper.input_parser
    with input_prepper.db_session() as db_session:
        if not is_pvadmin_connected_okrs(input_prepper):
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Not a pvadmin customer",
                        error_code="NOT_PVADMIN_CUSTOMER",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        claims = input_prepper.jwt_parser.payload.hasura_claims()
        default_role = claims.get("x-hasura-default-role")
        if default_role.lower() not in ["manage"]:
            return adapt_error_for_hasura(
                [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
                HTTPStatus.FORBIDDEN,
            )
        custom_attribute_settings = get_existing_custom_attributes_settings(
            db_session, input_prepper
        )
        if not custom_attribute_settings:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Custom attribute settings does not exists for this tenant group",
                        error_code="CUSTOM_ATTRIBUTE_SETTINGS_DOES_NOT_EXISTS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        input_data["last_updated_by"] = input_prepper.planview_user_id
        input_data["app_last_updated_by"] = input_prepper.user_id

        params = {
            k: input_data.get(k)
            for k in input_data.keys()
            if (k in CUSTOM_ATTRIBUTES_DB_FIELDS)
        }
        for p in params.keys():
            custom_attribute_settings.__setattr__(p, params[p])

        try:
            db_session.add(custom_attribute_settings)
            commit_db_session(db_session)
        except BaseException as e:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=f"Could not update custom attribute settings: {e}",
                        error_code="CANNOT_UPDATE_CUSTOM_ATTRIBUTE_SETTINGS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )
        return {"id": custom_attribute_settings.id}, HTTPStatus.OK


@prep_input
async def current_user_v2(request, body, input_prepper, applications):
    """Retrieve current user's roles information."""
    input_product_types = get_product_types(input_prepper) or []
    product_types = [sanitise_product_type(p) for p in input_product_types]
    apps = applications["apps"]
    product_types = get_product_types_for_connected_app(product_types)
    product_types = [p for p in product_types if p in apps]
    if not product_types:
        product_types = apps
    product_types = list(set(product_types))

    cum = CurrentUserManager(input_prepper)
    return cum.get_current_user_v2(product_types)


@prep_input
async def get_user_setting(request, body, input_prepper=None):
    """Insert User Settings."""
    usm = UserSettingsManager(input_prepper)
    return usm.get_user_setting()


@prep_input
async def insert_user_setting(request, body, input_prepper=None):
    """Insert User Settings."""
    usm = UserSettingsManager(input_prepper)
    return usm.insert_user_setting()


@prep_input
async def update_user_setting(request, body, input_prepper=None):
    """Update User Settings."""
    usm = UserSettingsManager(input_prepper)
    return usm.update_user_setting()


@prep_input
async def multi_level_okr(request, body, input_prepper):
    """Define the multi_level_query."""
    mlo = MultiLevelOKRManager(input_prepper)
    return mlo.fetch_multi_level_okr()


@prep_input
async def multi_level_okr_filter_lists(request, body, input_prepper):
    """Define the multi_level_query."""
    mlo = MultiLevelOKRListsManager(input_prepper)
    return mlo.fetch_multi_level_okr_filter_lists()


@prep_input
async def fetch_objectives(request, body, input_prepper):
    """Fetch all the objectives."""
    om = ObjectivesManager(input_prepper)
    return om.fetch_objectives()


@prep_input
async def fetch_objectives_by_wic_id(request, body, input_prepper):
    """Fetch all the objectives."""
    om = ObjectivesManager(input_prepper)
    return om.fetch_objectives_by_wic_id()


@prep_input
async def fetch_objective_by_id(request, body, input_prepper):
    """Fetch all the objectives."""
    om = ObjectivesManager(input_prepper)
    return om.fetch_objective_by_id()


@prep_input
async def update_roll_up_progress_configuration(request, body, input_prepper):
    """
    Update a configuration for rolling up progress percentage.

    Pre-conditions:
        1. Must be pvadmin user
        2. Must have manager role
    """
    with input_prepper.db_session() as db_session:
        if not is_pvadmin_connected_okrs(input_prepper):
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Not a pvadmin customer",
                        error_code="NOT_PVADMIN_CUSTOMER",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        claims = input_prepper.jwt_parser.payload.hasura_claims()
        default_role = claims.get("x-hasura-default-role")
        if default_role.lower() != "manage":
            return adapt_error_for_hasura(
                [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
                HTTPStatus.FORBIDDEN,
            )

        input_parser = input_prepper.input_parser
        # Get the setting
        manager = SettingsManager(
            org_id=input_prepper.org_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            db_session=db_session,
        )
        settings = manager.get_settings()
        if not settings:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Settings not exists for this tenant group",
                        error_code="SETTING_DOES_NOT_EXISTS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        # Update the roll_up_progress flag
        roll_up_progress_flag = input_parser.roll_up_progress
        settings.roll_up_progress = roll_up_progress_flag
        settings.last_updated_by = input_prepper.planview_user_id
        db_session.add(settings)
        commit_db_session(db_session)
        return {
            "id": settings.id,
            "roll_up_progress": settings.roll_up_progress,
        }, HTTPStatus.OK


@prep_input
async def fetch_key_results(request, body, input_prepper):
    """Fetch all the key results."""
    krm = KeyResultsManager(input_prepper)
    return krm.get_key_results()


@prep_input
async def get_activity_logs(request, body, input_prepper):
    """Fetch activity log."""
    key_result_id = input_prepper.input_parser.key_result_id
    objective_id = input_prepper.input_parser.objective_id
    if key_result_id:
        history_obj = KeyResultsActivityLogs(key_result_id, input_prepper)
    elif objective_id:
        history_obj = ObjectivesActivityLogs(objective_id, input_prepper)
    else:
        return []
    return history_obj.get_history()


@prep_input
async def get_level_config(request, body, input_prepper, applications):
    """Return only one latest level config."""
    with input_prepper.db_session() as db_session:
        manager = SettingsManager(
            org_id=input_prepper.org_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            db_session=db_session,
        )
        level_settings = manager.find_all()
        if not level_settings:
            return [], 200
        if len(level_settings) > 1:
            message = (
                f"Duplicate Settings : User {input_prepper.planview_user_id} Token: "
                f"org_id: {input_prepper.org_id} "
                f"- tenant_group_id: {input_prepper.tenant_group_id} "
                f"Original org_id - {input_prepper.org_id_original} "
                f"Original app_tenant_id - {input_prepper.app_tenant_id_original} "
                f"Original tenant_group_id - {input_prepper.tenant_group_id_original} "
            )
            for key, obj in enumerate(level_settings):
                message += (
                    f" DB {key}: tenant_id: {obj.tenant_id_str} - "
                    f"tenant_group_id_str {obj.tenant_group_id_str}"
                )
            print(message)
        else:
            message = (
                f"Single Setting : User {input_prepper.planview_user_id} Token: "
                f"org_id: {input_prepper.org_id} "
                f"- tenant_group_id: {input_prepper.tenant_group_id} "
                f"Original org_id - {input_prepper.org_id_original} "
                f"Original app_tenant_id - {input_prepper.app_tenant_id_original} "
                f"Original tenant_group_id - {input_prepper.tenant_group_id_original} "
            )
            level_setting = level_settings[0]
            message += (
                f" Single Settings DB : tenant_id: {level_setting.tenant_id_str} - "
                f"tenant_group_id_str {level_setting.tenant_group_id_str}"
            )
            print(message)

    return [{"level_config": level_settings[0].level_config}], 200


@prep_input
async def update_is_color_threshold_enabled_flag(request, body, input_prepper):
    """
    Update a configuration for use color threshold flag.

    Pre-conditions:
        1. Must be pvadmin user
        2. Must have manager role
    """
    with input_prepper.db_session() as db_session:
        if not is_pvadmin_connected_okrs(input_prepper):
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Not a pvadmin customer",
                        error_code="NOT_PVADMIN_CUSTOMER",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        claims = input_prepper.jwt_parser.payload.hasura_claims()
        default_role = claims.get("x-hasura-default-role")
        if default_role.lower() != "manage":
            return adapt_error_for_hasura(
                [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
                HTTPStatus.FORBIDDEN,
            )

        input_parser = input_prepper.input_parser
        # Get the setting
        manager = SettingsManager(
            org_id=input_prepper.org_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            db_session=db_session,
        )
        settings = manager.get_settings()
        if not settings:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Settings does not exist",
                        error_code="SETTING_DOES_NOT_EXISTS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        # Update the use_color_threshold flag
        is_color_threshold_enabled = input_parser.is_color_threshold_enabled
        settings.is_color_threshold_enabled = is_color_threshold_enabled
        settings.last_updated_by = input_prepper.planview_user_id
        db_session.add(settings)
        commit_db_session(db_session)
        return {
            "id": settings.id,
            "is_color_threshold_enabled": settings.is_color_threshold_enabled,
        }, HTTPStatus.OK


@prep_input
async def update_color_threshold_config(request, body, input_prepper):
    """
    Update a configuration for the thresholds set.

    Pre-conditions:
        1. Must be pvadmin user
        2. Must have manager role
    """
    with input_prepper.db_session() as db_session:
        if not is_pvadmin_connected_okrs(input_prepper):
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Not a pvadmin customer",
                        error_code="NOT_PVADMIN_CUSTOMER",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        claims = input_prepper.jwt_parser.payload.hasura_claims()
        default_role = claims.get("x-hasura-default-role")
        if default_role.lower() != "manage":
            return adapt_error_for_hasura(
                [dict(message="Not an admin user", error_code="NOT_MANAGE_ROLE")],
                HTTPStatus.FORBIDDEN,
            )

        input_parser = input_prepper.input_parser
        # Get the setting
        manager = SettingsManager(
            org_id=input_prepper.org_id,
            tenant_group_id=input_prepper.tenant_group_id,
            created_by=input_prepper.planview_user_id,
            db_session=db_session,
        )
        settings = manager.get_settings()
        if not settings:
            return adapt_error_for_hasura(
                [
                    dict(
                        message="Settings does not exist",
                        error_code="SETTING_DOES_NOT_EXISTS",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        # Update the use_color_threshold flag
        color_threshold_config = input_parser.input
        validator_response = manager.validate_color_threshold_config(
            color_threshold_config
        )
        if not validator_response["success"]:
            return adapt_error_for_hasura(
                [
                    dict(
                        message=validator_response["errors"],
                        error_code="INVALID_COLOR_THRESHOLD_CONFIGURATION",
                    )
                ],
                HTTPStatus.BAD_REQUEST,
            )

        settings.color_threshold_config = color_threshold_config
        settings.last_updated_by = input_prepper.planview_user_id
        db_session.add(settings)
        commit_db_session(db_session)
        return {
            "is_color_threshold_enabled": settings.is_color_threshold_enabled,
            "color_threshold_config": color_threshold_config,
        }, HTTPStatus.OK


@prep_input
async def delete_work_item_containers(request, body, input_prepper):
    """Delete work item containers."""
    wic_ids = []
    try:
        wic_manager = WorkItemContainersManager(input_prepper)
        wic_ids = input_prepper.input_parser.external_ids
        container_type = input_prepper.input_parser.container_type
        deleted_wics = wic_manager.delete_work_item_container_entities(
            wic_ids, container_type
        )
        return {
            "deleted_wics": deleted_wics,
        }, HTTPStatus.OK
    except Exception as e:
        print(
            f"Error deleting work item container:{input_prepper.tenant_group_id, wic_ids , str(e)}"
        )
        return internal_server_error("Error deleting work item container")


@prep_input
async def activity_associated_okrs(request, body, input_prepper):
    """Retrieve a list of Objectives, Key Results associated with a given activity."""
    try:
        activity_ids = input_prepper.input_parser.activity_ids
        container_type = input_prepper.input_parser.container_type
        manager = ActivityOKRManager(activity_ids, container_type, input_prepper)
        return manager.get_objectives_and_key_results(), HTTPStatus.OK
    except ValueError as e:
        return bad_request_error(str(e), "CANNOT_FETCH_OKRS_ASSOCIATED_WITH_ACTIVITIES")
    except Exception as e:
        print(f"Error retrieving objectives and key results for activity: {str(e)}")
        return internal_server_error("Error fetching OKRs associated with activities")
