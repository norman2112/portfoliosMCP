"""Manager class for KeyResults."""
from open_alchemy import models
from sqlalchemy import and_


class KeyResultsManager:
    """Class to handle the Objectives."""

    def __init__(self, input_prepper=None):
        """Initialize the KeyResultsManager with input_prepper."""
        self.input_prepper = input_prepper

    def get_total_count(self, db_session, id_list):
        """Get total count of keys results."""
        base_kr_query = db_session.query(models.KeyResult.id).filter_by(
            tenant_group_id_str=self.input_prepper.tenant_group_id, deleted_at_epoch=0
        )
        if id_list:
            base_kr_query = base_kr_query.filter(models.KeyResult.id.in_(id_list))
        total_count = base_kr_query.count()
        return total_count

    def get_key_results(self):
        """Fetch, process and return key results."""
        total_records, key_results = self.fetch_key_results()
        aggregated = self.process_key_result(key_results)
        result = {
            "total_records": total_records,
            "key_results": list(aggregated.values()),
        }
        return result

    def fetch_key_results(self):
        """Fetch key_results from the DB."""
        user_limit = self.input_prepper.input_parser.limit or 10
        user_offset = self.input_prepper.input_parser.offset or 0
        limit = min(max(int(user_limit), 1), 500)  # Restrict limit to 1-500
        offset = max(int(user_offset), 0)  # Ensure offset is non-negative
        ids = self.input_prepper.input_parser.ids
        id_list = [int(i) for i in ids.split(",")] if ids else []

        with self.input_prepper.db_session() as db_session:
            total_records = self.get_total_count(db_session, id_list)

            limited_kr_query = db_session.query(models.KeyResult.id).filter_by(
                tenant_group_id_str=self.input_prepper.tenant_group_id,
                deleted_at_epoch=0,
            )
            if id_list:
                limited_kr_query = limited_kr_query.filter(
                    models.KeyResult.id.in_(id_list)
                )

            limited_kr_subq = (
                limited_kr_query.order_by(models.KeyResult.id)
                .limit(limit)
                .offset(offset)
                .subquery()
            )

            key_results = (
                db_session.query(
                    models.KeyResult.id,
                    models.KeyResult.name,
                    models.KeyResult.description,
                    models.KeyResult.starts_at,
                    models.KeyResult.ends_at,
                    models.KeyResult.objective_id,
                    models.KeyResult.progress_percentage,
                    models.KeyResult.starting_value,
                    models.KeyResult.target_value.label("final_target_value"),
                    models.KeyResult.owned_by,
                    models.KeyResult.created_at,
                    models.ProgressPoint.id.label("progress_id"),
                    models.ProgressPoint.measured_at.label("progress_measured_at"),
                    models.ProgressPoint.value.label("progress_value"),
                    models.ProgressPoint.comment.label("progress_comment"),
                    models.Target.id.label("target_id"),
                    models.Target.starts_at.label("target_starts_at"),
                    models.Target.ends_at.label("target_ends_at"),
                    models.Target.value.label("target_value"),
                )
                .join(limited_kr_subq, models.KeyResult.id == limited_kr_subq.c.id)
                .outerjoin(
                    models.ProgressPoint,
                    and_(
                        models.ProgressPoint.key_result_id == models.KeyResult.id,
                        models.ProgressPoint.deleted_at_epoch == 0,
                    ),
                )
                .outerjoin(
                    models.Target,
                    and_(
                        models.Target.key_result_id == models.KeyResult.id,
                        models.Target.is_deleted.is_(False),
                    ),
                )
                .order_by(models.KeyResult.id)
                .all()
            )
            return total_records, key_results

    @staticmethod
    def process_key_result(key_results):
        """Process key results."""
        aggregated = {}
        progress_ids = set()
        target_ids = set()
        for key_result in key_results:
            key_result_id = key_result.id
            if key_result_id not in aggregated:
                curr_key_result = {
                    "id": key_result.id,
                    "name": key_result.name,
                    "description": key_result.description,
                    "overall_starts_at": key_result.starts_at,
                    "overall_ends_at": key_result.ends_at,
                    "objective_id": key_result.objective_id,
                    "progress_percentage": key_result.progress_percentage,
                    "starting_value": key_result.starting_value,
                    "final_target_value": key_result.final_target_value,
                    "targets": [],
                    "owned_by": key_result.owned_by,
                    "created_at": key_result.created_at,
                    "progress_points": [],
                }
                aggregated[key_result_id] = curr_key_result

            if key_result.progress_id and key_result.progress_id not in progress_ids:
                aggregated[key_result_id]["progress_points"].append(
                    {
                        "id": key_result.progress_id,
                        "measured_at": key_result.progress_measured_at,
                        "value": key_result.progress_value,
                        "comment": key_result.progress_comment,
                    }
                )
                progress_ids.add(key_result.progress_id)
            if key_result.target_id and key_result.target_id not in target_ids:
                aggregated[key_result_id]["targets"].append(
                    {
                        "id": key_result.target_id,
                        "value": key_result.target_value,
                        "starts_at": key_result.target_starts_at,
                        "ends_at": key_result.target_ends_at,
                    }
                )
                target_ids.add(key_result.target_id)

        for key_result_id, result in aggregated.items():
            result["progress_points"] = sorted(
                result["progress_points"],
                key=lambda x: x["measured_at"],
                reverse=True,
            )
            result["targets"] = sorted(result["targets"], key=lambda x: x["starts_at"])
        return aggregated
