"""Logging configuration for Planview Portfolios MCP server."""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from .config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "tool_name"):
            log_data["tool_name"] = record.tool_name
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "count"):
            log_data["count"] = record.count
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type

        return json.dumps(log_data)


def setup_logging():
    """Configure logging for the application."""
    logger = logging.getLogger("planview_portfolios_mcp")
    logger.setLevel(settings.log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    if settings.log_format == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

    logger.addHandler(console_handler)

    # Optional file handler
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger


# Create logger instance
logger = setup_logging()
