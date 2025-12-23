"""Common classes and functions for models."""

from datetime import date, datetime
import json

from sqlalchemy.inspection import inspect
from open_alchemy import models
from okrs_api.model_helpers.deleter import Deleter


def dictify_model(model_instance, attrib_names=None):
    """
    Extract the provided attribute names from a model instance.

    :params model model_instance: an SqlAlchemy ORM model instance
    :param list attrib_names: list of attribute names to extract

    If `attrib_names` is None, will return all column attribs.
    """
    inspect_attribs = dict(inspect(model_instance).mapper.column_attrs)
    attrib_names = attrib_names or inspect_attribs.keys()
    full_dict = model_instance.to_dict()
    return {name: full_dict.get(name) for name in attrib_names}


def dictify_model_for_json(model_instance, attrib_names=None):
    """
    Extract the provided attribute names from a model instance ready for json.

    :params model model_instance: an SqlAlchemy ORM model instance
    :param list attrib_names: list of attribute names to extract

    If `attrib_names` is None, will return all column attribs.
    Will also json dump and load the object to ensure json compatibility.
    """
    inspect_attribs = dict(inspect(model_instance).mapper.column_attrs)
    attrib_names = attrib_names or inspect_attribs.keys()
    full_dict = model_instance.__dict__
    final_dict = {name: full_dict.get(name) for name in attrib_names}
    json_data = json.dumps(final_dict, default=default_json_converter)
    return json.loads(json_data)


def default_json_converter(obj):
    """
    Convert a special-case object to json.

    `json.dumps` does not always have a way to convert all python types (like
    datetime instances, for example). By providing this function to the
    `default` parameter of `json.dumps`, we can let this do the additional
    conversion necessary.
    """
    if isinstance(obj, (datetime, date)):
        return obj.__str__()

    raise Exception("Cannot convert to json")


def clone_model_instance(model_instance):
    """
    Clone a model instance, minus unnecessary fields.

    We remove `id` and the `_sa_instance_state` when we clone.
    """
    attribs = dict(model_instance.__dict__)
    attribs.pop("id")  # get rid of id
    attribs.pop("_sa_instance_state")  # get rid of SQLAlchemy special attr
    return model_instance.__class__(**attribs)


def find_or_build(db_session, model, build_params=None, **kwargs):
    """Find an instance of a model, given its parameters, or build one."""
    instance = db_session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance

    kwargs |= build_params or {}
    return model(**kwargs)


def commit_db_session(db_session):
    """Commit the database session and rollback if there are problems."""
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e


def clean_wi_and_kr_wi_mapping(input_prepper, deleted_cards):
    """Remove wi and kr_wi mappings for deleted cards."""
    if input_prepper.db_session is not None:
        product_type = input_prepper.input_parser.product_type
        if product_type is None:
            product_type = input_prepper.app_name
        with input_prepper.db_session() as db_session:
            work_items = (
                db_session.query(models.WorkItem)
                .filter(models.WorkItem.external_id.in_(deleted_cards))
                .filter_by(external_type=product_type)
                .all()
            )
            key_result_wi_mappings = (
                db_session.query(models.KeyResultWorkItemMapping)
                .filter(
                    models.KeyResultWorkItemMapping.work_item_id.in_(
                        [wi.id for wi in work_items]
                    )
                )
                .all()
            )
            for ke_wi_map in key_result_wi_mappings:
                deleter = Deleter(db_session=db_session, model_instance=ke_wi_map)
                deleter.delete()
            for wi in work_items:

                deleter = Deleter(db_session=db_session, model_instance=wi)
                deleter.delete()

            commit_db_session(db_session)


def add_tenant_and_user_fields(params, input_prepper, add_pv_fields=False):
    """Add tenant and user id fields."""
    tenant_id_str = input_prepper.org_id
    tenant_group_id_str = input_prepper.tenant_group_id

    planview_user_id = input_prepper.planview_user_id
    app_user_id = input_prepper.user_id

    pv_tenant_id = tenant_group_id_str if tenant_group_id_str else tenant_id_str
    pv_created_by = planview_user_id if planview_user_id else app_user_id
    pv_last_updated_by = planview_user_id if planview_user_id else app_user_id

    params.update(
        dict(
            tenant_id_str=tenant_id_str,
            tenant_group_id_str=tenant_group_id_str,
            app_created_by=app_user_id,
            created_by=planview_user_id,
            app_last_updated_by=app_user_id,
            last_updated_by=planview_user_id,
        )
    )
    if add_pv_fields:
        params.update(
            dict(
                pv_tenant_id=pv_tenant_id,
                pv_created_by=pv_created_by,
                pv_last_updated_by=pv_last_updated_by,
            )
        )
    return params


def set_last_updated_by_fields(obj, input_prepper, add_pv_fields=False):
    """Update last_updated fields."""
    obj.last_updated_by = input_prepper.planview_user_id
    obj.app_last_updated_by = input_prepper.user_id
    if add_pv_fields:
        obj.pv_last_updated_by = (
            obj.last_updated_by if obj.last_updated_by else obj.app_last_updated_by
        )
    return obj
