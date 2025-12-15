"""Test model helpers for WorkItems."""

import pytest
from mock_alchemy.mocking import UnifiedAlchemyMagicMock

from okrs_api.model_helpers.activity_mappings import ActivitiesConnectionCreator
from okrs_api import utils


class TestActivitiesConnectionCreator:
    """Test the connection of work items."""

    ORG_ID = "p-1123asdasdsaplt"
    ORG_ID_2 = "p-1123xcvxvcxvcxvcx"
    GROUP_ID = "121312321321321321321"
    GROUP_ID_2 = "1213128978979878979"
    PRODUCT_TYPE = "e1_prm"
    CONTAINER_TYPE = "e1_strategy"

    def make_input_parser(self, data={}):
        """
        Make an input parser.

        :param dict data: data to override the base data
        """
        parser_data = {**data}
        return utils.Map(**parser_data)

    @pytest.mark.integration
    def test_create(
        self,
        db_session,
        work_item_container_factory,
        objective_factory,
        setting_factory,
        key_result_factory,
    ):
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_id_str = self.ORG_ID
        wic.external_id = "101"
        wic.title = "Epic Quest"
        wic.external_type = self.PRODUCT_TYPE
        wic.app_name = self.PRODUCT_TYPE
        wic.tenant_group_id_str = self.GROUP_ID
        db_session.commit()
        wic_id = wic.id
        obj = objective_factory()
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory()
        kr.objective_id = obj.id
        db_session.commit()
        connector = ActivitiesConnectionCreator(
            db_session=db_session,
            created_by="xyzabc",
            app_name=self.PRODUCT_TYPE,
            user_id="112334",
            org_id=self.ORG_ID,
            tenant_group_id=self.GROUP_ID,
            input_parser=self.make_input_parser(
                data={
                    "work_items": [
                        {
                            "external_id": "wi_1",
                            "tenant_id_str": self.ORG_ID,
                            "tenant_group_id_str": self.GROUP_ID,
                            "item_type": "New Feature",
                            "external_type": self.PRODUCT_TYPE,
                            "container_type": self.CONTAINER_TYPE,
                        }
                    ],
                    "work_item_container": {
                        "external_id": "101",
                        "external_type": self.PRODUCT_TYPE,
                        "external_title": "Epic Quest",
                    },
                    "key_result_id": kr.id,
                }
            ),
        )
        mapping = connector.connect()[0]
        assert mapping.key_result_id == kr.id
        assert mapping.work_item.work_item_container_id == wic_id
        assert mapping.work_item.work_item_container.tenant_id_str == self.ORG_ID

    @pytest.mark.integration
    def test_create_duplicate_external_id(
        self,
        db_session,
        work_item_container_factory,
        objective_factory,
        setting_factory,
        key_result_factory,
    ):
        setting_factory()
        wic = work_item_container_factory()
        wic.tenant_id_str = self.ORG_ID_2
        wic.external_id = "101"
        wic.title = "Epic Quest"
        wic.external_type = self.PRODUCT_TYPE
        wic.app_name = self.PRODUCT_TYPE
        wic.tenant_group_id_str = self.GROUP_ID_2
        db_session.commit()
        wic_id = wic.id
        obj = objective_factory()
        # This ideally would not happen, but we don't want the test to fail intermittently
        # In real life, there would be a separate WIC with correct ORG and GROUP ids
        # but that may not always be found if we only search by external ID, which was the bug.
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory()
        kr.objective_id = obj.id
        db_session.commit()
        connector = ActivitiesConnectionCreator(
            db_session=db_session,
            created_by="xyzabc",
            app_name=self.PRODUCT_TYPE,
            user_id="112334",
            org_id=self.ORG_ID,
            tenant_group_id=self.GROUP_ID,
            input_parser=self.make_input_parser(
                data={
                    "work_items": [
                        {
                            "external_id": "wi_1",
                            "tenant_id_str": self.ORG_ID,
                            "tenant_group_id_str": self.GROUP_ID,
                            "item_type": "New Feature",
                            "external_type": self.PRODUCT_TYPE,
                            "container_type": self.CONTAINER_TYPE,
                        }
                    ],
                    "work_item_container": {
                        "external_id": "101",
                        "external_type": self.PRODUCT_TYPE,
                        "external_title": "Epic Quest",
                    },
                    "key_result_id": kr.id,
                }
            ),
        )
        mapping = connector.connect()[0]
        assert mapping.key_result_id == kr.id
        assert (
            mapping.work_item.work_item_container_id != wic_id
        )  # Duplicate external ID should not match
        assert mapping.work_item.work_item_container.tenant_id_str == self.ORG_ID

    @pytest.mark.integration
    def test_create_duplicate_wi_external_id(
        self,
        db_session,
        work_item_container_factory,
        objective_factory,
        setting_factory,
        work_item_factory,
        key_result_factory,
    ):
        setting_factory()
        wic_other = work_item_container_factory()
        wic_other.tenant_id_str = self.ORG_ID_2
        wic_other.external_id = "101"
        wic_other.title = "Epic Quest"
        wic_other.external_type = self.PRODUCT_TYPE
        wic_other.app_name = self.PRODUCT_TYPE
        wic_other.tenant_group_id_str = self.GROUP_ID_2
        db_session.commit()
        wic_other_id = wic_other.id

        wi_other = work_item_factory()
        wi_other.tenant_id_str = self.ORG_ID_2
        wi_other.tenant_group_id_str = self.GROUP_ID_2
        wi_other.external_id = "wi_1"
        wi_other.external_type = self.PRODUCT_TYPE
        db_session.commit()
        wi_other_id = wi_other.id

        wic = work_item_container_factory()
        wic.tenant_id_str = self.ORG_ID
        wic.external_id = "101"
        wic.title = "Epic Quest"
        wic.external_type = self.PRODUCT_TYPE
        wic.container_type = self.CONTAINER_TYPE
        wic.app_name = self.PRODUCT_TYPE
        wic.tenant_group_id_str = self.GROUP_ID
        db_session.commit()

        obj = objective_factory()
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory()
        kr.objective_id = obj.id
        db_session.commit()
        connector = ActivitiesConnectionCreator(
            db_session=db_session,
            created_by="xyzabc",
            app_name=self.PRODUCT_TYPE,
            user_id="112334",
            org_id=self.ORG_ID,
            tenant_group_id=self.GROUP_ID,
            input_parser=self.make_input_parser(
                data={
                    "work_items": [
                        {
                            "external_id": "wi_1",
                            "tenant_id_str": self.ORG_ID,
                            "tenant_group_id_str": self.GROUP_ID,
                            "item_type": "New Feature",
                            "external_type": self.PRODUCT_TYPE,
                            "container_type": self.CONTAINER_TYPE,
                        }
                    ],
                    "work_item_container": {
                        "external_id": "101",
                        "external_type": self.PRODUCT_TYPE,
                        "external_title": "Epic Quest",
                    },
                    "key_result_id": kr.id,
                }
            ),
        )
        mapping = connector.connect()[0]
        assert mapping.key_result_id == kr.id
        assert (
            mapping.work_item.work_item_container_id != wic_other_id
        )  # Duplicate external ID should not match
        assert (
            mapping.work_item.id != wi_other_id
        )  # Duplicate external ID should not match (Sales BUG scenario)

    @pytest.mark.integration
    def test_create_find_correct_wi_external_id(
        self,
        db_session,
        work_item_container_factory,
        objective_factory,
        setting_factory,
        work_item_factory,
        key_result_factory,
    ):
        setting_factory()
        wic_other = work_item_container_factory()
        wic_other.tenant_id_str = self.ORG_ID_2
        wic_other.external_id = "101"
        wic_other.title = "Epic Quest"
        wic_other.external_type = self.PRODUCT_TYPE
        wic_other.app_name = self.PRODUCT_TYPE
        wic_other.tenant_group_id_str = self.GROUP_ID_2
        db_session.commit()
        wic_other_id = wic_other.id

        wi_other = work_item_factory()
        wi_other.tenant_id_str = self.ORG_ID_2
        wi_other.tenant_group_id_str = self.GROUP_ID_2
        wi_other.external_id = "wi_1"
        wi_other.external_type = self.PRODUCT_TYPE
        db_session.commit()
        wi_other_id = wi_other.id

        wic = work_item_container_factory()
        wic.tenant_id_str = self.ORG_ID
        wic.external_id = "101"
        wic.title = "Epic Quest"
        wic.external_type = self.PRODUCT_TYPE
        wic.app_name = self.PRODUCT_TYPE
        wic.tenant_group_id_str = self.GROUP_ID
        db_session.commit()
        wic_id = wic.id

        wi = work_item_factory()
        wi.tenant_id_str = self.ORG_ID
        wi.tenant_group_id_str = self.GROUP_ID
        wi.external_id = "wi_1"
        wi.external_type = self.PRODUCT_TYPE
        wi.container_type = self.CONTAINER_TYPE
        db_session.commit()
        wi_id = wi.id

        obj = objective_factory()
        obj.work_item_container_id = wic.id
        db_session.commit()
        kr = key_result_factory()
        kr.objective_id = obj.id
        db_session.commit()
        connector = ActivitiesConnectionCreator(
            db_session=db_session,
            created_by="xyzabc",
            app_name=self.PRODUCT_TYPE,
            user_id="112334",
            org_id=self.ORG_ID,
            tenant_group_id=self.GROUP_ID,
            input_parser=self.make_input_parser(
                data={
                    "work_items": [
                        {
                            "external_id": "wi_1",
                            "tenant_id_str": self.ORG_ID,
                            "tenant_group_id_str": self.GROUP_ID,
                            "item_type": "New Feature",
                            "external_type": self.PRODUCT_TYPE,
                            "container_type": self.CONTAINER_TYPE,
                        }
                    ],
                    "work_item_container": {
                        "external_id": "101",
                        "external_type": self.PRODUCT_TYPE,
                        "external_title": "Epic Quest",
                    },
                    "key_result_id": kr.id,
                }
            ),
        )
        mapping = connector.connect()[0]
        assert mapping.key_result_id == kr.id
        assert (
            mapping.work_item.work_item_container_id != wic_other_id
        )  # Duplicate external ID should not match
        assert (
            mapping.work_item.work_item_container_id == wic_id
        )  # Should not create a new one
        assert (
            mapping.work_item.id != wi_other_id
        )  # Duplicate external ID should not match (Sales BUG scenario)
        assert mapping.work_item.id == wi_id  # Should not create a new one
