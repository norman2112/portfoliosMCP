"""Module for cron jobs."""

from datetime import datetime, timedelta
from http import HTTPStatus

from connexion import NoContent
from open_alchemy import models


WIC_CONTAINER_EXPIRATION_DAYS = 30


# noqa: E711
# pylint:disable=W0613,C0121
async def reregister_tenants(request, body):
    """
    Re-provision tenants and re-subscribe WorkItems with Integration Hub.

    Also re-register all the work items.
    Will accept the following body:

    .. code-block:

        {
            "payload": {
                global_tenant_ids: [str],
                tenant_ids: [str],
            }
        }


    `global_tenant_ids` are gtids in the Settings record.
    `tenant_id` are `tenant_id_str` in the Settings record.
    """

    # This step is no longer valid and for the time being not required.
    # The method is still called but it immediately returns True marking it completed.
    # The files are kept because in future we may want to go for another queuing system
    # in which case we may need it again.

    return NoContent, HTTPStatus.OK


# noqa: E711
# pylint:disable=W0613,C0121
async def delete_work_item_container_orphans(request, body):
    """
    Delete expired orphaned WorkItemContainers.

    After 7 days from the last update, the WorkItemContainer is eligible to be
    deleted if it is orphaned.
    An orphaned WorkItemContainer has no WorkItems or Objectives attached to
    it.
    """
    expiration_date = datetime.now() - timedelta(days=WIC_CONTAINER_EXPIRATION_DAYS)
    with request.app["db_session"]() as db_session:
        wic_tuples = (
            db_session.query(models.WorkItemContainer.id)
            .distinct()
            .outerjoin(models.WorkItem, models.Objective)
            .filter(models.WorkItem.work_item_container_id == None)  # noqa: E711
            .filter(models.Objective.id == None)  # noqa: E711
            .filter(models.WorkItemContainer.updated_at < expiration_date)
            .all()
        )
        # Note: the comma, because we're grabbing the value from tuples, because..
        # python.
        wic_ids = [value for value, in wic_tuples]

        db_session.query(models.WorkItemContainer).filter(
            models.WorkItemContainer.id.in_(wic_ids)
        ).delete()
        _commit_db_session(db_session)

    return NoContent, HTTPStatus.OK


# pylint:enable=W0613,C0121


def _commit_db_session(db_session):
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
