"""
logger.py
---------
Provides a single `get_logger(name)` factory that returns a logger writing
to both the console and a rotating log file under `logs/`.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from src.utils.config import LOGS_DIR

LOG_FILE = os.path.join(LOGS_DIR, "app.log")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
BACKUP_COUNT = 5


def get_logger(name: str = "disease_prediction") -> logging.Logger:
    """
    Create (or retrieve) a logger configured with:
      - a console handler (INFO and above)
      - a rotating file handler (DEBUG and above), capped at 5MB x 5 files

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

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger
