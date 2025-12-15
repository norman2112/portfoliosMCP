"""Test the activity log helpers."""

from open_alchemy import models
import pytest

from okrs_api.model_helpers.activity_logger import DeletionLogger


class TestDeletionLogger:
    """Ensure a deletion log can be created."""

    @pytest.mark.integration
    def test_create_log(self, db_session, setting_factory, objective_factory):
        """Ensure that a log can be created from the model."""
        setting_factory()
        objective = objective_factory()
        db_session.commit()

        logger = DeletionLogger(
            instance=objective,
            db_session=db_session,
            user_id="123",
        )
        logger.create_log()
        activity_log = db_session.query(models.ActivityLog).first()
        assert activity_log.info
        assert activity_log.action == "delete.objectives"
