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
    """Enumeration of kconfig-tweak actions.

    This enum defines the available actions that can be performed
    using the kconfig-tweak tool.
    """

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
    """Manages NuttX build configurations.

    This class provides methods to read, modify, and manage Kconfig
    options for NuttX builds.
    """

    def __init__(self, nuttxspace_path: Path, nuttx_dir: str = "nuttx"):
        """Initialize the ConfigManager.

        Args:
            nuttxspace_path: Path to the NuttX repository workspace.
            nuttx_dir: Name of the NuttX OS directory within the workspace.
                Defaults to "nuttx".
        """
        self.nuttxspace_path = Path(nuttxspace_path)
        self.nuttx_path = self.nuttxspace_path / nuttx_dir

    def kconfig_read(self, config: str) -> str:
        """Read the current state of a Kconfig option.

        Reads and prints the current value of a Kconfig option to stdout.

        Args:
            config: The name of the Kconfig option to read.

        Returns:
            str: The current value of the Kconfig option.
        """
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.STATE, config], cwd=self.nuttx_path
        )
        value = result.stdout.strip()
        print(f"{config}={value}")
        return value

    def kconfig_enable(self, config: str) -> int:
        """Enable a Kconfig option.

        Args:
            config: The name of the Kconfig option to enable.

        Returns:
            int: Exit code of the kconfig-tweak command. Returns 0 on success,
                non-zero on failure.
        """
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.ENABLE, config], cwd=self.nuttx_path
        )
        logging.info(f"Kconfig enable: {config}")
        return result.returncode

    def kconfig_disable(self, config: str) -> int:
        """Disable a Kconfig option.

        Args:
            config: The name of the Kconfig option to disable.

        Returns:
            int: Exit code of the kconfig-tweak command. Returns 0 on success,
                non-zero on failure.
        """
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.DISABLE, config], cwd=self.nuttx_path
        )
        logging.info(f"Kconfig disable: {config}")
        return result.returncode

    def kconfig_apply_changes(self) -> int:
        """Apply Kconfig changes by running olddefconfig.

        This method runs 'make olddefconfig' to apply any pending
        Kconfig changes and update the configuration.

        Returns:
            int: Exit code of the make command. Returns 0 on success,
                non-zero on failure.
        """
        result = utils.run_make_command(["make", "olddefconfig"], cwd=self.nuttx_path)
        if result.returncode != 0:
            logging.error("Kconfig change apply may have failed")
        else:
            logging.info("Kconfig changes applied")
        return result.returncode

    def kconfig_set_value(self, config: str, value: str) -> int:
        """Set a numerical Kconfig option value.

        Args:
            config: The name of the Kconfig option.
            value: The numerical value to set. Must be convertible to int.

        Returns:
            int: Exit code of the kconfig-tweak command. Returns 0 on success,
                non-zero on failure.

        Raises:
            ValueError: If the value cannot be converted to an integer.
        """
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
        """Set a string Kconfig option value.

        Args:
            config: The name of the Kconfig option.
            value: The string value to set.

        Returns:
            int: Exit code of the kconfig-tweak command. Returns 0 on success,
                non-zero on failure.
        """
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.SET_STR, config, value],
            cwd=self.nuttx_path,
        )
        logging.info(f"Kconfig set string: {config}={value}")
        return result.returncode

    def kconfig_menuconfig(self) -> int:
        """Run the interactive menuconfig interface.

        Opens the menuconfig interface for interactive Kconfig editing.
        This is a curses-based interface that allows interactive configuration
        of Kconfig options.

        Returns:
            int: Exit code of the menuconfig command. Returns 0 on success,
                non-zero on failure.
        """
        logging.debug("Opening menuconfig")
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.MENUCONFIG], cwd=self.nuttx_path
        )
        return result.returncode

    def kconfig_merge_config_file(
        self, source_file: str, config_file: str = None
    ) -> int:
        """Merge a Kconfig file into the current configuration.

        Merges configuration options from a source file into the target
        configuration file using kconfig-merge.

        Args:
            source_file: Path to the source configuration file to merge.
            config_file: Path to the target configuration file. If None,
                defaults to .config in the NuttX directory.

        Returns:
            int: Exit code of the kconfig-merge command. Returns 0 on success,
                non-zero on failure.

        Raises:
            ValueError: If source_file is not provided or is empty.
        """
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
