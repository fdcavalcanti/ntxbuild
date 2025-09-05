"""
NuttX Build System Assistant

A Python package to assist with NuttX build system operations.
"""

import logging
import sys
from pathlib import Path

from . import build, config, utils

__all__ = ["build", "config", "utils"]


# Configure logging for the library
def _setup_logging():
    """Setup logging configuration for the ntxbuild library."""
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".ntxbuild" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging.
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console output
        ],
    )

    # Set our library logger level
    logger = logging.getLogger("ntxbuild")
    logger.setLevel(logging.WARNING)


# Setup logging when module is imported
_setup_logging()

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version

try:
    __version__ = version("ntxbuild")
except PackageNotFoundError:
    # Package is not installed, fallback to development version
    __version__ = "0.1.0+dev"
__author__ = "Filipe Cavalcanti"
__description__ = "NuttX Build System Assistant"
