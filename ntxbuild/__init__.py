"""
NuttX Build System Assistant

A Python package to assist with NuttX build system operations.
"""

import logging
import sys
from importlib.metadata import PackageNotFoundError, version
from logging.handlers import RotatingFileHandler

from . import build, config, utils

__all__ = ["build", "config", "utils"]

DEFAULT_LOG_FILE_NAME = "ntxbuild.log"
DEFAULT_LOG_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_LOG_BACKUP_COUNT = 3


def _setup_logging():
    """Setup logging configuration for the ntxbuild library."""
    # Create logs directory if it doesn't exist
    log_dir = utils.NTXBUILD_DEFAULT_USER_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / DEFAULT_LOG_FILE_NAME

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=DEFAULT_LOG_MAX_BYTES,
        backupCount=DEFAULT_LOG_BACKUP_COUNT,
    )

    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console output
            file_handler,  # Rotated log file output
        ],
    )

    logger = logging.getLogger("ntxbuild")
    logger.setLevel(logging.WARNING)


# Setup logging when module is imported
_setup_logging()

try:
    __version__ = version("ntxbuild")
except PackageNotFoundError:
    # Package metadata is unavailable in source-only/dev contexts.
    __version__ = "0+unknown"
__author__ = "Filipe Cavalcanti"
__description__ = "NuttX Build System Assistant"
