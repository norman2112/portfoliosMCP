"""Helpers for Settings-related concerns."""

from open_alchemy import models
from sqlalchemy import or_, and_


class SettingsManager:
    """Manager for all Settings-related help."""

    def __init__(self, org_id, tenant_group_id, created_by, db_session):
        """
        Initialize the SettingsManager.

        :param str org_id: the organization id
        :param str tenant_group_id: the group id
        :param str created_by: the planview user id
        :param db_session db_session: the database session
        """
        self.org_id = org_id
        self.tenant_group_id = tenant_group_id
        self.created_by = created_by
        self.db_session = db_session

    def find_or_build(self):
        """Find or build a new setting for the organization."""
        return self._find() or self._build_default()

    def _find(self):
        """Look for an existing Setting, based on the org_id."""
        return (
            self.db_session.query(models.Setting)
            .filter(
                or_(
                    and_(
                        models.Setting.tenant_id_str == self.org_id,
                        models.Setting.tenant_id_str != "",
                    ),
                    models.Setting.tenant_group_id_str == self.tenant_group_id,
                )
            )
            .first()
        )

    def find_all(self):
        """Look for an existing Setting, based on the org_id and return all matches."""
        return (
            self.db_session.query(models.Setting)
            .filter(
                or_(
                    and_(
                        models.Setting.tenant_id_str == self.org_id,
                        models.Setting.tenant_id_str != "",
                    ),
                    models.Setting.tenant_group_id_str == self.tenant_group_id,
                )
            )
            .order_by(models.Setting.updated_at.desc())
            .all()
        )

    def get_settings(self):
        """Get User settings."""
        record_exists = self._find()
        if record_exists:
            return record_exists
        return []

    def _build_default(self):
        """
        Build the Setting for the organization.

        The Setting needs no other arguments as it should have database defaults.
        """
        return models.Setting(
            tenant_id_str=self.org_id,
            tenant_group_id_str=self.tenant_group_id,
            created_by=self.created_by,
        )

    def validate_color_threshold_config(self, color_threshold_payload):
        """
        Validate the color threshold payload.

        :param list color_ranges: List of color range dictionaries
        """
        if (
            not isinstance(color_threshold_payload, list)
            or len(color_threshold_payload) == 0
        ):
            return {"success": False, "errors": ["Input must be a non-empty list"]}

        errors = []
        names = set()
        color_codes = set()

        for i, current in enumerate(color_threshold_payload):
            # Check if the object has all required properties
            required_keys = ["min", "max", "name", "colorCode"]
            if not all(key in current for key in required_keys):
                errors.append(f"Object at index {i} is missing required properties")
                continue

            # Check min/max sequence with previous object
            if i > 0:
                previous = color_threshold_payload[i - 1]
                if current["min"] != previous["max"]:
                    errors.append(
                        f"Min value ({current['min']}) of object at index {i} is not equal to "
                        f"max value ({previous['max']}) of previous object"
                    )

            # Check for duplicate names
            if current["name"] in names:
                errors.append(f"Duplicate name '{current['name']}' found at index {i}")
            else:
                names.add(current["name"])

            # Check for duplicate colorCodes
            if current["colorCode"] in color_codes:
                errors.append(
                    f"Duplicate colorCode '{current['colorCode']}' found at index {i}"
                )
            else:
                color_codes.add(current["colorCode"])

        return {"success": len(errors) == 0, "errors": errors}


class LevelConfigParser:
    """Wrapper with utility methods to more accurately parser the Level Config."""

    def __init__(self, level_config):
        """
        Initialize the LevelConfigParser.

        :param dict level_config: the level config in a Setting instance
        """
        self.level_config = level_config

    def default_level(self):
        """Return the default level dict."""
        return next(level for level in self.level_config if level.get("is_default"))

    def default_depth(self):
        """Return the default depth for the level config."""
        return self.default_level()["depth"]
