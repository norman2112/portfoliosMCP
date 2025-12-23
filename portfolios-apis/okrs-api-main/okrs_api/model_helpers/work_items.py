"""Helpers for WorkItems-related needs."""

from datetime import datetime, timezone

from open_alchemy import models

from okrs_api.api.controller.helpers import sanitise_product_type
from okrs_api.model_helpers.common import find_or_build


class WorkItemCreator:
    """
    Create a work item and its mappings from params.

    A Work Item is an abstraction of an external Activity (e.g. a Leankit Card).
    This is used to create a WorkItem after an Activity has been created.

    This creator takes in an InputParser, which contains relevant data for
    creating a WorkItem. It also takes in WorkItem attributes that may come
    as a return value from the service that created the activity.

    Between these two sets of data, the WorkItemCreator will be able to
    create a WorkItem.
    """

    def __init__(self, work_item_attribs, input_parser, db_session):
        """
        Initialize params to create work item.

        :param dict work_item_attribs: attribs used to create the work item
        :param InputParser input_parser: a parser of base class InputParser
        :param Session db_session: a SQLAlchemy session

        Details:
        `work_item_attribs` represents attributes that were adapted and returned
        from the external api service.
        This dict must contain an `external_id` and a `tenant_id_str`
        """
        self.work_item_attribs = work_item_attribs or {}
        self.parser = input_parser
        self.db_session = db_session
        self._work_item = None

    def create(self):
        """Create the WorkItem and its mapping."""
        wic = self._get_or_create_wic()

        work_item = models.WorkItem(**self._work_item_dict)  # pylint: disable=no-member
        work_item.work_item_container = wic
        work_item_mapping = (
            models.KeyResultWorkItemMapping(  # pylint: disable=no-member
                work_item=work_item,
                key_result_id=self.parser.key_result_id,
                tenant_id_str=self._tenant_id_str,
                tenant_group_id_str=self._tenant_group_id_str,
                created_by=self._created_by,
                app_created_by=self._app_created_by,
            )
        )

        self.db_session.add_all([wic, work_item, work_item_mapping])
        #   try to commit
        try:
            self.db_session.commit()
            self._work_item = work_item
            return work_item
        except:  # noqa: E722
            self.db_session.rollback()
            raise

    def _get_or_create_wic(self):
        wic = find_or_build(
            db_session=self.db_session,
            model=models.WorkItemContainer,
            build_params={
                "external_title": self.parser.context_title,
                "tenant_id_str": self._tenant_id_str,
                "tenant_group_id_str": self._tenant_group_id_str,
                "created_by": self._created_by,
                "app_created_by": self._app_created_by,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            external_id=self.parser.context_id,
            external_type=sanitise_product_type(self.parser.product_type),
            tenant_id_str=self._tenant_id_str,
        )
        # Set the tenant_id on the wic in case it doesn't exist
        wic.tenant_id_str = wic.tenant_id_str or self._tenant_id_str
        wic.tenant_group_id_str = wic.tenant_group_id_str or self._tenant_group_id_str
        return wic

    @property
    def _external_id(self):
        """Return the id of the activity from the work_item_attribs."""
        return self.work_item_attribs.get("external_id")

    @property
    def _tenant_id_str(self):
        """Return the tenant_id_str from the work_item_attribs."""
        return self.work_item_attribs.get("tenant_id_str")

    @property
    def _tenant_group_id_str(self):
        """Return the tenant_group_id_str from the work_item_attribs."""
        return self.work_item_attribs.get("tenant_group_id_str")

    @property
    def _item_type(self):
        """
        Return the type of this work item.

        This comes from the external creation of the activity.
        """
        return self.work_item_attribs.get("item_type")

    @property
    def _app_name(self):
        """Return the app name."""
        return self.work_item_attribs.get("app_name")

    @property
    def _created_by(self):
        """Return the planview user id."""
        return self.work_item_attribs.get("created_by")

    @property
    def _app_created_by(self):
        """Return the app user id."""
        return self.work_item_attribs.get("app_created_by")

    @property
    def _work_item_dict(self):
        return {
            "title": self.work_item_attribs.get("title"),
            "external_type": sanitise_product_type(self.parser.product_type),
            "external_id": self._external_id,
            "item_type": self._item_type,
            "state": "not_started",
            "planned_start": self.work_item_attribs.get("planned_start"),
            "planned_finish": self.work_item_attribs.get("planned_finish"),
            "tenant_id_str": self._tenant_id_str,
            "tenant_group_id_str": self._tenant_group_id_str,
            "created_by": self._created_by,
            "app_created_by": self._app_created_by,
            "app_name": self._app_name,
            "container_type": self.work_item_attribs.get("container_type"),
        }
