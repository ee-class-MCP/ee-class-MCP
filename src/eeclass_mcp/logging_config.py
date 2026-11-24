"""Logging configuration for stdio MCP server.

All logs MUST go to sys.stderr because sys.stdout is reserved for MCP JSON-RPC messages.
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configure root and package loggers to write strictly to stderr."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries unless DEBUG is requested.
    if numeric_level > logging.DEBUG:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
