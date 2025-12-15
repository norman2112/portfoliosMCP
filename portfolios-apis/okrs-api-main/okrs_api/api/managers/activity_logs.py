"""Manager class for Activity Logs."""
from open_alchemy import models

# from sqlalchemy import or_


class ActivityLogsManager:
    """Class to handle the Activity Logs."""

    allowed_keys = {
        "objective_id",
        "key_result_id",
        "progress_point_id",
        "created_at",
    }
    info_keys_map = {
        "objectives": {
            "objective_name",
            "description",
            "starts_at",
            "ends_at",
            "parent_objective_id",
            "level_depth",
            "owned_by",
            "rolled_up_progress_percentage",
        },
        "key_results": {
            "key_result_name",
            "description",
            "owned_by",
            "starting_value",
            "starts_at",
            "ends_at",
            "target_value",
            "key_result_progress_percentage",
        },
        "targets": {"id", "starts_at", "ends_at", "target_value"},
        "progress_points": {
            "measured_at",
            "progress_point_value",
            "comment",
            "key_result_progress_percentage",
            "objective_progress_percentage",
        },
    }

    key_name_mapping = {
        "key_results": {
            "starts_at": "overall_starts_at",
            "ends_at": "overall_ends_at",
            "target_value": "final_target_value",
        }
    }

    def __init__(self, object_id, input_prepper):
        """Initialize the HistoryManager with input_prepper."""
        self.id = object_id
        self.input_prepper = input_prepper

    def fetch_history(self):
        """Fetch history."""
        raise NotImplementedError("This method should be overridden in subclasses")

    def filter_object(self, model, info_data):
        """Filter records based on model."""
        info_keys = self.info_keys_map[model]
        filtered_info = {}
        name_map = self.key_name_mapping.get(model)
        for k, v in info_data.items():
            if k in info_keys:
                if name_map and k in name_map:
                    filtered_info[name_map[k]] = v
                else:
                    filtered_info[k] = v
        return filtered_info

    def process_data(self, data):
        """Process history records."""
        processed = []
        for record in data:
            dict_record = record.to_dict()
            filtered_record = {
                k: v for k, v in dict_record.items() if k in self.allowed_keys
            }
            filtered_record["created_by"] = dict_record.get(
                "pv_created_by"
            ) or dict_record.get("pv_last_updated_by")
            parts = record.action.split(".")
            action, model = parts[0], parts[-1]
            filtered_record["action"] = action
            filtered_record["model"] = model
            filtered_info = {}
            if model in self.info_keys_map:
                info = record.info or {}
                if action == "update":
                    new_changes = self.filter_object(model, info["new"])
                    if new_changes:
                        filtered_info["new"] = new_changes
                        filtered_info["old"] = self.filter_object(model, info["old"])
                else:
                    filtered_info = self.filter_object(model, info)

            if filtered_info:
                filtered_record["info"] = filtered_info
                processed.append(filtered_record)
        return processed

    def get_history(self):
        """Fetch, process and return history."""
        history = self.fetch_history()
        return self.process_data(history)


class KeyResultsActivityLogs(ActivityLogsManager):
    """Class to handle KeyResultsActivityLogs."""

    def fetch_history(self):
        """Fetch key result history."""
        with self.input_prepper.db_session() as db_session:
            history = (
                db_session.query(models.ActivityLog)
                .filter_by(tenant_group_id_str=self.input_prepper.tenant_group_id)
                .filter_by(key_result_id=self.id)
                .order_by(models.ActivityLog.created_at.desc())
                .all()
            )
            return history


class ObjectivesActivityLogs(ActivityLogsManager):
    """Class to handle ObjectivesActivityLogs."""

    def fetch_history(self):
        """Fetch objectives history."""
        with self.input_prepper.db_session() as db_session:
            history = (
                db_session.query(models.ActivityLog)
                .filter_by(tenant_group_id_str=self.input_prepper.tenant_group_id)
                .filter_by(objective_id=self.id)
                .order_by(models.ActivityLog.created_at.desc())
                .all()
            )
            return history
