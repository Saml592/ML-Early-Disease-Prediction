"""
logger.py
---------
Provides a single `get_logger(name)` factory that returns a logger writing
to stdout (for cloud/container environments like Render) and optionally to
a rotating log file for local development.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.utils.config import LOGS_DIR

LOG_FILE = os.path.join(LOGS_DIR, "app.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
BACKUP_COUNT = 5

# Detect if running in a cloud/container environment (Render sets this)
IS_CLOUD = os.environ.get("RENDER") or os.environ.get("IS_CLOUD")


def get_logger(name: str = "disease_prediction") -> logging.Logger:
    """
    Create (or retrieve) a logger configured with:
      - a stdout handler (INFO and above) — always on, visible in Render logs
      - a rotating file handler (DEBUG and above) — local dev only

    Args:
        name: Logger name, typically the calling module's __name__.

    Returns:
        Configured `logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured (avoid duplicate handlers on repeated imports)
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(LOG_FORMAT)

    # Always write to stdout — Render's log viewer captures stdout/stderr
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    # Also write to a rotating file in local dev (skip in cloud to avoid
    # wasting disk on an ephemeral filesystem that resets on every deploy)
    if not IS_CLOUD:
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            pass  # If logs dir isn't writable, just skip file logging

    logger.propagate = False

    return logger
