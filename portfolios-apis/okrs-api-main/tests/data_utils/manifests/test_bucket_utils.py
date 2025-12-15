import json
from pathlib import Path

import pytest

from okrs_api.data_utils.manifests.bucket_utils import ManifestConductor

ADAPTED_MANIFEST_FILE = Path(__file__).parent.resolve() / "adapted_test_manifest.json"


class TestManifestConductor:
    TENANT_ID_STR = "LEANKIT~d09-123456789"

    @pytest.mark.vcr
    def test_upload_adapted_manifest(self, mocker):
        """Ensure that the manifest can be uploaded."""
        with open(ADAPTED_MANIFEST_FILE, "r") as f:
            adapted_manifest_data = json.load(f)

        conductor = ManifestConductor("leankit", self.TENANT_ID_STR)
        # By patching the output filename, we can guarantee that vcr will replay
        # the api call to S3 properly.
        mocker.patch.object(
            conductor, "_local_output_filename", return_value=str(ADAPTED_MANIFEST_FILE)
        )
        mocker.patch.object(
            conductor, "base_adapted_filename", "test-adapted-manifest.json"
        )

        conductor.upload_adapted_manifest(adapted_manifest_data)

    @pytest.mark.vcr
    def test_download_adapted_manifest(self):
        """Ensure that the adapted manifest can be downloaded for import."""
        conductor = ManifestConductor("leankit", self.TENANT_ID_STR)
        filename = conductor.download_adapted_manifest()
        assert filename == "/tmp/adapted-manifest.json"

    def test_download_adapted_manifest_no_file(self, mocker):
        """
        Ensure raise of error when no adapted manifest found.

        If we cannot find an adapted manifest for the product_type,
        then we raise an error.
        """
        conductor = ManifestConductor("leankit", self.TENANT_ID_STR)
        mocker.patch.object(
            conductor, "_all_adapted_manifest_filenames_for_tenant", return_value=[]
        )
        with pytest.raises(FileNotFoundError) as err:
            conductor.download_adapted_manifest()

        assert "No adapted manifests for this product type" in str(err.value)
