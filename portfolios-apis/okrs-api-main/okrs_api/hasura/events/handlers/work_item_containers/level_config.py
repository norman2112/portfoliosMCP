"""Event handler for all WorkItemContainer operations."""

from open_alchemy import models
from sqlalchemy import or_

from okrs_api.hasura.events.handlers.base import Base


class Handler(Base):
    """Handler for the WorkItemContainer operations."""

    def insert_event(self):
        """
        Perform code related to an INSERT.

        Create a `setting` record for the organization, if one does not
        already exist.
        """
        if self._find_setting():
            return True

        self.db_session.add(
            models.Setting(
                tenant_id_str=self.tenant_id_str,
                tenant_group_id_str=self.tenant_group_id_str,
            )
        )
        return self._commit_db_session()

    @property
    def tenant_id_str(self):
        """Return the `tenant_id_str` that was passed in."""
        return self.event_parser.find_value_for_key("tenant_id_str")

    @property
    def tenant_group_id_str(self):
        """Return the `tenant_group_id_str` that was passed in."""
        return self.event_parser.find_value_for_key("tenant_group_id_str")

    def _find_setting(self):
        """Look for an existing level config, based on the tenant_id_str."""
        return (
            self.db_session.query(models.Setting)
            .filter(
                or_(
                    models.Setting.tenant_group_id_str == self.tenant_group_id_str,
                    models.Setting.tenant_id_str == self.tenant_id_str,
                )
            )
            .one_or_none()
        )
