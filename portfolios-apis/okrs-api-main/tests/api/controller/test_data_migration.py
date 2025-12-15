"""Test cron endpoints."""
import json
import os
from pathlib import Path

from open_alchemy import models
import pytest
import sqlalchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import close_all_sessions

from okrs_api.api.controller import data_migration


MANIFEST_DATA_FILE = (
    Path(__file__).parent.parent.parent
    / "data_utils"
    / "manifests"
    / "manifest_test_data.csv"
)

ADAPTED_MANIFEST_FILE = (
    Path(__file__).parent.parent.parent
    / "data_utils"
    / "manifests"
    / "adapted_test_manifest.json"
)


def manual_db_cleanup(engine):
    """
    Truncate all database tables.

    Normally we wrap our database usage in a transaction, that we can roll back
    easily later. BUT, in cases where the method we are testing creates its own
    brand new connection to the database (to bypass triggers for example), we
    have to clean up the database the old-fashioned way - truncate the data in
    the relevant tables.
    """
    close_all_sessions()
    metadata = MetaData()
    metadata.reflect(bind=engine)
    with engine.connect() as connection:
        for table in reversed(metadata.sorted_tables):
            if table.name != "alembic_version":
                connection.execute(
                    f"truncate table {table.name} restart identity cascade"
                )


class TestAdaptProductManifest:
    """Ensure that the manifest can be downloaded, converted, and uploaded."""

    TEST_BODY = {
        "payload": json.dumps(
            {
                "product_type": "leankit",
                "manifest_filename": "10127710376-10127710404-manifest.csv",
                "tenant_id_str": "LEANKIT~d09-1234",
            }
        )
    }

    @pytest.mark.integration
    async def test_adapt_product_manifest(self, mocker, request_with_db_session):
        """Ensure that the manifest is received by the controller."""
        mocker.patch(
            "okrs_api.api.controller.data_migration.ManifestConductor",
            return_value=mocker.Mock(
                download_product_manifest=mocker.Mock(
                    return_value=str(MANIFEST_DATA_FILE)
                ),
                upload_adapted_manifest=mocker.Mock(),
            ),
        )
        response_data, response_status = await data_migration.adapt_product_manifest(
            request_with_db_session, self.TEST_BODY, use_batch=False
        )
        assert "Setting" in response_data
        assert response_status == 200


class TestImportAdaptedManifest:
    TEST_BODY = {
        "payload": json.dumps(
            {
                "product_type": "leankit",
                "new_tenant_id_str": "LEANKIT~d999-111",
                "original_tenant_id_str": "LEANKIT~d09-1234",
            }
        )
    }

    def teardown_method(self):
        """
        Teardown the database.

        This must be done manually here as opposed to relying on the rollback
        of the db_session transaction. The method this is testing makes its own
        connection to the database.
        """
        engine = sqlalchemy.create_engine(os.environ["DATABASE_URL"])
        manual_db_cleanup(engine=engine)

    @pytest.mark.integration
    async def test_import_adapted_manifest(self, mocker, request_with_db_session):
        """Ensure that adapted manifest is imported by the controller."""
        mocker.patch(
            "okrs_api.api.controller.data_migration.ManifestConductor",
            return_value=mocker.Mock(
                download_adapted_manifest=mocker.Mock(
                    return_value=str(ADAPTED_MANIFEST_FILE)
                ),
            ),
        )
        response_data, response_status = await data_migration.import_adapted_manifest(
            request_with_db_session, self.TEST_BODY, use_batch=False
        )

        db_session = request_with_db_session.app["db_session"]
        new_objective_attribs = response_data["Objective"][0]["new"]
        found_new_objective = db_session.query(models.Objective).get(
            new_objective_attribs["id"]
        )

        assert found_new_objective.name == new_objective_attribs["name"]
        assert response_data["Setting"]
        assert not response_data.get("errors")
        assert response_status == 200
        db_session.close()


class TestDeleteOrganization:
    TEST_BODY = {
        "payload": json.dumps(
            {
                "tenant_id_str": "LEANKIT~d09-1234",
            }
        )
    }

    def teardown_method(self):
        """
        Teardown the database.

        This must be done manually here as opposed to relying on the rollback
        of the db_session transaction. The method this is testing makes its own
        connection to the database.
        """
        engine = sqlalchemy.create_engine(os.environ["DATABASE_URL"])
        manual_db_cleanup(engine=engine)

    @pytest.mark.integration
    async def test_delete_organization(
        self, request_with_db_session, progress_point_factory
    ):
        """Ensure that the organization is entirely deleted from the database."""
        db_session = request_with_db_session.app["db_session"]
        pp = progress_point_factory()
        tenant_id_str = pp.tenant_id_str
        db_session.commit()

        body = self._make_hasura_payload(tenant_id_str)
        await data_migration.delete_organization(
            request_with_db_session, body, use_batch=False
        )
        pp_count = (
            db_session.query(models.ProgressPoint)
            .filter_by(tenant_id_str=tenant_id_str)
            .count()
        )
        assert pp_count == 0

    def _make_hasura_payload(self, tenant_id_str):
        """Make a hasura payload that would come from Hasura."""
        return {
            "payload": json.dumps(
                {
                    "tenant_id_str": tenant_id_str,
                }
            )
        }
