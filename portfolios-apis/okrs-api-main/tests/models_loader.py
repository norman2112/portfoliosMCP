"""A single, reliable way to load models on import."""
from pathlib import Path

from open_alchemy import init_yaml

ROOT_DIR = Path(__file__).parent.parent
SPECIFICATION_DIR = ROOT_DIR / "openapi"


def run_once(func):
    """Provide a wrapper that will only runt he function once."""

    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return func(*args, **kwargs)

    wrapper.has_run = False
    return wrapper


@run_once
def initialize_models():
    """Initialize the models from the openapi spec file."""
    init_yaml(SPECIFICATION_DIR / "openapi.yml")
