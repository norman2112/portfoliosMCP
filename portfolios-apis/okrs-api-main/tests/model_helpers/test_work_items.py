"""Test model helpers for WorkItems."""

import pytest
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from okrs_api.model_helpers.work_items import WorkItemCreator
from okrs_api import utils


class TestWorkItemCreator:
    """Test the creation of work items."""

    BASE_INPUT = {
        "context_id": "12345",
        "context_title": "Epic Quest",
        "domain": "d08.leankit.io",
        "product_type": "leankit",
        "title": "Test Work Item",
        "planned_start": "2021-01-01",
        "planned_finish": "2021-05-05",
        "key_result_id": 1,
        "external_activity_type_id": "123456",
    }

    def make_input_parser(self, data={}):
        """
        Make an input parser.

        :param dict data: data to override the base data
        """
        parser_data = {**self.BASE_INPUT, **data}
        return utils.Map(**parser_data)

    @pytest.mark.usefixtures("init_models")
    def test_create(self):
        creator = WorkItemCreator(
            work_item_attribs={
                "external_id": 1,
                "tenant_id_str": "tenant-id-1",
                "item_type": "New Feature",
            },
            input_parser=self.make_input_parser(),
            db_session=UnifiedAlchemyMagicMock(),
        )
        work_item = creator.create()
        wic = work_item.work_item_container

        assert work_item.tenant_id_str == "tenant-id-1"
        assert work_item.item_type == "New Feature"
        assert work_item.external_id == 1
        assert wic.external_title == "Epic Quest"

    @pytest.mark.integration
    def test_create_duplicate_external_id(
        self,
        db_session,
        work_item_container_factory,
        objective_factory,
        setting_factory,
        key_result_factory,
    ):
        """Test that we don't reuse the same WI even if external ID is same but tenant id different."""
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_id_str = "tenant-id-2"
        wic.external_id = "101"
        wic.title = "Epic Hunt"
        wic.external_type = "leankit"
        wic.app_name = "leankit"
        wic.tenant_group_id_str = "tenant-group-id-2"
        db_session.commit()
        wic_id = wic.id
        obj = objective_factory()
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory()
        kr.objective_id = obj.id
        db_session.commit()

        creator = WorkItemCreator(
            work_item_attribs={
                "external_id": "10212",
                "title": "Hello Sherlock Item",
                "tenant_id_str": "tenant-id-2001",
                "tenant_group_id_str": "tenant-group-id-str-2",
                "item_type": "New Feature",
            },
            input_parser=self.make_input_parser(
                data={
                    "context_id": "101",
                    "context_title": "Epic Quest",
                    "domain": "d08.leankit.io",
                    "product_type": "leankit",
                    "title": "Test Work Item",
                    "planned_start": "2021-01-01",
                    "planned_finish": "2021-05-05",
                    "key_result_id": kr.id,
                    "external_activity_type_id": "123456",
                }
            ),
            db_session=db_session,
        )
        work_item = creator.create()
        wic = work_item.work_item_container
        assert wic.id != wic_id
