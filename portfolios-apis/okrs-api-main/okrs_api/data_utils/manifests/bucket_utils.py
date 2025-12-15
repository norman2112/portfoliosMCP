"""Responsible for downloading the manifest."""
from datetime import date
import json
import os

import boto3

from okrs_api.model_helpers.common import default_json_converter


class ManifestConductor:
    """Handles manifest import and exports."""

    PRODUCTION_ENVIRONMENTS = ["production"]
    AVAILABLE_PRODUCT_TYPES = ["leankit"]
    LEANKIT_BUCKET_BASE = "leankit-manifests-"
    OKRS_BUCKET_BASE = "platforma-okrs-"
    SAVED_PRODUCT_MANIFEST_FILE = "/tmp/leankit-manifest.csv"
    SAVED_ADAPTED_MANIFEST_FILE = "/tmp/adapted-manifest.json"

    def __init__(self, product_type, original_tenant_id_str):
        """
        Initialize the manifest conductor.

        :param string product_type: planview product type
        :param string original_tenant_id_str: tenant_id_str of the moving tenant
        """
        self.product_type = product_type
        self.original_tenant_id_str = original_tenant_id_str
        self.base_adapted_filename = f"{date.today()}-adapted-manifest.json"
        self.s3 = boto3.client("s3")

    def download_product_manifest(self, manifest_filename):
        """
        Download the manifest from the Planview product.

        Step 1 of the 3-part process.
        """
        self.s3.download_file(
            self._get_product_manifest_bucket_name(),
            manifest_filename,
            self.SAVED_PRODUCT_MANIFEST_FILE,
        )
        return self.SAVED_PRODUCT_MANIFEST_FILE

    def upload_adapted_manifest(self, adapted_manifest_data):
        """
        Upload the adapted (JSON) manifest to the appropriate place.

        Step 2 of the 3-part process.

        :param dict adapted_manifest_data: the adapted manifest data to be
        written to the filesystem.
        """
        adapted_manifest_file = self._save_adapted_manifest_locally(
            adapted_manifest_data
        )
        upload_filename = self._adapted_manifest_upload_filename()
        self.s3.upload_file(
            adapted_manifest_file, self._okrs_bucket_name(), upload_filename
        )

    def download_adapted_manifest(self):
        """
        Download our adapted (JSON) manifest from our s3 bucket.

        Step 3 of the 3-part process. Download the latest adapted manifest
        file and save it in the /tmp directory.
        """
        self.s3.download_file(
            self._okrs_bucket_name(),
            self._adapted_manifest_download_filename(),
            self.SAVED_ADAPTED_MANIFEST_FILE,
        )
        return self.SAVED_ADAPTED_MANIFEST_FILE

    @property
    def _environment(self):
        """Get the current environment string for this app."""
        env_str = os.environ.get("CONNEXION_ENVIRONMENT") or "development"
        return env_str.lower()

    def _get_product_manifest_bucket_name(self):
        product_type = (
            self.product_type
            if self.product_type in self.AVAILABLE_PRODUCT_TYPES
            else None
        )
        return getattr(self, f"_{product_type}_bucket_name", None)()

    def _local_output_filename(self):
        """Return the output filename for the okrs manifest."""
        return f"/tmp/{self.base_adapted_filename}"

    def _save_adapted_manifest_locally(self, adapted_manifest_data):
        """Save the adapted manifest as a json file."""
        output_filename = self._local_output_filename()
        json_manifest = json.dumps(
            adapted_manifest_data, default=default_json_converter
        )
        with open(output_filename, "w") as f:
            f.write(json_manifest)

        return output_filename

    def _adapted_manifest_directory_name(self):
        """
        Return the directory portion of the adapted manifest.

        Directory is in the form of {product_type}/{tenant_id_str}.
        """
        return f"{self.product_type}/{self.original_tenant_id_str}"

    def _is_production_env(self):
        return self._environment == "production"

    def _okrs_bucket_suffix(self):
        """Return the okrs bucket suffix based on the current env."""
        if self._is_production_env():
            return "production"

        return "development"

    def _okrs_bucket_name(self):
        """Return the bucket for okrs."""
        return f"{self.OKRS_BUCKET_BASE}{self._okrs_bucket_suffix()}"

    def _okrs_bucket(self):
        """Return the OKRs bucket."""
        return self.s3.bucket(self._okrs_bucket_name())

    def _leankit_bucket_suffix(self):
        """Return the leankit bucket suffix, based on env."""
        if self._is_production_env():
            return "prod"

        return "dev"

    def _leankit_bucket_name(self):
        """Return the leankit bucket name."""
        return f"{self.LEANKIT_BUCKET_BASE}{self._leankit_bucket_suffix()}"

    def _all_adapted_manifest_filenames_for_tenant(self):
        """
        Return the bucket contents of the okrs bucket.

        Filter the s3 file names just based on product type.
        Sort them in descending order. This should give us the most recent
        filename for the product type at the beginning of the list.
        """
        bucket_contents = self.s3.list_objects_v2(
            Bucket=self._okrs_bucket_name(),
            Prefix=f"{self._adapted_manifest_directory_name()}/",
        )["Contents"]
        filenames = [obj["Key"] for obj in bucket_contents]
        filenames.sort(reverse=True)
        return filenames

    def _adapted_manifest_download_filename(self):
        """
        Return the latest adapted manifest file from the bucket.

        This filename must be formatted in a way wherein the product type
        (e.g 'leankit', 'projectplace' etc) matches the product type we're
        attempting to import.
        """
        manifest_filenames = self._all_adapted_manifest_filenames_for_tenant()
        if not manifest_filenames:
            raise FileNotFoundError(
                "No adapted manifests for this product type are "
                "present in the S3 bucket."
            )

        return manifest_filenames[0]

    def _adapted_manifest_upload_filename(self):
        """
        Return the name of the adapted manifest filename to upload.

        The upload filename will be directory-keyed.
        """
        return f"{self._adapted_manifest_directory_name()}/{self.base_adapted_filename}"
