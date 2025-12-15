"""Utility functions for importing and determining event handlers."""

import importlib

from inflection import pluralize, underscore

BASE_HANDLERS_IMPORT_PATH = "okrs_api.hasura.events.handlers"


def deduce_module_name(instance):
    """
    Return the module name for this instance.

    This should be the same as the table name.
    """
    cls_name = type(instance).__name__
    underscore_name = underscore(cls_name)
    return pluralize(underscore_name)


def handler_cls(module_name, base_path=None):
    """Return the handler class or an error."""

    base_path = base_path or BASE_HANDLERS_IMPORT_PATH
    full_module_path = f"{base_path}.{module_name}"
    module = importlib.import_module(full_module_path)
    # `Handler` class in that module.
    return getattr(module, "Handler")
