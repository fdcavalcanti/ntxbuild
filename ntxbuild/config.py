"""
Configuration management for NuttX builds.
"""

import logging
from enum import Enum
from pathlib import Path

from . import utils

# Get logger for this module
logger = logging.getLogger("ntxbuild.config")

KCONFIG_TWEAK = "kconfig-tweak"
KCONFIG_MERGE = "kconfig-merge"


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

    def __init__(self, nuttxspace_path: Path, nuttx_dir: str = "nuttx"):
        self.nuttxspace_path = nuttxspace_path
        self.nuttx_path = nuttxspace_path / nuttx_dir

    def kconfig_read(self, config: str) -> str:
        """Read Kconfig file"""
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.STATE, config], cwd=self.nuttx_path
        )
        value = result.stdout.strip()
        print(f"{config}={value}")
        return value

    def kconfig_enable(self, config: str) -> int:
        """Enable Kconfig option."""
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.ENABLE, config], cwd=self.nuttx_path
        )
        logging.info(f"Kconfig enable: {config}")
        return result.returncode

    def kconfig_disable(self, config: str) -> int:
        """Disable Kconfig option."""
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.DISABLE, config], cwd=self.nuttx_path
        )
        logging.info(f"Kconfig disable: {config}")
        return result.returncode

    def kconfig_apply_changes(self) -> int:
        """Show all Kconfig options"""
        result = utils.run_make_command(["make", "olddefconfig"], cwd=self.nuttx_path)
        if result.returncode != 0:
            logging.error("Kconfig change apply may have failed")
        else:
            logging.info("Kconfig changes applied")
        return result.returncode

    def kconfig_set_value(self, config: str, value: str) -> int:
        """Set Kconfig value"""
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Value must be numerical")

        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.SET_VAL, config, str(value)],
            cwd=self.nuttx_path,
        )
        logging.info(f"Kconfig set value: {config}={value}")
        return result.returncode

    def kconfig_set_str(self, config: str, value: str) -> int:
        """Set Kconfig string"""
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.SET_STR, config, value],
            cwd=self.nuttx_path,
        )
        logging.info(f"Kconfig set string: {config}={value}")
        return result.returncode

    def kconfig_menuconfig(self) -> int:
        """Run menuconfig"""
        logging.debug("Opening menuconfig")
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.MENUCONFIG], cwd=self.nuttx_path
        )
        return result.returncode

    def kconfig_merge_config_file(
        self, source_file: str, config_file: str = None
    ) -> int:
        """Merge Kconfig file"""
        if not source_file:
            raise ValueError("Source file is required")

        if not config_file:
            config_file = (Path(self.nuttx_path) / ".config").as_posix()

        logging.info(f"Kconfig merge config file: {source_file} into {config_file}")

        source_file = Path(source_file).resolve().as_posix()
        result = utils.run_kconfig_command(
            [KCONFIG_MERGE, "-m", config_file, source_file], cwd=self.nuttx_path
        )
        return result.returncode
