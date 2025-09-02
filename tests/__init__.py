"""
NuttX Build System Assistant

A Python package to assist with NuttX build system operations.
"""

__version__ = "0.1.0"
__author__ = "NuttX Community"
__description__ = "NuttX Build System Assistant"

from . import build
from . import config
from . import utils

__all__ = ["build", "config", "utils"]
