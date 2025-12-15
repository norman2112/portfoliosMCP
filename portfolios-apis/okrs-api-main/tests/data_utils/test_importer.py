"""Test the importer functions."""

import json
from pathlib import Path

from open_alchemy import models
import pytest
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import InternalError

from okrs_api.data_utils.importer import attribs_diff, DataImporter, ImportLogger


ADAPTED_MANIFEST_FILE = (
    Path(__file__).parent / "manifests" / "adapted_test_manifest.json"
)

ADAPTED_MANIFEST_FILE_2 = (
    Path(__file__).parent / "manifests" / "adapted_test_manifest_2.json"
)

ADAPTED_MANIFEST_FILE_3 = (
    Path(__file__).parent / "manifests" / "adapted_test_manifest_3.json"
)


class TestDataImporter:
    """Test the data importer and that triggers are disabled properly."""

    ORIGINAL_TENANT_ID_STR = "LEANKIT~d12-123"
    NEW_TENANT_ID_STR = "LEANKIT~d999-111"

    @pytest.fixture()
    def data_importer(self):
        """Initialize the data importer."""

        def _data_importer(db_session_instance):
            adapted_manifest_file = open(ADAPTED_MANIFEST_FILE, "+r")
            return DataImporter(
                db_session_instance, adapted_manifest_file, self.NEW_TENANT_ID_STR
            )

        return _data_importer

    @pytest.fixture(scope="function")
    def new_db_connection(self, db_settings):
        """Create a database connection to the engine specified in settings."""
        db_settings_dict = db_settings.engine.dict()
        db_url = db_settings_dict.pop("name_or_url")
        engine = create_engine(db_url, **db_settings_dict)
        connection = engine.connect()
        yield connection
        connection.close()

    @pytest.fixture()
    def db_session_triggers_disabled(self, new_db_connection):
        """
        Return a db_session with a new database engine.

        The new database engine represents a separate connection to the
        postgres database.

        This new engine/connection will have triggers disabled.

        https://docs.sqlalchemy.org/en/14/core/connections.html
        """
        transaction = new_db_connection.begin()

        with new_db_connection.connect() as con:
            con.execute("SET session_replication_role = replica;")
            db_session = sqlalchemy.orm.scoped_session(
                sqlalchemy.orm.sessionmaker(bind=new_db_connection)
            )
            yield db_session
            db_session.close()
        transaction.rollback()

    @pytest.mark.integration
    def test_import_data(self, db_session_triggers_disabled, data_importer):
        """
        Ensure data is imported correctly.

        The data we are importing would be exported from the origin install of
        okrs-api.
        """
        with db_session_triggers_disabled() as db_session_instance:
            log_data = data_importer(
                db_session_instance=db_session_instance
            ).apply_adapted_manifest()
            new_progress_point = (
                db_session_instance.query(models.ProgressPoint)
                .filter_by(tenant_id_str=self.NEW_TENANT_ID_STR)
                .first()
            )

            migration_log_entry = (
                db_session_instance.query(models.TenantMigrationLog)
                .filter_by(
                    new_tenant_id_str=self.NEW_TENANT_ID_STR,
                    original_tenant_id_str=self.ORIGINAL_TENANT_ID_STR,
                    success=True,
                    message="IMPORT",
                )
                .first()
            )

        old_work_item_container_id = log_data["WorkItemContainer"][0]["original"]["id"]
        new_work_item_container_id = log_data["WorkItemContainer"][0]["new"]["id"]

        assert (
            log_data["WorkItem"][0]["original"]["work_item_container_id"]
            == old_work_item_container_id
        )
        assert (
            log_data["WorkItem"][0]["new"]["work_item_container_id"]
            == new_work_item_container_id
        )

        assert (
            log_data["WorkItemContainerRole"][0]["original"]["work_item_container_id"]
            == old_work_item_container_id
        )
        assert (
            log_data["WorkItemContainerRole"][0]["new"]["work_item_container_id"]
            == new_work_item_container_id
        )

        assert not log_data.get("ERRORS")
        assert (
            "imported 1 records of 1 in manifest"
            in log_data["SUMMARY"]["ProgressPoint"]
        )
        assert new_progress_point

    @pytest.mark.integration
    def test_trigger_reset_bleed(
        self, db_session, db_session_triggers_disabled, data_importer
    ):
        """
        Ensure that triggers are only effected for one engine/connection.
        """
        # Begin a new database connection/engine with the
        # `db_session_triggers_disabled` fixture. This returns an SQA session
        # object that can be initialized as a new SQL session object.
        with db_session_triggers_disabled() as db_session_instance1:
            data_importer(
                db_session_instance=db_session_instance1
            ).apply_adapted_manifest()

        # Meanwhile, use the same database connection/engine that the app
        # will already be using to attempt to perform a database operation
        # that would cause an error due to triggers.
        with db_session() as db_session_instance2:
            wic = models.WorkItemContainer(
                external_id="test-abc-123",
                external_type="leankit",
                external_title="Test WIC - should fail by trigger",
                app_last_updated_by="123456789",
                objective_editing_levels=[0, 4],
            )
            with pytest.raises(InternalError) as e:
                db_session_instance2.add(wic)
                db_session_instance2.commit()

            assert (
                "objective_editing_levels and level_depth_default must both be null on insert"
                in str(e.value)
            )


class TestDataImporterWithD09Data:
    """Test the data importer and that triggers are disabled properly."""

    ORIGINAL_TENANT_ID_STR = "LEANKIT~d09-10146315773"
    NEW_TENANT_ID_STR = "LEANKIT~i01-10146315773"
    NEW_TENANT_GROUP_ID_STR = "uuiduuiduuiduuiduuid12233"

    @pytest.fixture()
    def data_importer(self):
        """Initialize the data importer."""

        def _data_importer(db_session_instance):
            adapted_manifest_file = open(ADAPTED_MANIFEST_FILE_2, "+r")
            return DataImporter(
                db_session_instance,
                adapted_manifest_file,
                self.NEW_TENANT_ID_STR,
                new_tenant_group_id_str=self.NEW_TENANT_GROUP_ID_STR,
            )

        return _data_importer

    @pytest.fixture(scope="function")
    def new_db_connection(self, db_settings):
        """Create a database connection to the engine specified in settings."""
        db_settings_dict = db_settings.engine.dict()
        db_url = db_settings_dict.pop("name_or_url")
        engine = create_engine(db_url, **db_settings_dict)
        connection = engine.connect()
        yield connection
        connection.close()

    @pytest.fixture()
    def db_session_triggers_disabled(self, new_db_connection):
        """
        Return a db_session with a new database engine.

        The new database engine represents a separate connection to the
        postgres database.

        This new engine/connection will have triggers disabled.

        https://docs.sqlalchemy.org/en/14/core/connections.html
        """
        transaction = new_db_connection.begin()

        with new_db_connection.connect() as con:
            con.execute("SET session_replication_role = replica;")
            db_session = sqlalchemy.orm.scoped_session(
                sqlalchemy.orm.sessionmaker(bind=new_db_connection)
            )
            yield db_session
            db_session.close()
        transaction.rollback()

    @pytest.mark.integration
    def test_import_data(self, db_session_triggers_disabled, data_importer):
        """
        Ensure data is imported correctly.

        The data we are importing would be exported from the origin install of
        okrs-api.
        """
        with db_session_triggers_disabled() as db_session_instance:
            log_data = data_importer(
                db_session_instance=db_session_instance
            ).apply_adapted_manifest()

            migration_log_entry = (
                db_session_instance.query(models.TenantMigrationLog)
                .filter_by(
                    new_tenant_id_str=self.NEW_TENANT_ID_STR,
                    original_tenant_id_str=self.ORIGINAL_TENANT_ID_STR,
                    success=True,
                    message="IMPORT",
                )
                .first()
            )

        assert migration_log_entry
        assert not log_data.get("ERRORS")
        old_group_id = log_data["Objective"][0]["original"]["tenant_group_id_str"]
        new_group_id = log_data["Objective"][0]["new"]["tenant_group_id_str"]
        assert old_group_id == "LEANKIT~d09-10146315773"
        assert new_group_id == self.NEW_TENANT_GROUP_ID_STR

    @pytest.mark.integration
    def test_trigger_reset_bleed(
        self, db_session, db_session_triggers_disabled, data_importer
    ):
        """
        Ensure that triggers are only effected for one engine/connection.
        """
        # Begin a new database connection/engine with the
        # `db_session_triggers_disabled` fixture. This returns an SQA session
        # object that can be initialized as a new SQL session object.
        with db_session_triggers_disabled() as db_session_instance1:
            data_importer(
                db_session_instance=db_session_instance1
            ).apply_adapted_manifest()

        # Meanwhile, use the same database connection/engine that the app
        # will already be using to attempt to perform a database operation
        # that would cause an error due to triggers.
        with db_session() as db_session_instance2:
            wic = models.WorkItemContainer(
                external_id="test-abc-123",
                external_type="leankit",
                external_title="Test WIC - should fail by trigger",
                app_last_updated_by="123456789",
                objective_editing_levels=[0, 4],
            )
            with pytest.raises(InternalError) as e:
                db_session_instance2.add(wic)
                db_session_instance2.commit()

            assert (
                "objective_editing_levels and level_depth_default must both be null on insert"
                in str(e.value)
            )


class TestDataImporterWithOldDeletedObjectiveData:
    """Test the data importer and that triggers are disabled properly."""

    ORIGINAL_TENANT_ID_STR = "LEANKIT~d09-10146315773"
    NEW_TENANT_ID_STR = "LEANKIT~i01-10146315773"
    NEW_TENANT_GROUP_ID_STR = "uuiduuiduuiduuiduuid12233"

    @pytest.fixture()
    def data_importer(self):
        """Initialize the data importer."""

        def _data_importer(db_session_instance):
            adapted_manifest_file = open(ADAPTED_MANIFEST_FILE_3, "+r")
            return DataImporter(
                db_session_instance,
                adapted_manifest_file,
                self.NEW_TENANT_ID_STR,
                new_tenant_group_id_str=self.NEW_TENANT_GROUP_ID_STR,
            )

        return _data_importer

    @pytest.fixture(scope="function")
    def new_db_connection(self, db_settings):
        """Create a database connection to the engine specified in settings."""
        db_settings_dict = db_settings.engine.dict()
        db_url = db_settings_dict.pop("name_or_url")
        engine = create_engine(db_url, **db_settings_dict)
        connection = engine.connect()
        yield connection
        connection.close()

    @pytest.fixture()
    def db_session_triggers_disabled(self, new_db_connection):
        """
        Return a db_session with a new database engine.

        The new database engine represents a separate connection to the
        postgres database.

        This new engine/connection will have triggers disabled.

        https://docs.sqlalchemy.org/en/14/core/connections.html
        """
        transaction = new_db_connection.begin()

        with new_db_connection.connect() as con:
            con.execute("SET session_replication_role = replica;")
            db_session = sqlalchemy.orm.scoped_session(
                sqlalchemy.orm.sessionmaker(bind=new_db_connection)
            )
            yield db_session
            db_session.close()
        transaction.rollback()

    @pytest.mark.integration
    def test_import_data(self, db_session_triggers_disabled, data_importer):
        """
        Ensure data is imported correctly.

        The data we are importing would be exported from the origin install of
        okrs-api.
        """
        with db_session_triggers_disabled() as db_session_instance:
            log_data = data_importer(
                db_session_instance=db_session_instance
            ).apply_adapted_manifest()

        assert not log_data.get("ERRORS")
        assert log_data.get("WARNINGS")
        assert log_data["WARNINGS"][0]["model"] == "ActivityLog"
        assert log_data["WARNINGS"][0]["attribs"]["objective_id"] is None
        old_group_id = log_data["Objective"][0]["original"]["tenant_group_id_str"]
        new_group_id = log_data["Objective"][0]["new"]["tenant_group_id_str"]
        assert old_group_id == "LEANKIT~d09-10146315773"
        assert new_group_id == self.NEW_TENANT_GROUP_ID_STR


class TestImportLogger:
    """Test the import logger."""

    ORIGINAL_ATTRIBS = {"value": 10, "key_result_id": 1, "app_last_updated_by": 1}
    NEW_ATTRIBS = {"value": 10, "key_result_id": 30, "app_last_updated_by": 100}

    @pytest.fixture()
    def import_logger(self):
        """Log some sample attributes"""
        logger = ImportLogger()
        logger.log("progress_point", self.ORIGINAL_ATTRIBS, self.NEW_ATTRIBS)
        return logger

    def test_log(self, import_logger):
        """Ensure that the normal logging works as expected."""

        first_entry = import_logger.import_logs["progress_point"][0]
        first_entry_keys = list(first_entry.keys())
        assert first_entry_keys == ["original", "new", "diff"]
        assert first_entry["new"]["app_last_updated_by"] == 100
        assert "value" not in first_entry["diff"]
        assert "key_result_id" in first_entry["diff"]

    def test_log_error(self):
        """Ensure that the logger can log errors."""
        logger = ImportLogger()
        logger.log_error(
            message="An occurred", model_name="ProgressPoint", attribs=self.NEW_ATTRIBS
        )
        errors = logger.errors()
        assert len(errors) == 1
        assert errors[0]["model"] == "ProgressPoint"

    def test_log_serializable(self, import_logger):
        """Ensure that the log can be serializable to JSON."""
        json_log = json.dumps(import_logger.import_logs)
        assert json_log


class TestAttribsDiff:
    ORIGINAL_ATTRIBS = {"value": 10, "key_result_id": 1, "app_last_updated_by": 1}
    NEW_ATTRIBS = {"value": 10, "key_result_id": 30, "app_last_updated_by": 100}

    def test_attribs_diff(self):
        """Ensure that the attrib differences ar presented properly."""
        diff = attribs_diff(self.ORIGINAL_ATTRIBS, self.NEW_ATTRIBS)
        assert type(diff) == dict
        assert "key_result_id" in diff.keys()
        assert "app_last_updated_by" in diff.keys()
        assert "value" not in diff.keys()
        assert diff["app_last_updated_by"] == "100"
