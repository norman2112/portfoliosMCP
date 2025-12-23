"""Level Config validations."""

import copy
from open_alchemy import models
from sqlalchemy import and_
from sqlalchemy import or_
from okrs_api.validators.base import BaseValidator

# pylint:disable=too-many-arguments


class LevelConfigValidator(BaseValidator):
    """Validator for the `level_config` in the settings."""

    VALIDATIONS = [
        "depth_sequence",
        "unique_name",
        "exactly_one_default",
        "level_not_removed",
    ]

    def __init__(
        self,
        input_prepper,
        action_type=None,
        existing_level_config=None,
        proposed_level_config=None,
    ):
        """
        Initialize the level config validator.

        :param LevelConfig existing_level_config: the existing level config.
        This is used in case wherein we want to use the validator but do not
        want to re-fetch the existing level config.

        :param LevelConfig proposed_level_config: a level config override
        This param would be directly supplied, overriding the level config
        typically provided by user input.
        """
        super().__init__(input_prepper)
        self.action_type = action_type or "add_or_edit"
        self.existing_level_config = existing_level_config or []
        self.proposed_level_config = proposed_level_config

    @property
    def level_config(self):
        """Return the proposed level config from the user input."""
        return self.proposed_level_config or self.input_parser.level_config

    @property
    def add_or_edit_action(self):
        """Return True if this is an add_or_edit action."""
        return self.action_type == "add_or_edit"

    @property
    def delete_action(self):
        """Return True if this is a delete action."""
        return self.action_type == "delete"

    @property
    def _depths(self):
        return [int(depth) for depth in self._attr_list("depth")]

    @property
    def _max_depth(self):
        """Return an integer of the deepest depth."""
        return max(self._depths)

    def _existing_level_config(self):
        """
        Return the existing level config, if it exists in the database.

        Memoize the exisitng level config, if it is passed in.
        """
        if not self.existing_level_config:
            setting = (
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

            if setting:
                self.existing_level_config = setting.level_config

        return self.existing_level_config

    def _attr_list(self, key):
        """Return a list of a single attribute."""
        return [level.get(key) for level in self.level_config]

    def _level_count_comparison(self):
        """
        Return the difference level counts.

        The level count difference is <new_level_count> - <current_level_count>.
        A positive number is more levels. A negative number is fewer levels.
        """

        existing_level_config = self._existing_level_config()
        return len(self.level_config) - len(existing_level_config)

    def _level_not_removed_check(self):
        """
        Check that the number of levels has not decreased.

        This check is only performed if the action is an add/edit action.
        """
        if not self.add_or_edit_action:
            return True

        if self._level_count_comparison() >= 0:
            return True

        self.add_error(
            code="level_not_removed",
            message="You may not remove a level with this action.",
        )
        return False

    def _depth_sequence_check(self):
        """Validate the depths are sequential."""
        if not self.add_or_edit_action:
            return True

        expected_depths = list(range(self._max_depth + 1))
        if self._depths == expected_depths:
            return True

        self.add_error(
            code="depth_sequence",
            message="Levels do not have sequential depths, "
            f"starting from 0. {self._depths}",
            details=[{"attribute": "depths", "value": self._depths}],
        )
        return False

    def _unique_name_check(self):
        """Validate the names are unique."""
        names = self._attr_list("name")
        return self.check_uniqueness(names, "name")

    def get_first_work_item_container(self):
        """Get first work item container."""
        work_item_container = (
            self.db_session.query(models.WorkItemContainer)
            .filter(
                or_(
                    models.WorkItemContainer.tenant_group_id_str
                    == self.tenant_group_id,
                    models.WorkItemContainer.tenant_id_str == self.org_id,
                )
            )
            .filter(models.WorkItemContainer.deleted_at_epoch == 0)
            .order_by(models.WorkItemContainer.level_depth_default.desc())
            .first()
        )
        return work_item_container

    def get_all_work_item_containers(self):
        """Get all work items containers."""
        work_item_containers = (
            self.db_session.query(models.WorkItemContainer)
            .filter(
                or_(
                    models.WorkItemContainer.tenant_group_id_str
                    == self.tenant_group_id,
                    models.WorkItemContainer.tenant_id_str == self.org_id,
                )
            )
            .filter(models.WorkItemContainer.deleted_at_epoch == 0)
            .order_by(models.WorkItemContainer.level_depth_default.desc())
            .all()
        )
        return work_item_containers

    def _find_wic_max_default_level_depth(self):
        """Find the maximum level depth default amongst WorkItemContainers."""
        work_item_container = self.get_first_work_item_container()
        if not work_item_container:
            return None
        level_depth_default = work_item_container.level_depth_default
        return level_depth_default

    def get_entities(self, level_depth_default):
        """
        Filter and group entities based on a given level depth and their container type.

        This function iterates through a list of work item containers (`wics`), which is
        expected to be a list of objects or dictionaries with attributes like
        `level_depth_default`, `container_type`, `external_id`, and `external_title`.
        It filters the `wics` based on the provided `level_depth_default` value
        and groups them into predefined categories: strategies, works, and boards,
        based on their `container_type`.
        """
        work_item_containers = self.get_all_work_item_containers()
        container_to_entity_map = {
            "e1_strategy": "strategies",
            "e1_work": "works",
            "lk_board": "boards",
        }

        entities = {"strategies": [], "works": [], "boards": []}

        for each in work_item_containers:
            if each.level_depth_default == level_depth_default:
                entity_type = container_to_entity_map.get(each.container_type)

                if entity_type:
                    entities[entity_type].append(
                        {"id": each.external_id, "title": each.external_title}
                    )

        return entities

    @staticmethod
    def get_primary_level(config, depth):
        """Retrieve the name of the primary level from specified depth."""
        for entry in config:
            if entry.get("depth") == depth:
                return entry.get("name", "")

        return ""

    def _level_depth_required_check(self):
        """
        Validate default depth of WorkItemContainers.

        If any WorkItemContainer associated with this organization has a
        `level_depth_default` greater than the greatest level depth in this
        config, then this config is invalid.
        """
        min_depth_required = self._find_wic_max_default_level_depth() or 0
        if self._max_depth >= min_depth_required:
            return True
        print(
            f"Last Level as Primary: {self.tenant_group_id} - "
            f"{self.org_id} - {self.user_id} - {self.user_id}"
        )
        self.add_error(
            code="level_depth_required",
            message=(
                "You do not have enough levels to meet the minimum "
                f"level depth required: ({min_depth_required})"
            ),
            details=[
                {
                    "attribute": "min_depth_required",
                    "value": min_depth_required,
                    "primary_level": self.get_primary_level(
                        self.existing_level_config, min_depth_required
                    ),
                    "entities": self.get_entities(min_depth_required),
                }
            ],
        )
        return False

    def _exactly_one_default_check(self):
        """Validate the levels have exactly one default."""
        defaults = [level for level in self.level_config if level.get("is_default")]
        if len(defaults) == 1:
            return True
        if self.action_type == "delete":
            self.add_error(
                code="default_level_con_not_be_deleted",
                message="Please save changes to the default level before deleting another level.",
            )
            return False

        self.add_error(
            code="exactly_one_default",
            message="You must have exactly one default.",
        )
        return False


class LevelConfigDeletionValidator(BaseValidator):
    """
    Work in collaboration with teh LevelConfigValidator.

    This validator applies errors that only occur on delete operations.
    """

    VALIDATIONS = [
        "level_depth_in_bounds",
        "no_objectives",
        "valid_level_config",
    ]

    def __init__(self, input_prepper, existing_level_config):
        """
        Initialize the validator.

        :param int level_depth: the level depth to delete
        :param LevelConfig existing_level_config: the existing level config
        """
        super().__init__(input_prepper)
        self.existing_level_config = existing_level_config
        self._proposed_level_config = None

    @property
    def level_depth(self):
        """Return the level depth supplied by user input."""
        return self.input_parser.level_depth

    def proposed_level_config(self):
        """
        Return the new, proposed level config.

        The proposed level config is the existing level config but
            - without the level that was marked for deletion
            - with newly re-indexed, sequential depths

        Memoize the result.
        """
        if not self._proposed_level_config:
            level_config = copy.deepcopy(self.existing_level_config)
            if self.level_depth < len(level_config):
                del level_config[self.level_depth]
            for i, level in enumerate(level_config):
                level["depth"] = i
            self._proposed_level_config = level_config

        return self._proposed_level_config

    def _level_depth_in_bounds_check(self):
        """
        Check if the level depth is deletable.

        Level depths should always be sequential and start from 0, so the
        level count should always be one greater than the highest level depth.
        """
        if self.level_depth < len(self.existing_level_config):
            return True

        self.add_error(
            code="level_depth_in_bounds",
            message="Level depth is out of range.",
        )
        return False

    @staticmethod
    def get_entities_info(objectives):
        """Get work item containers info for given objectives."""
        container_to_entity_map = {
            "e1_strategy": "strategies",
            "e1_work": "works",
            "lk_board": "boards",
        }

        entities = {key: {} for key in container_to_entity_map.values()}

        for obj in objectives:
            container = obj.work_item_container
            if container is None:
                continue
            entity_type = container_to_entity_map.get(container.container_type)
            entity_id = container.external_id

            entity_group = entities[entity_type]

            entity = entity_group.setdefault(
                entity_id,
                {
                    "id": container.external_id,
                    "title": container.external_title,
                    "objectives": [],
                },
            )

            entity["objectives"].append({"id": obj.id, "title": obj.name})
        entities = {key: list(group.values()) for key, group in entities.items()}
        return entities

    def _no_objectives_check(self):
        """Return an error if the depth to be deleted has objectives."""
        objectives = (
            self.db_session.query(models.Objective)
            .filter(
                or_(
                    models.Objective.tenant_group_id_str == self.tenant_group_id,
                    models.Objective.tenant_id_str == self.org_id,
                )
            )
            .filter_by(level_depth=self.level_depth, deleted_at_epoch=0)
            .all()
        )
        entities = self.get_entities_info(objectives)
        objectives_count = len(objectives)
        if objectives_count == 0:
            return True

        self.add_error(
            code="no_objectives",
            message=(
                f"Please move {objectives_count} objectives "
                "from this level before deleting."
            ),
            details=[
                {
                    "attribute": "objective_count",
                    "value": objectives_count,
                    "entities": entities,
                    "primary_level": LevelConfigValidator.get_primary_level(
                        self.existing_level_config, self.level_depth
                    ),
                }
            ],
        )
        return False

    def _valid_level_config_check(self):
        """
        Validate, using the standard LevelConfigValidator.

        Use the proposed_level_config as input.
        """

        validator = LevelConfigValidator(
            input_prepper=self.input_prepper,
            action_type="delete",
            proposed_level_config=self.proposed_level_config(),
            existing_level_config=self.existing_level_config,
        )
        validator.validate()
        if not validator.errors:
            return True

        self.append_errors(validator.errors)
        return False


# pylint:disable=not-an-iterable
class LevelConfigInsertValidator(BaseValidator):
    """
    Work in collaboration with the LevelConfigValidator.

    This validator applies errors that only occur on delete operations.
    """

    VALIDATIONS = [
        "valid_level_config",
    ]

    def __init__(self, input_prepper, existing_level_config):
        """
        Initialize the validator.

        :param int level_depth: the level depth to delete
        :param LevelConfig existing_level_config: the existing level config
        """
        super().__init__(input_prepper)
        self.existing_level_config = existing_level_config
        self._proposed_level_config = None
        self._insert_at = None

    @property
    def new_level(self):
        """Return the level depth supplied by user input."""
        return self.input_parser.new_level

    @property
    def insert_at(self):
        """Return the index at which we need to insert the new level."""
        if not self._insert_at:
            self._insert_at = self.input_parser.new_level.get("depth", None)
        return self._insert_at

    def _attr_list(self, key):
        """Return a list of a single attribute."""
        return [level.get(key) for level in self.proposed_level_config]

    def proposed_level_config(self):
        """
        Return the new, proposed level config.

        The proposed level config is the existing level config but
            - without the level that was marked for deletion
            - with newly re-indexed, sequential depths

        Memoize the result.
        """
        if not self._proposed_level_config:
            level_config = copy.deepcopy(self.existing_level_config)
            level_config.insert(self.insert_at, self.new_level)
            for level in range(self.insert_at + 1, len(level_config)):
                level_config[level]["depth"] += 1
            self._proposed_level_config = level_config

        return self._proposed_level_config

    def _valid_level_config_check(self):
        """
        Validate, using the standard LevelConfigValidator.

        Use the proposed_level_config as input.
        """
        validator = LevelConfigValidator(
            input_prepper=self.input_prepper,
            proposed_level_config=self.proposed_level_config(),
            existing_level_config=self.existing_level_config,
        )
        validator.validate()
        if not validator.errors:
            return True

        self.append_errors(validator.errors)
        return False
