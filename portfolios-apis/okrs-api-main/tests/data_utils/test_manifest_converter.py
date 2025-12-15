"""Test data_utils endpoints."""

from pathlib import Path

import pytest

from okrs_api.data_utils.manifests import leankit

MANIFEST_DATA_FILE = Path(__file__).parent / "manifests" / "manifest_test_data.csv"


@pytest.fixture(scope="module")
def manifest_ids():
    """The .csv manifest file that we receive from leankit."""
    with open(MANIFEST_DATA_FILE, "r+") as f:
        return leankit.convert_manifest(f)


class TestLeankitConverter:
    @pytest.mark.integration
    def test_convert_manifest(self, manifest_ids):
        """
        Ensure the manifest_ids has the id replacements.

        Every column specified for every model should have a list of id
        replacements.

        Example::

            {
                "Objective": {
                    "app_owned_by": [(100, 200), (300, 400)],
                    "app_created_by": [(100, 200), (300, 400)],
                    ...
                },
                ...
            }

        """

        expected_model_keys = {
            "Setting",
            "WorkItemContainer",
            "Objective",
            "KeyResult",
            "KeyResultWorkItemMapping",
            "ProgressPoint",
            "WorkItem",
            "ActivityLog",
        }
        objective_manifest = manifest_ids["Objective"]
        assert set(manifest_ids.keys()) == expected_model_keys
        assert {"app_owned_by", "app_created_by", "app_last_updated_by"}.issubset(
            set(objective_manifest.keys())
        )
