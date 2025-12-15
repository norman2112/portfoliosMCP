"""
Module for converting data migration manifests.

A planview product team may supply a manifest. That manifest will got through
the appropriate converter into a standardized format that the exporter can
use to substitute external api data.
"""

import importlib


AVAILABLE_PRODUCT_TYPES = "leankit"
BASE_MANIFESTS_PATH = "okrs_api.data_utils.manifests"


def manifest_converter(manifest_file, product_type="leankit"):
    """
    Import the appropriate Converter and run it.

    Return the resulting json adapted manifest.
    """

    if product_type not in AVAILABLE_PRODUCT_TYPES:
        raise KeyError(f"product_type {product_type} was not found")

    full_module_path = f"{BASE_MANIFESTS_PATH}.{product_type}"
    module = importlib.import_module(full_module_path)
    return module.convert_manifest(manifest_file)
