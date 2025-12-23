"""Module for true deletion of a tenant from OKRs."""

from sqlalchemy.sql import text

from open_alchemy import models

from okrs_api.model_helpers.common import commit_db_session


class Eradicator:
    """Used to completely remove all data belonging to a tenant."""

    DELETION_TABLES = [
        "settings",
        "work_item_containers",
        "objectives",
        "key_results",
        "key_result_work_item_mappings",
        "progress_points",
        "work_items",
        "activity_logs",
        "work_item_container_roles",
    ]

    @classmethod
    def delete_tenant(cls, db_session, tenant_id_str):
        """Delete all a tenant's records from OKRs permanently."""
        engine = db_session.get_bind()
        with engine.connect() as con:
            for table in cls.DELETION_TABLES:
                stmt = text(f"DELETE FROM {table} WHERE tenant_id_str = :tenant_id_str")
                con.execute(stmt, {"table": table, "tenant_id_str": tenant_id_str})

        cls._log_deletion_attempt(db_session, tenant_id_str)

    @classmethod
    def _log_deletion_attempt(cls, db_session, tenant_id_str):
        """Log the deletion attempt in the tenant migration table."""
        log = models.TenantMigrationLog(
            message="DELETE",
            original_tenant_id_str=tenant_id_str,
            success=True,
        )
        db_session.add(log)
        commit_db_session(db_session)
