"""
The repository for all VIEWS that are used in the database.

These are COPIES of the current VIEWS. This is not code that will be used in
migrations.

When you change, insert or a delete a view in a migration, make sure to update
it here as well as record of what our current views look like.

TODO: create a task that will generate a migration based on one or more of the
views in this file.
"""

VIEWS = {
    "objective_progress_points_view": (
        """
        CREATE OR REPLACE VIEW objective_progress_points_view
        AS SELECT key_results.objective_id,
        progress_points.*
        FROM key_results
        LEFT JOIN progress_points ON key_results.id = progress_points.key_result_id
        WHERE key_results.deleted_at_epoch = 0
        """
    ),
    "key_result_work_items_view": (
        "CREATE OR REPLACE VIEW key_result_work_items_view AS "
        "SELECT mappings.key_result_id, work_items.* "
        "FROM key_result_work_item_mappings AS mappings LEFT JOIN work_items "
        "ON mappings.work_item_id = work_items.id"
    ),
    "work_item_key_results_view": (
        """
        CREATE OR REPLACE VIEW work_item_key_results_view
        AS SELECT mappings.work_item_id,
        key_results.*
        FROM key_result_work_item_mappings mappings
        LEFT JOIN key_results ON mappings.key_result_id = key_results.id
        WHERE key_results.deleted_at_epoch = 0
        """
    ),
}
