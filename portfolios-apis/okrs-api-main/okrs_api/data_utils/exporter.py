"""Export all data."""
import copy

from open_alchemy import models

from okrs_api.model_helpers.common import (
    dictify_model,
    commit_db_session,
)
from okrs_api.data_utils.sorters.objective import objective_sorter


class ModelExporter:
    """
    Exporter for a single model.

    Apply external ids supplied by the manifest to the model, if applicable.
    """

    def __init__(
        self, db_session, model, tenant_id_str, manifest_entries=None, sorter_func=None
    ):
        """
        Initialize the ModelExporter.

        :param List manifest_entries: the manifest entries, relevant to this
        model only.
        :param Func sorter_func: the function to be run, passing in all the
        instances, and returning a sorted list of those instances, in the order
        they should be processed/inserted in the target database.

        Example of `manifest_entries`::

            {
                external_id: [(99, 11), (101, 8)],
                app_owned_by: [(222, 333), (411, 144)],
                app_created_by: [(222, 333), (411, 144)],
                app_updated_by: [(222, 333), (411, 144)],
            }

        """
        self.db_session = db_session
        self.model = model
        self.tenant_id_str = tenant_id_str
        self.manifest_entries = manifest_entries or {}
        self.sorter_func = sorter_func

    def export(self):
        """
        Export the modified attributes of the new model instance.

        Return a list of instance attributes, with the relevant external ids
        replaced according to the manifest entries.
        """
        return [
            self._export_instance(model_instance)
            for model_instance in self._all_instances()
        ]

    def _all_instances(self):
        results = (
            self.db_session.query(self.model)
            .filter_by(tenant_id_str=self.tenant_id_str)
            .all()
        )
        if not self.sorter_func:
            return results

        return self.sorter_func(results)

    def _apply_manifest_to_attribs(self, model_attribs):
        """
        Alter any ids found in the manifest, if any.

        param dict model_attribs: the attributes of a model. Since these
         attributes will undergo changes, it is recommended that this dict be
         a deepcopy of the models attributes.
        """
        if not self.manifest_entries:
            return model_attribs

        for column_name, change_list in self.manifest_entries.items():
            for original_id, new_id in change_list:
                if str(model_attribs[column_name]) == str(original_id):
                    model_attribs[column_name] = new_id
                    break

        return model_attribs

    def _export_instance(self, model_instance):
        """
        Export an instance of a model.

        Keep the original attributes of the instance in a key called "old",
        and keep the new attributes of the instance in a key called "new".

        Example::

            {
                "old": {"id": 1, "external_id": "100", ...},
                "new": {"id": 1, "external_id": "200", ...}
            }

        """
        old_attribs = dictify_model(model_instance)
        output = {"old": old_attribs}
        new_attribs = copy.deepcopy(old_attribs)
        output["new"] = self._apply_manifest_to_attribs(new_attribs)
        return output


class OrgExporter:
    """For exporting an organization."""

    MODEL_CONFIG = {
        "Setting": {},
        "WorkItemContainer": {},
        "Objective": {"sorter_func": objective_sorter},
        "KeyResult": {},
        "WorkItem": {},
        "KeyResultWorkItemMapping": {},
        "ProgressPoint": {},
        "ActivityLog": {},
    }

    def __init__(self, db_session, tenant_id_str, manifest_ids):
        """
        Initialize the org exporter.

        :param Dict manifest_ids: aggregated manifest ids, as a python structure.
        """
        self.db_session = db_session
        self.tenant_id_str = tenant_id_str
        self.manifest_ids = manifest_ids
        self.summary = {}

    def export(self):
        """Export all models for an organization."""
        output = {}
        for model_name, config in self.MODEL_CONFIG.items():
            print(f"==> Starting export for {model_name}")
            self._log_export_attempt(
                partial=True, message=f"{model_name}_started", status=False
            )
            model = getattr(models, model_name)
            manifest_entries = self.manifest_ids[model_name]
            exporter = ModelExporter(
                self.db_session,
                model,
                self.tenant_id_str,
                manifest_entries=manifest_entries,
                sorter_func=config.get("sorter_func"),
            )
            output[model_name] = exporter.export()
            self._add_to_summary(model_name, len(output[model_name]))
            self._log_export_attempt(partial=True, message=f"{model_name}_finished")
            print(f"<== Done export for {model_name}")

        self._log_export_attempt()
        output["SUMMARY"] = self.summary
        return output

    def _log_export_attempt(self, partial=False, message=None, status=True):
        """Log the export attempt in the database."""
        if not partial:
            log = models.TenantMigrationLog(
                message="EXPORT",
                original_tenant_id_str=self.tenant_id_str,
                success=True,
            )
        else:
            log = models.TenantMigrationLog(
                message=str(message),
                original_tenant_id_str=self.tenant_id_str,
                success=status,
            )
        self.db_session.add(log)
        commit_db_session(self.db_session)

    def _add_to_summary(self, model_name, exported_count):
        """Add summary information about the models."""
        model = getattr(models, model_name)
        actual_count = (
            self.db_session.query(model)
            .filter_by(tenant_id_str=self.tenant_id_str)
            .count()
        )
        self.summary[
            model_name
        ] = f"exported {exported_count} of {actual_count} records"
        return self.summary
