"""Helpers for Activity Connection-related needs."""

from open_alchemy import models
from sqlalchemy import and_
from sqlalchemy import or_

from okrs_api.model_helpers.common import find_or_build
from okrs_api.model_helpers.settings import LevelConfigParser
from okrs_api.utils import utc_timestamp


class ActivitiesConnectionCreator:
    """
    Connects Work Items to a Key result.

    Responsibilities:

    1. Create key_result_work_item_mappings, connecting multiple work items
        to a key result.
    2. Create a WorkItem container for the work item(s) if it doesn't already
        exist.
    3. Return the KeyResultWorkItemMappings
    """

    def __init__(
        self,
        db_session,
        input_parser,
        org_id,
        tenant_group_id,
        created_by,
        user_id,
        **kwargs,
    ):
        """
        Initialize params to create work item.

        :param Session db_session: a SQLAlchemy session
        :param InputParser input_parser: the InputParser for this request
        :param str org_id: the org_id, which may be used as tenant_id_str
        :param str created_by: the planview user_id
        :param str user_id: the app user_id
        """
        self.db_session = db_session
        self.input_parser = input_parser
        self.org_id = org_id
        self.tenant_group_id = tenant_group_id
        self.created_by = created_by
        self.user_id = user_id
        self.app_name = kwargs.get("app_name", None)
        self.is_pvadmin = kwargs.get("is_pvadmin", False)
        # For memoization
        self._setting = None
        self._kr_wi_mappings = []

    def connect(self):
        """Connect a key result to work item(s)."""

        # Get or create the WorkItemContainer that will be associated with
        # all work items in this function.
        wic = self._get_or_build_wic()

        self.db_session.add(wic)

        for wi_data in self.input_parser.work_items:
            wi = self._get_or_build_wi(wi_data)
            # Updating the values of the work item from the work item input.
            self._update_wi_values(wi, wi_data)

            # Append the work items to the work item container
            wic.work_items.append(wi)

            # Get or build the KeyResultWorkItemMapping
            mapping = self._get_kr_wi_mapping(wi, self.input_parser.key_result_id)
            if not mapping:
                mapping = models.KeyResultWorkItemMapping(
                    key_result_id=self.input_parser.key_result_id,
                    tenant_id_str=self.org_id,
                    tenant_group_id_str=self.tenant_group_id,
                    created_by=self.created_by,
                    app_created_by=self.user_id,
                    created_at=utc_timestamp(),
                )
                wi.key_result_work_item_mappings.append(mapping)
            self._kr_wi_mappings.append(mapping)

        self._commit_db_session()
        return self._kr_wi_mappings

    def setting(self):
        """
        Return the settings record for this tenant_id_str.

        Memoize the result.
        """
        if not self._setting:
            self._setting = (
                self.db_session.query(models.Setting)
                .filter(
                    or_(
                        and_(
                            models.Setting.tenant_id_str == self.org_id,
                            models.Setting.tenant_id_str != "",
                        ),
                        models.Setting.tenant_group_id_str == self.tenant_group_id,
                    )
                )
                .first()
            )

        return self._setting

    def _get_default_level_depth(self):
        """
        Return the level depth of the default level.

        This is found in the Settings for this user.
        """
        if not self.setting():
            return None

        parser = LevelConfigParser(self.setting().level_config)
        return parser.default_depth()

    def _get_or_build_wic(self):
        """Find or build a new WorkItemContainer."""
        filter_params = {
            "external_id": self._work_item_container_data["external_id"],
            "external_type": self._work_item_container_data["external_type"],
        }
        if self.is_pvadmin:
            filter_params["tenant_group_id_str"] = self.tenant_group_id
        else:
            filter_params["tenant_id_str"] = self.org_id
        wic = find_or_build(
            db_session=self.db_session,
            model=models.WorkItemContainer,
            build_params={
                "tenant_id_str": self.org_id,
                "tenant_group_id_str": self.tenant_group_id,
                "created_by": self.created_by,
                "app_created_by": self.user_id,
                "created_at": utc_timestamp(),
                "external_title": self._work_item_container_data["external_title"],
                "level_depth_default": self._get_default_level_depth(),
                "app_name": self.app_name,
            },
            **filter_params,
        )
        # Set the org_id on the wic in case it doesn't exist
        wic.tenant_id_str = wic.tenant_id_str or self.org_id
        wic.tenant_group_id_str = wic.tenant_group_id_str or self.tenant_group_id
        return wic

    def _get_or_build_wi(self, wi_data):
        """Find or build a new WorkItem."""
        build_params = wi_data | {
            "tenant_id_str": self.org_id,
            "tenant_group_id_str": self.tenant_group_id,
            "created_by": self.created_by,
            "app_created_by": self.user_id,
            "app_name": self.app_name,
            "created_at": utc_timestamp(),
        }
        wi = find_or_build(
            db_session=self.db_session,
            model=models.WorkItem,
            build_params=build_params,
            external_type=wi_data["external_type"],
            external_id=wi_data["external_id"],
            container_type=wi_data["container_type"],
            tenant_id_str=self.org_id,
        )
        # Set the org_id on the wic in case it doesn't exist
        wi.tenant_id_str = wi.tenant_id_str or self.org_id
        wi.tenant_group_id_str = wi.tenant_group_id_str or self.tenant_group_id
        return wi

    def _get_kr_wi_mapping(self, wi, key_result_id):
        wi_mapping_model = models.KeyResultWorkItemMapping
        wi_mapping = (
            self.db_session.query(wi_mapping_model)
            .filter_by(
                work_item=wi,
                key_result_id=key_result_id,
            )
            .first()
        )

        if wi_mapping:
            # Set the org_id on the mapping in case it doesn't exist
            wi_mapping.tenant_id_str = wi_mapping.tenant_id_str or self.org_id
            wi_mapping.tenant_group_id_str = (
                wi_mapping.tenant_group_id_str or self.tenant_group_id
            )
        return wi_mapping

    @staticmethod
    def _update_wi_values(wi, wi_data):
        """Update each WorkItem with input data."""
        # Remove external properties as we will use real time API to fetch those
        updated_wi_data = wi_data
        for key, value in updated_wi_data.items():
            setattr(wi, key, value)

    @property
    def _work_item_container_data(self):
        """Return the attribs just for the work item container."""
        return {
            key: self.input_parser.work_item_container[key]
            for key in ["external_id", "external_type", "external_title"]
        }

    def _commit_db_session(self):
        """Commit the database session. Rollback on Error."""
        try:
            self.db_session.commit()
            return True
        except Exception as e:
            self.db_session.rollback()
            raise e
