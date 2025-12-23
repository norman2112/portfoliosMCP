from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from open_alchemy import models
import pytest

from okrs_api.model_helpers.deleter import Deleter


class TestDeleter:
    def test_cascade_for_wic_unit(self, setting_factory, progress_point_factory):
        """
        Ensure that a wic deletion soft deletes when the Deleter is used.

        This is a unit test that uses a mock alchemy for the db_session.
        """
        # Database setup
        db_session = UnifiedAlchemyMagicMock()
        pp = progress_point_factory.build()
        db_session.commit()

        wic = pp.key_result.objective.work_item_container
        deleter = Deleter(db_session=db_session, model_instance=wic)
        deleter.delete()
        db_session.commit()

        assert wic.is_deleted
        assert pp.is_deleted
        assert pp.key_result.is_deleted
        assert pp.key_result.objective.is_deleted

    @pytest.mark.integration
    def test_cascade_for_wic(self, db_session, setting_factory, progress_point_factory):
        """Ensure that a wic deletion soft deletes when the Deleter is used."""
        # Database setup
        setting_factory()
        pp = progress_point_factory()
        db_session.commit()

        wic = pp.key_result.objective.work_item_container
        deleter = Deleter(db_session=db_session, model_instance=wic)
        deleter.delete()
        db_session.commit()

        assert wic.is_deleted
        assert pp.is_deleted
        assert pp.key_result.is_deleted
        assert pp.key_result.objective.is_deleted

    @pytest.mark.integration
    def test_true_deletion_for_kr_mappings(
        self, db_session, setting_factory, key_result_work_item_mapping_factory
    ):
        """Ensure that KeyResultMappings are truly deleted."""
        # Db setup
        setting_factory()
        mapping = key_result_work_item_mapping_factory()
        mapping_id = mapping.id
        db_session.commit()

        kr = mapping.key_result
        deleter = Deleter(db_session=db_session, model_instance=kr)
        deleter.delete()

        found_mapping = db_session.query(models.KeyResultWorkItemMapping).get(
            mapping_id
        )

        assert not found_mapping
        assert kr.is_deleted
