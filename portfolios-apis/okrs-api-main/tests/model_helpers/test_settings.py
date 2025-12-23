"""Test model helpers for Settings."""

import pytest
from open_alchemy import models

from okrs_api.model_helpers.settings import LevelConfigParser, SettingsManager


class TestSettingsManager:
    """Tests for the Settings Manager."""

    DEFAULT_ORG_ID = "987654321-TEST"

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_create_if_not_existing(self, db_session):
        """Ensure that a new [default] Setting is created if none exist."""
        manager = SettingsManager(
            org_id=self.DEFAULT_ORG_ID,
            db_session=db_session,
            tenant_group_id="1234",
            created_by="4321",
        )
        setting = manager.find_or_build()
        assert setting.tenant_id_str == self.DEFAULT_ORG_ID

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_find_correct_if_tenant_id_empty(self, db_session):
        """Ensure that the right existing setting is found when we only have a tenant group id."""
        existing_setting1 = models.Setting(
            level_config=[{"name": "Test1", "depth": 0, "id_default": True}],
            tenant_id_str="",
            tenant_group_id_str="1235",
        )
        db_session.add(existing_setting1)
        existing_setting2 = models.Setting(
            level_config=[{"name": "Test2", "depth": 0, "id_default": True}],
            tenant_id_str="something",
            tenant_group_id_str="1234",
        )
        db_session.add(existing_setting2)
        db_session.commit()

        manager = SettingsManager(
            org_id="",
            db_session=db_session,
            tenant_group_id="1234",
            created_by="4321",
        )
        setting = manager.find_or_build()
        assert setting.tenant_id_str == "something"
        assert setting.tenant_group_id_str == "1234"
        assert setting.level_config[0]["name"] == "Test2"

    @pytest.mark.integration
    @pytest.mark.usefixtures("init_models")
    def test_find_if_existing(self, db_session):
        """Ensure that the Setting returned is the existing setting."""
        # Setup
        existing_setting = models.Setting(
            level_config=[{"name": "Test", "depth": 0, "id_default": True}],
            tenant_id_str=self.DEFAULT_ORG_ID,
        )
        db_session.add(existing_setting)
        db_session.commit()

        # Now, ensure that we're getting back the original.
        manager = SettingsManager(
            org_id=self.DEFAULT_ORG_ID,
            db_session=db_session,
            tenant_group_id="1234",
            created_by="4321",
        )
        setting = manager.find_or_build()
        assert setting.level_config[0].get("name") == "Test"


class TestLevelConfigParser:
    """Test the LevelConfigParser."""

    LEVEL_CONFIG_DATA = [
        {"depth": 0, "name": "Enterprise", "color": "#ba8aa4", "is_default": False},
        {"depth": 1, "name": "Portfolio", "color": "#f87b55", "is_default": False},
        {"depth": 2, "name": "Program", "color": "#8ab98e", "is_default": True},
        {"depth": 3, "name": "Team", "color": "#608eb6", "is_default": False},
    ]

    def test_default_level_detection(self):
        """Ensure that the parser can find the default level correctly."""
        parser = LevelConfigParser(self.LEVEL_CONFIG_DATA)
        assert parser.default_level()["name"] == "Program"

    def test_default_depth_detection(self):
        """Ensure that the parser can find the default depth correctly."""
        parser = LevelConfigParser(self.LEVEL_CONFIG_DATA)
        assert parser.default_depth() == 2
