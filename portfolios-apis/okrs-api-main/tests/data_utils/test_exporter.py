"""Test export utilities."""

import pytest

from inflection import underscore
from open_alchemy import models

from okrs_api.data_utils.exporter import ModelExporter, OrgExporter
from tests.factories.support.common import DEFAULT_TENANT_ID_STR


class TestModelExporter:
    DEFAULT_TENANT_ID_STR = "LEANKIT~d99-123"
    TEST_USER_ID_ENTRIES = [(100, 200), (300, 400)]

    @pytest.fixture
    def export_model(self):
        """Make an exporter out of the model."""

        def _export_model(
            db_session, model, factory, factory_attribs=None, manifest_entries=None
        ):
            factory_attribs = factory_attribs or {}
            manifest_entries = manifest_entries or {}
            factory_attribs["tenant_id_str"] = self.DEFAULT_TENANT_ID_STR
            db_instance = factory(**factory_attribs)
            db_session.commit()
            db_session.refresh(db_instance)

            exporter = ModelExporter(
                db_session=db_session,
                model=model,
                tenant_id_str=self.DEFAULT_TENANT_ID_STR,
                manifest_entries=manifest_entries,
            )
            export_log = exporter.export()
            first_attribs_pair = export_log[0]
            first_attribs_keys = first_attribs_pair["new"].keys()

            return {
                "db_instance": db_instance,
                "first_attribs_pair": first_attribs_pair,
                "first_attribs_keys": first_attribs_keys,
            }

        return _export_model

    @pytest.mark.parametrize(
        "model_name, expected_keys",
        [
            pytest.param(
                "Setting", {"level_config", "created_at", "updated_at"}, id="setting"
            ),
            pytest.param(
                "WorkItemContainer",
                {
                    "external_id",
                    "external_type",
                    "external_title",
                    "level_depth_default",
                    "objective_editing_levels",
                },
                id="wic",
            ),
            pytest.param(
                "Objective",
                {
                    "name",
                    "description",
                    "progress_percentage",
                    "level_depth",
                    "app_owned_by",
                    "parent_objective_id",
                },
                id="objective",
            ),
            pytest.param(
                "KeyResult",
                {
                    "name",
                    "description",
                    "starting_value",
                    "target_value",
                    "value_type",
                    "data_source",
                    "progress_percentage",
                    "objective_id",
                },
                id="key-result",
            ),
            pytest.param(
                "KeyResultWorkItemMapping",
                {"key_result_id", "work_item_id"},
                id="key-result-work-item-mapping",
            ),
            pytest.param(
                "ProgressPoint",
                {"value", "measured_at", "key_result_id"},
                id="progress-point",
            ),
            pytest.param(
                "WorkItem",
                {
                    "title",
                    "item_type",
                    "planned_start",
                    "planned_finish",
                    "external_type",
                    "external_id",
                    "state",
                    "work_item_container_id",
                },
                id="work-item",
            ),
            pytest.param(
                "ActivityLog",
                {
                    "action",
                    "info",
                    "work_item_id",
                    "objective_id",
                    "progress_point_id",
                    "key_result_id",
                },
                id="activity-log",
            ),
        ],
    )
    @pytest.mark.integration
    def test_models_export(
        self, export_model, db_session, request, model_name, expected_keys
    ):
        """Test export of relevant models."""
        expected_keys = expected_keys | {
            "id",
            "created_at",
            "updated_at",
            "tenant_id_str",
        }
        model = getattr(models, model_name)
        factory = request.getfixturevalue(f"{underscore(model_name)}_factory")
        export = export_model(db_session, model, factory)

        assert len(export["first_attribs_pair"].keys()) == 2
        assert export["first_attribs_pair"]["old"]
        assert export["first_attribs_pair"]["new"]
        assert expected_keys.issubset(export["first_attribs_keys"])

    @pytest.mark.parametrize(
        "factory_attribs, manifest_entries, expected_subset",
        [
            pytest.param(
                {"app_created_by": 100, "app_owned_by": 300},
                {
                    "app_created_by": TEST_USER_ID_ENTRIES,
                    "app_owned_by": TEST_USER_ID_ENTRIES,
                },
                {"app_created_by": 200, "app_owned_by": 400},
                id="app-ownership",
            ),
            pytest.param(
                {"app_owned_by": "300"},
                {
                    "app_created_by": TEST_USER_ID_ENTRIES,
                    "app_owned_by": TEST_USER_ID_ENTRIES,
                },
                {"app_created_by": None, "app_owned_by": "400"},
                id="app-ownership-blank-with-string",
            ),
            pytest.param(
                {"app_owned_by": 100},
                {
                    "app_created_by": TEST_USER_ID_ENTRIES,
                    "app_owned_by": TEST_USER_ID_ENTRIES,
                },
                {"app_owned_by": 100},
                id="no-change",
            ),
        ],
    )
    @pytest.mark.integration
    def test_export_with_manifest_entries(
        self,
        export_model,
        db_session,
        objective_factory,
        factory_attribs,
        manifest_entries,
        expected_subset,
    ):
        """Ensure that the manifest changes are made."""
        export = export_model(
            db_session,
            models.Objective,
            objective_factory,
            factory_attribs=factory_attribs,
            manifest_entries=manifest_entries,
        )

        assert set(expected_subset).issubset(set(export["first_attribs_pair"]["new"]))


class TestOrgExporter:
    TEST_MANIFEST_IDS = {
        "Setting": {
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
        },
        "WorkItemContainer": {
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
            "external_id": [("111", "333")],
        },
        "Objective": {
            "app_owned_by": [("222", "444")],
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
        },
        "KeyResult": {
            "app_owned_by": [("222", "444")],
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
        },
        "KeyResultWorkItemMapping": {
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
        },
        "ProgressPoint": {
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
        },
        "WorkItem": {
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
            "external_id": [("111", "222"), ("333", "444")],
        },
        "ActivityLog": {
            "app_created_by": [("222", "444")],
            "app_last_updated_by": [("222", "444")],
        },
    }

    @pytest.mark.integration
    def test_org_exporter(self, db_session, progress_point_factory, setting_factory):
        """Test that the org models are exported properly."""
        setting_factory()
        db_session.commit()
        progress_point = progress_point_factory(
            app_created_by=222, app_last_updated_by=222
        )
        db_session.commit()

        exporter = OrgExporter(
            db_session,
            tenant_id_str=DEFAULT_TENANT_ID_STR,
            manifest_ids=self.TEST_MANIFEST_IDS,
        )
        output = exporter.export()
        output_keys = list(output.keys())
        migration_log_entry = (
            db_session.query(models.TenantMigrationLog)
            .filter_by(
                new_tenant_id_str=None,
                original_tenant_id_str=DEFAULT_TENANT_ID_STR,
                success=True,
                message="EXPORT",
            )
            .first()
        )

        summary = output["SUMMARY"]
        assert migration_log_entry
        assert {"Objective", "ActivityLog", "KeyResult", "SUMMARY"}.issubset(
            set(output_keys)
        )
        assert "name" in list(output["Objective"][0]["new"].keys())
        assert summary["Objective"] == "exported 1 of 1 records"
        # Ensure that no changes were made to the progress point.
        reloaded_pp = db_session.query(models.ProgressPoint).get(progress_point.id)
        assert reloaded_pp.app_last_updated_by == "222"
        # Ensure that the output shows the change dictated by the manifest entries
        pp_entry = output["ProgressPoint"][0]
        assert pp_entry["old"]["app_created_by"] == "222"
        assert pp_entry["new"]["app_created_by"] == "444"

    @pytest.mark.integration
    def test_exporter_summary(
        self,
        db_session,
        objective_factory,
        work_item_container_factory,
        setting_factory,
    ):
        """Test that a tree of objectives is exported properly."""
        TENANT_ID_STR = "LEANKIT~d123-9999"
        setting_factory(tenant_id_str=TENANT_ID_STR)
        db_session.commit()
        wic = work_item_container_factory(tenant_id_str=TENANT_ID_STR)
        objective_factory(
            level_depth=3,
            tenant_id_str=TENANT_ID_STR,
            work_item_container=wic,
            name="Depth 3 Objective",
            parent_objective=objective_factory(
                tenant_id_str=TENANT_ID_STR,
                work_item_container=wic,
                level_depth=2,
                name="Depth 2 Objective",
                parent_objective=objective_factory(
                    tenant_id_str=TENANT_ID_STR,
                    work_item_container=wic,
                    level_depth=1,
                    name="Depth 1 Objective",
                    parent_objective=objective_factory(
                        tenant_id_str=TENANT_ID_STR,
                        work_item_container=wic,
                        name="Depth 0 Objective",
                        level_depth=0,
                    ),
                ),
            ),
        )
        db_session.commit()

        # begin test.
        exporter = OrgExporter(
            db_session,
            tenant_id_str=TENANT_ID_STR,
            manifest_ids=self.TEST_MANIFEST_IDS,
        )
        output = exporter.export()
        summary = output["SUMMARY"]
        assert summary["Objective"] == "exported 4 of 4 records"
