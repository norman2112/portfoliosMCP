"""Leankit Manifest converter utilities."""

import csv

from collections import defaultdict

MANIFEST_CONFIG = {
    "Setting": {"user": ["app_created_by", "app_last_updated_by"]},
    "WorkItemContainer": {
        "user": ["app_created_by", "app_last_updated_by"],
        "board": ["external_id"],
    },
    "Objective": {"user": ["app_owned_by", "app_created_by", "app_last_updated_by"]},
    "KeyResult": {"user": ["app_owned_by", "app_created_by", "app_last_updated_by"]},
    "KeyResultWorkItemMapping": {"user": ["app_created_by", "app_last_updated_by"]},
    "ProgressPoint": {"user": ["app_created_by", "app_last_updated_by"]},
    "WorkItem": {
        "user": ["app_created_by", "app_last_updated_by"],
        "card": ["external_id"],
    },
    "ActivityLog": {"user": ["app_created_by", "app_last_updated_by"]},
}


def convert_manifest(manifest_file):
    """
    Convert a Leankit Manifest file into a normalized adaptation.

    Will convert the manifest into a model-aware dict in the format of::

        {
            modelName: {
                attrib1: [(originalId, newId), ...],
                attrib2: [(originalId, newId), ...]
                ...
            },
            ...
        }

    """
    reader = csv.reader(manifest_file)
    next(reader, None)  # skip the headers

    # First, create a per-table manifest, wherein the external table name is the
    # key in a dict. Each key references an array of (original_id, nee_id) tuples.
    per_table_manifest = defaultdict(list)
    for original_id, new_id, table_name, _entity_name in reader:
        per_table_manifest[table_name].append((original_id, new_id))

    # This may not be the most efficient way to do this, but it is thorough.
    # Essentially every model's attribute that needs inspection is linked to
    # an array of ids to look through and find/replace in each model instance.
    adapted_manifest = {}
    for model_name, config in MANIFEST_CONFIG.items():
        adapted_manifest[model_name] = {}
        for external_table_name, columns in config.items():
            for column in columns:
                adapted_manifest[model_name][column] = per_table_manifest[
                    external_table_name
                ]

    return adapted_manifest
