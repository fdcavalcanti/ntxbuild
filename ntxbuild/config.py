"""
Configuration management for NuttX builds.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any

from . import utils

# Get logger for this module
logger = logging.getLogger(__name__)

KCONFIG_TWEAK = "kconfig-tweak"


class KconfigTweakAction(str, Enum):
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    ENABLE = "--enable"
    DISABLE = "--disable"
    MODULE = "--module"
    SET_STR = "--set-str"
    SET_VAL = "--set-val"
    UNDEFINE = "--undefine"
    STATE = "--state"
    ENABLE_AFTER = "--enable-after"
    DISABLE_AFTER = "--disable-after"
    MODULE_AFTER = "--module-after"
    FILE = "--file"
    KEEP_CASE = "--keep-case"


class ConfigManager:
    """Manages NuttX build configurations."""

    def __init__(self, nuttxspace_path: Path):
        self.nuttxspace_path = nuttxspace_path
        self.nuttx_path = nuttxspace_path / "nuttx"

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def validate_config(self) -> bool:
        """Validate configuration."""
        # TODO: Implement configuration validation
        return True

    def kconfig_read(self, config: str, nuttx_dir: Path):
        """Read Kconfig file"""
        try:
            result = utils.run_kconfig_command(
                [KCONFIG_TWEAK, KconfigTweakAction.STATE, config], cwd=nuttx_dir
            )
            print(f"{config}={result.stdout.strip()}")
            return result
        except Exception as e:
            logger.error(f"Kconfig read failed: {e}")
            return 1

    def kconfig_enable(self, config: str):
        """Enable Kconfig option."""
        try:
            result = utils.run_kconfig_command(
                [KCONFIG_TWEAK, KconfigTweakAction.ENABLE, config], cwd=self.nuttx_path
            )
            print(f"{config}={result.stdout.strip()}")
            return result
        except Exception as e:
            logger.error(f"Kconfig read failed: {e}")
            return 1

    def kconfig_disable(self, config: str):
        """Disable Kconfig option."""
        try:
            result = utils.run_kconfig_command(
                [KCONFIG_TWEAK, KconfigTweakAction.DISABLE, config], cwd=self.nuttx_path
            )
            print(f"{config}={result.stdout.strip()}")
            return result
        except Exception as e:
            logger.error(f"Kconfig read failed: {e}")
            return 1

    def kconfig_apply_changes(self, nuttx_dir: Path):
        """Show all Kconfig options"""
        try:
            result = utils.run_make_command(["make", "olddefconfig"], cwd=nuttx_dir)
            return result
        except Exception as e:
            logger.error(f"Kconfig apply changes failed: {e}")
            return 1

    def kconfig_set_value(self, config: str, value: str, nuttx_dir: Path):
        """Set Kconfig value"""
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Value must be numerical")

        try:
            result = utils.run_kconfig_command(
                [KCONFIG_TWEAK, KconfigTweakAction.SET_VAL, config, str(value)],
                cwd=nuttx_dir,
            )
            return result.returncode
        except Exception as e:
            logger.error(f"Kconfig set value failed: {e}")
            return 1

    def kconfig_set_str(self, config: str, value: str, nuttx_dir: Path):
        """Set Kconfig string"""
        try:
            result = utils.run_kconfig_command(
                [KCONFIG_TWEAK, KconfigTweakAction.SET_STR, config, value],
                cwd=nuttx_dir,
            )
            return result.returncode
        except Exception as e:
            logger.error(f"Kconfig set string failed: {e}")
            return 1
