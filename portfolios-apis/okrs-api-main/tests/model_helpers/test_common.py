"""Test common model helper utilities."""

from datetime import datetime
import json

from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from open_alchemy import models
import pytest

from okrs_api.model_helpers.common import (
    find_or_build,
    dictify_model,
    dictify_model_for_json,
)


class TestFindOrBuild:
    """Ensure that finding or building a model works properly."""

    def test_build(self):
        """Ensure that we can build or find a model."""
        instance = find_or_build(
            UnifiedAlchemyMagicMock(),
            models.WorkItemContainer,
            build_params={"tenant_id_str": "test-tenant"},
            external_type="leankit",
            external_id="123",
        )

        assert instance.tenant_id_str == "test-tenant"
        assert instance.external_type == "leankit"
        assert instance.external_id == "123"

    @pytest.mark.integration
    def test_find(self, db_session, work_item_container_role_factory):
        #  Setup create a Work Item Container Role
        existing_wic_role = work_item_container_role_factory()
        existing_wic = existing_wic_role.work_item_container
        db_session.commit()

        """Ensure that an instance can be found with the proper params."""
        wic_role = find_or_build(
            db_session=db_session,
            model=models.WorkItemContainerRole,
            build_params={"tenant_id_str": "should-not-overwrite-tenant"},
            app_created_by=existing_wic_role.app_created_by,
            work_item_container_id=existing_wic.id,
        )
        # Should find and not create.
        assert wic_role.id
        assert wic_role.id == existing_wic_role.id
        assert wic_role.tenant_id_str == existing_wic_role.tenant_id_str
        assert wic_role.app_created_by == existing_wic_role.app_created_by
        assert wic_role.work_item_container_id == existing_wic.id


class TestDictify:
    """Ensure support methods work."""

    @pytest.mark.parametrize(
        "attrib_names",
        [
            pytest.param(["id", "tenant_id_str"], id="with-attribute-names"),
            pytest.param(None, id="without-attribute-names"),
        ],
    )
    def test_dictify_model(self, attrib_names):
        """Ensure dictify model works properly."""
        work_item = models.WorkItem(
            id=1,
            title="Test Item",
            external_type="leankit",
            external_id="1234",
            state="in_progress",
            planned_start=datetime(2021, 10, 10),
            planned_finish=datetime(2021, 11, 11),
            created_at=datetime(2021, 1, 1),
            tenant_id_str="tenant-id-1",
        )
        dict = dictify_model(work_item, attrib_names)
        assert dict["tenant_id_str"] == "tenant-id-1"
        assert dict["id"] == 1
        if not attrib_names:
            assert dict["title"] == "Test Item"
            assert dict["created_at"] == "2021-01-01T00:00:00"
        else:
            assert not dict.get("title")

    @pytest.mark.integration
    def test_dictify_persisted_key_result(self, db_session, key_result_factory):
        """
        Ensure that the dictify of records works as expected.

        Should only dictify the columns on the record and leave out relationship
        data.
        """
        kr = key_result_factory()
        db_session.commit()

        assert kr.id
        dict = dictify_model(kr)
        dict_keys = set(dict.keys())
        assert "Test Key Result" in dict["name"]
        assert {"objective_id", "id", "starts_at", "ends_at"}.issubset(dict_keys)
        assert "objective" not in dict_keys

    @pytest.mark.integration
    def test_dictify_for_json_persisted(self, db_session, progress_point_factory):
        """
        Ensure that the dictify of records works as expected.

        Should only dictify the columns on the record and leave out relationship
        data.
        """
        progress_point = progress_point_factory()
        db_session.commit()

        assert progress_point.id
        dict = dictify_model_for_json(progress_point)
        dict_keys = set(dict.keys())
        assert {
            "key_result_id",
            "id",
            "objective_progress_percentage",
            "app_created_by",
        }.issubset(dict_keys)
        assert "key_result" not in dict_keys
        assert isinstance(dict["created_at"], str)
        assert isinstance(dict["measured_at"], str)

    @pytest.mark.parametrize(
        "model_name",
        [
            pytest.param("setting"),
            pytest.param("work_item_container"),
            pytest.param("objective"),
            pytest.param("key_result"),
            pytest.param("key_result_work_item_mapping"),
            pytest.param("work_item"),
            pytest.param("progress_point"),
            pytest.param("activity_log"),
        ],
    )
    @pytest.mark.integration
    def test_serialization_of_persisted_models(self, db_session, request, model_name):
        factory = request.getfixturevalue(f"{model_name}_factory")
        model_instance = factory()
        db_session.commit()
        dict = dictify_model(model_instance)
        json_str = json.dumps(dict)
        assert json_str
        assert dict["id"]

    @pytest.mark.integration
    def test_dictify_json_columns(self, db_session, setting_factory):
        setting = setting_factory()
        db_session.commit()

        dict = dictify_model(setting)
        first_is_default_value = dict["level_config"][0]["is_default"]
        assert type(first_is_default_value) is bool
        assert first_is_default_value is False
