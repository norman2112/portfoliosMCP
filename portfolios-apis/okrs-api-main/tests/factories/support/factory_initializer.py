"""Used to initialize Factories from FactoryBot."""
import glob
import importlib
from pathlib import Path

from inflection import camelize
from mock_alchemy.mocking import UnifiedAlchemyMagicMock


FACTORIES_DIR = Path(__file__).parent.parent
FACTORIES_IMPORT_PATH = "tests.factories"

# Used for memoization.
FACTORY_MODULE_NAMES = []
FACTORY_CLASSES = []


def import_factories():
    """
    Import factories. Returns the factory classes.

    Memoize the result in the FACTORY_CLASSED global.
    """
    global FACTORY_CLASSES
    if not FACTORY_CLASSES:
        for factory_module in _get_factory_module_names():
            full_module_path = f"{FACTORIES_IMPORT_PATH}.{factory_module}"
            module = importlib.import_module(full_module_path)
            factory_cls = camelize(f"{factory_module}_factory")
            FACTORY_CLASSES.append(getattr(module, factory_cls))

    return FACTORY_CLASSES


def add_db_session_to_factories(db_session=None):
    """
    Initialize all factories with a db_session of your choice.

    If you do not provide one, a mock db_session will be used.
    This will return the db_session at the end of initialization.
    """
    db_session = db_session or UnifiedAlchemyMagicMock()

    for factory_cls in import_factories():
        # An abstract class does not have a db_session attached.
        if not factory_cls._meta.abstract:
            factory_cls._meta.sqlalchemy_session = db_session

    return db_session


def _get_factory_module_names():
    """
    Return all valid factory module names in the `tests/factories/` directory.

    This ignores files like __init__.py and any directories.
    Memoize the results in the FACTORY_MODULE_NAMES global.
    """
    global FACTORY_MODULE_NAMES
    if not FACTORY_MODULE_NAMES:
        all_files = glob.glob(f"{FACTORIES_DIR}/[a-z]*.py")
        FACTORY_MODULE_NAMES = [Path(f).stem for f in all_files]

    return FACTORY_MODULE_NAMES
