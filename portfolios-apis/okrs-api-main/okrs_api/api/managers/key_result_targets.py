"""Manager class for key result targets."""

from okrs_api.model_helpers.common import set_last_updated_by_fields
from okrs_api.model_helpers.progress_points import get_progress_points_by_krid
from okrs_api.model_helpers.targets import (
    create_target,
    update_target,
    delete_target,
    get_targets_by_krid,
    get_mapped_target,
)


class KeyResultTargetsManager:
    """Class to handle the key result targets."""

    def __init__(self, key_result_id, db_session=None):
        """Initialize the KeyResultTargetsManager with input_prepper."""
        self.key_result_id = key_result_id
        self.targets = None
        self.progress_points = None
        self.db_session = db_session

    def create_targets(self, input_prepper, targets_data):
        """Create targets db objects."""
        for target in targets_data:
            target["key_result_id"] = self.key_result_id
            new_target = create_target(input_prepper, target)
            self.db_session.add(new_target)

    @staticmethod
    def has_target_changed(target_data, target_object):
        """Validate if target has changed."""
        if target_data["starts_at"] != target_object.starts_at:
            return True
        if target_data["ends_at"] != target_object.ends_at:
            return True
        if target_data["value"] != target_object.value:
            return True
        return False

    def process_targets(self, input_prepper, targets_data):
        """Insert/Delete/Update db targets objects."""
        targets_map = {t.id: t for t in self.targets}
        existing_target_ids = set(targets_map.keys())
        all_targets = []

        # TODO: Remove the if block once the multi targets' feature has been enabled for everyone
        if len(existing_target_ids) == 1 and len(targets_data) == 1:
            if not targets_data[0].get("id"):
                targets_data[0]["id"] = list(existing_target_ids)[0]
        for target_data in targets_data:
            target_id = target_data.get("id")
            if target_id:
                if target_id not in existing_target_ids:
                    raise Exception
                target_object = targets_map[target_id]
                if self.has_target_changed(target_data, target_object):
                    update_target(input_prepper, target_object, target_data)
                    self.db_session.add(target_object)
                existing_target_ids.discard(target_data["id"])
                all_targets.append(target_object)
            else:
                target_data["key_result_id"] = self.key_result_id
                new_target = create_target(input_prepper, target_data)
                self.db_session.add(new_target)
                all_targets.append(new_target)
        if existing_target_ids:
            for target_id in existing_target_ids:
                target_object = targets_map[target_id]
                delete_target(input_prepper, target_object)
                self.db_session.add(target_object)
        self.db_session.flush()
        return all_targets

    def remap_progress_points(self, all_targets, input_prepper):
        """Remap progress points to targets."""
        sorted_targets = sorted(all_targets, key=lambda t: t.starts_at)
        for progress_point in self.progress_points:
            target_id = get_mapped_target(sorted_targets, progress_point.measured_at)
            if progress_point.target_id and progress_point.target_id == target_id:
                continue
            progress_point.target_id = target_id
            set_last_updated_by_fields(progress_point, input_prepper)
            self.db_session.add(progress_point)

    def manage_targets(self, input_prepper, targets_data):
        """Handle targets' updates and progress points remapping."""
        self.progress_points = get_progress_points_by_krid(
            self.db_session, self.key_result_id
        )
        self.targets = get_targets_by_krid(self.db_session, self.key_result_id)
        all_targets = self.process_targets(input_prepper, targets_data)
        self.remap_progress_points(all_targets, input_prepper)
