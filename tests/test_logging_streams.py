import logging
import sys
from pathlib import Path


# Ensure `src/` is on the import path when running tests from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def test_setup_logging_uses_stderr_for_stream_handlers():
    from planview_portfolios_mcp.logging_config import setup_logging

    logger = setup_logging()

    stream_handlers = [
        handler
        for handler in logger.handlers
        if isinstance(handler, logging.StreamHandler)
    ]
    assert stream_handlers, "Expected at least one stream handler on app logger"
    assert all(
        handler.stream is sys.stderr for handler in stream_handlers
    ), "All app logger stream handlers must write to stderr"


def test_setup_logging_rewrites_root_stdout_handler_to_stderr():
    from planview_portfolios_mcp.logging_config import setup_logging

    root_logger = logging.getLogger()
    old_handlers = list(root_logger.handlers)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    root_logger.addHandler(stdout_handler)
    try:
        setup_logging()
        rewritten_stream_handlers = [
            handler
            for handler in root_logger.handlers
            if isinstance(handler, logging.StreamHandler)
        ]
        assert all(
            handler.stream is not sys.stdout for handler in rewritten_stream_handlers
        ), "Root stream handlers must not write to stdout"
    finally:
        root_logger.removeHandler(stdout_handler)
        for handler in list(root_logger.handlers):
            if handler not in old_handlers:
                root_logger.removeHandler(handler)
