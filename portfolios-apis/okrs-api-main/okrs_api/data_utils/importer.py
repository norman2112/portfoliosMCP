"""Importer methods to import model attributes from another system."""

from collections import defaultdict
import json

from open_alchemy import models
from inflection import camelize

from okrs_api.model_helpers.common import commit_db_session


def setify_dict(d):
    """Return a set from a dict, with all values stringified as well."""
    return set({k: str(v) for k, v in d.copy().items()}.items())


def attribs_diff(attribs1, attribs2):
    """
    Find the differences between the two sets of attributes.

    Return the differences in a dict.
    """
    # First typecast all values in the attribs as strings and convert to a set.
    set1 = setify_dict(attribs1.copy())
    set2 = setify_dict(attribs2.copy())
    return dict(set2 - set1)


class PrimaryKeyMap:
    """
    Mapper for original ids to new ids.

    `ID_MAP` holds all values, ordered by model name.

    Example::

        {
            "Objective": [(1, 200), (2, 211), (3, 999)],
            "KeyResult": [(4, 43), (5, 66), (6, 89)],
            ...
        }
    """

    def __init__(self):
        """Initialize the key map."""
        self.id_map = defaultdict(list)

    def add(self, model_name, original_id, new_id):
        """Add an original_id, new_id pairing to the map if it does not exist."""
        if not self.find_new_id(model_name, original_id):
            self.id_map[model_name].append((original_id, new_id))

        return original_id, new_id

    def find_new_id(self, model_name, original_id):
        """Find the new id for the original id and model given."""
        for o_id, new_id in self.id_map[model_name]:
            if o_id == original_id:
                return new_id

        return None

    def find_original_id(self, model_name, new_id):
        """Find the original id for the new id and model given."""
        for original_id, n_id in self.id_map[model_name]:
            if n_id == new_id:
                return original_id

        return None


class ImportLogger:
    """
    The logger for all Import-related activity.

    The logger will log original data (via information in the export file), and the
     final data after import, logging each entry.
    """

    def __init__(self):
        """Initialize the import logger."""
        self.import_logs = defaultdict(list)

    def log(self, model_name, original_attribs, new_attribs):
        """
        Log the attributes and difference for each entry.

        Group by model name.
        """

        self.import_logs[model_name].append(
            {
                "original": original_attribs,
                "new": new_attribs,
                "diff": attribs_diff(original_attribs, new_attribs),
            }
        )

    def log_error(self, message, model_name=None, attribs=None):
        """
        Log an error message.

        :param message: The message to be logged.
        :param model_name: The name of the model we are using
        :param attribs: The attribs associated with the model for the error
        """

        self.import_logs["ERRORS"].append(
            {"message": message, "model": model_name, "attribs": attribs}
        )

    def log_warning(self, message, model_name=None, attribs=None):
        """
        Log a warning message.

        :param message: The message to be logged.
        :param model_name: The name of the model we are using
        :param attribs: The attribs associated with the model for the error
        """

        self.import_logs["WARNINGS"].append(
            {"message": message, "model": model_name, "attribs": attribs}
        )

    def errors(self):
        """Return just the errors from the import logs."""
        return self.import_logs.get("ERRORS")

    def set_summary(self, summary):
        """Set the SUMMARY key in the import logs."""
        self.import_logs["SUMMARY"] = summary
        return self.import_logs


class ForeignKeyReplacer:
    """Replace foreign key model attribs with replacement/new foreign key ids."""

    FOREIGN_KEY_CONFIG = {
        "Objective": [
            ("parent_objective_id", "Objective"),
            ("work_item_container_id", "WorkItemContainer"),
        ],
        "KeyResult": [("objective_id", "Objective")],
        "KeyResultWorkItemMapping": [
            ("key_result_id", "KeyResult"),
            ("work_item_id", "WorkItem"),
        ],
        "ProgressPoint": [("key_result_id", "KeyResult")],
        "ActivityLog": [
            ("objective_id", "Objective"),
            ("key_result_id", "KeyResult"),
            ("work_item_id", "WorkItem"),
            ("progress_point_id", "ProgressPoint"),
        ],
        "WorkItem": [("work_item_container_id", "WorkItemContainer")],
        "WorkItemContainerRole": [("work_item_container_id", "WorkItemContainer")],
    }

    @classmethod
    def replace_foreign_keys(cls, model_name, original_attribs, primary_key_map):
        """
        Return the original attribs of the model, with the foreign keys replaced.

        :param str model_name: the name of the model
        :param dict original_attribs: the original attribs for this model
        :param PrimaryKeyMap primary_key_map: the map of ids for this import
        """
        new_attribs = original_attribs.copy()
        new_attribs.pop("id")
        fk_configs = cls.FOREIGN_KEY_CONFIG.get(model_name)
        if fk_configs:
            for column_name, fk_model_name in fk_configs:
                new_attribs[column_name] = primary_key_map.find_new_id(
                    fk_model_name, original_attribs[column_name]
                )

        return new_attribs


class DataImporter:
    """Importer class for export files."""

    def __init__(
        self,
        db_session,
        adapted_manifest_file,
        new_tenant_id_str,
        new_tenant_group_id_str=None,
    ):
        """
        Initialize the export file.

        The export file contains all the old data from the old okrs-api instance,
        with external ids replaced.
        """
        self.db_session = db_session
        self.adapted_manifest_file = adapted_manifest_file
        self.new_tenant_id_str = new_tenant_id_str
        self.new_tenant_group_id_str = new_tenant_group_id_str
        self.original_tenant_id_str = None
        self.has_been_run = False
        self.import_logger = ImportLogger()
        self.key_map = PrimaryKeyMap()
        self.summary = {}
        self.memo = {}
        self._export_summary = {}

    @property
    def successful(self):
        """Return if this import was successful or not."""
        return bool(self.has_been_run and not self.import_logger.errors())

    def adapted_manifest_data(self):
        """
        Return only the data should be imported.

        This will only return keys and data from the manifest file that are
        camelcase. Any keys that are not UpperCamelCase will be discarded as
        diagnostic data. e.g. SUMMARY, ERRORS.

        Memoize the result.
        """
        if not self.memo.get("adapted_manifest_data"):
            all_data = json.load(self.adapted_manifest_file)
            self._export_summary = all_data.get("SUMMARY", {})
            self.memo["adapted_manifest_data"] = {
                key: value
                for (key, value) in all_data.items()
                if self._valid_model_name(key)
            }

        return self.memo["adapted_manifest_data"]

    def apply_adapted_manifest(self):
        """Import and apply data from an adapted manifest."""
        self.has_been_run = True
        data = self.adapted_manifest_data()
        for model_name, attrib_change_list in data.items():
            print(f"Importing for {model_name}")
            self._log_import_attempt(
                partial=True, message=f"{model_name}_started", status=False
            )
            for changes in attrib_change_list:
                # Set the original tenant id str, as pulled from the first
                # entry in the export file.
                if not self.original_tenant_id_str:
                    self.original_tenant_id_str = changes["old"].get("tenant_id_str")

                original_id = changes["new"]["id"]
                prepped_attribs = self._prepare_attributes_for_insert(
                    model_name, changes["new"]
                )
                new_instance = self._insert_record(model_name, prepped_attribs)
                if new_instance:
                    self.key_map.add(model_name, original_id, new_instance.id)
                    prepped_attribs["id"] = new_instance.id
                    self.import_logger.log(
                        model_name,
                        original_attribs=changes["old"],
                        new_attribs=prepped_attribs,
                    )
            print(f"Import done for {model_name}")
            self._log_import_attempt(
                partial=True, message=f"{model_name}_finished", status=True
            )
            self._add_to_summary(model_name, len(data[model_name]))
        self._log_import_attempt()
        return self.import_logger.set_summary(self.summary)

    def _prepare_attributes_for_insert(self, model_name, original_attribs):
        """
        Prepare data for insertion.

        This will
            - replace all foreign keys with the new foreign keys.
            - set the new `tenant_id_str`
        """

        attribs_v2 = ForeignKeyReplacer.replace_foreign_keys(
            model_name=model_name,
            original_attribs=original_attribs,
            primary_key_map=self.key_map,
        )
        attribs_v2["tenant_id_str"] = self.new_tenant_id_str
        if self.new_tenant_group_id_str is not None:
            attribs_v2["tenant_group_id_str"] = self.new_tenant_group_id_str
        return attribs_v2

    def _add_to_summary(self, model_name, manifest_count):
        """
        Add information to the summary.

        param str model_name: the name of the model imported
        """
        model = getattr(models, model_name)
        actual_count = (
            self.db_session.query(model)
            .filter_by(tenant_id_str=self.new_tenant_id_str)
            .count()
        )
        self.summary[
            model_name
        ] = f"imported {actual_count} records of {manifest_count} in manifest"
        return self.summary

    @staticmethod
    def _remove_generated_fields(attribs):
        """Remove from attribs the fields which are calculated."""

        generated_fields = ["pv_tenant_id", "pv_created_by", "pv_last_updated_by"]

        for field in generated_fields:
            if field in attribs:
                del attribs[field]

    @staticmethod
    def _should_skip_insert(model_name, attribs):
        """Check if we have a special case and skip insert."""

        # Special case - 1
        # Data created before July-2021 was hard removed (as opposed to soft deleted).
        # Hence creating deleted objective history in ActivityLog would cause trouble
        # if those `removed` objectives do not exist in the DB.
        # In such scenarios we skip the insert.
        if (model_name == "ActivityLog") and (not attribs["objective_id"]):
            return True

        # Default case - do not skip
        return False

    def _insert_record(self, model_name, attribs):
        """Insert a new record into the table."""
        model_cls = getattr(models, model_name)
        self._remove_generated_fields(attribs)

        if self._should_skip_insert(model_name, attribs):
            self.import_logger.log_warning(
                "Skip insert for special cases", model_name=model_name, attribs=attribs
            )
            return None

        instance = model_cls(**attribs)
        self.db_session.add(instance)
        try:
            self.db_session.commit()
            return instance
        except Exception as e:
            self.db_session.rollback()
            print("ERROR: Migration insert failed for ", e)
            self.import_logger.log_error(f"{str(e)}", model_name, attribs)

    def _log_import_attempt(self, partial=False, message=None, status=True):
        """Log the import attempt in the database."""
        if not partial:
            log = models.TenantMigrationLog(
                message="IMPORT",
                original_tenant_id_str=self.original_tenant_id_str,
                new_tenant_id_str=self.new_tenant_id_str,
                success=self.successful,
            )
        else:
            log = models.TenantMigrationLog(
                message=message,
                original_tenant_id_str=self.original_tenant_id_str,
                new_tenant_id_str=self.new_tenant_id_str,
                success=status,
            )

        self.db_session.add(log)
        commit_db_session(self.db_session)

    def _valid_model_name(self, model_name):
        """
        Return bool if model name is camelcase.

        Only upper-CamelCase names are valid model names.
        Cannot be ALL UPPER CASE.
        """
        matches_camelcase = camelize(model_name, True) == model_name
        all_uppercase = model_name.isupper()
        return matches_camelcase and not all_uppercase

    @property
    def export_summary(self):
        """Return the export summary from adapter manifest."""

        return self._export_summary
