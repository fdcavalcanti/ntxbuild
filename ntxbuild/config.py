"""
Configuration management for NuttX builds.

This module provides classes and utilities for managing Kconfig-based
configuration for NuttX builds, including reading, modifying, and merging
configuration options.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from pathlib import Path

import kconfiglib

from . import utils
from .build import BuildTool

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


@dataclass(frozen=True)
class KconfigEnvironmentContext:
    """Context manager for Kconfig environment variables.

    Manages the environment variables required by Kconfiglib to properly
    resolve paths in the NuttX build system. These variables are set
    before Kconfig operations and restored afterward to avoid interfering
    with other build system operations.

    Attributes:
        bindir: Path to the NuttX binary directory.
        appsbindir: Path to the NuttX apps binary directory.
        appsdir: Path to the NuttX apps directory.
        externaldir: Path to the external directory.
    """

    bindir: Path
    appsbindir: Path
    appsdir: Path
    externaldir: Path

    def set_environment(self):
        """Set environment variables for Kconfig operations."""
        os.environ["BINDIR"] = str(self.bindir)
        os.environ["APPSBINDIR"] = str(self.appsbindir)
        os.environ["APPSDIR"] = str(self.appsdir)
        os.environ["EXTERNALDIR"] = str(self.externaldir)

    def restore_environment(self):
        """Restore environment by removing Kconfig-related variables."""
        os.unsetenv("BINDIR")
        os.unsetenv("APPSBINDIR")
        os.unsetenv("APPSDIR")
        os.unsetenv("EXTERNALDIR")


def kconfig_chdir(f):
    """Decorator to manage environment variables for Kconfig operations.

    This decorator ensures that environment variables are properly set before
    Kconfig operations and restored afterward. This is necessary because:
    - NuttX build system uses environment variables to determine the source
      tree and apps directory
    - We should not interfere with other modules using the build system
    - Leaving these variables set causes path-related issues

    The decorator sets the environment, executes the wrapped method, and
    restores the environment regardless of success or failure.
    """

    @wraps(f)
    def wrap(self, *args, **kwargs):
        self.environment_context.set_environment()
        ret = f(self, *args, **kwargs)
        self.environment_context.restore_environment()
        return ret

    return wrap


class KconfigParser(kconfiglib.Kconfig):
    """Parser for NuttX Kconfig files.

    Extends kconfiglib.Kconfig to provide NuttX-specific initialization
    and environment management. Handles setting up environment variables,
    loading existing configuration files, and managing the working directory.
    """

    KCONFIG_FILE = "Kconfig"
    KCONFIG_CONFIG = ".config"

    def __init__(
        self,
        nuttxspace_path: Path,
        apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
        nuttx_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
        warn: bool = False,
    ):
        """Initialize the Kconfig parser.

        Args:
            nuttx_path: Path to the NuttX source directory.
            apps_path: Path to the NuttX apps directory.
            warn: Whether to show warnings. Defaults to False.

        Raises:
            FileNotFoundError: If the apps_path does not exist.
            RuntimeError: If the .config file is not found (NuttX must be
                initialized first).
        """
        self.nuttx_path = Path(nuttxspace_path) / nuttx_dir
        self.apps_path = Path(nuttxspace_path) / apps_dir
        self.original_dir = os.getcwd()
        self.external_path = self.nuttx_path / "external"
        self.use_custom_ext_path = False

        logger.debug(
            "Initializing Kconfig parser with Kconfig at "
            f"{self.nuttx_path / self.KCONFIG_FILE}"
        )
        if not self.external_path.exists():
            self.external_path = self.nuttx_path / "dummy"

        self.environment_context = KconfigEnvironmentContext(
            bindir=self.nuttx_path,
            appsbindir=self.apps_path,
            appsdir=self.apps_path,
            externaldir=self.external_path,
        )
        self.environment_context.set_environment()

        os.chdir(self.nuttx_path)
        try:
            super().__init__(self.KCONFIG_FILE, warn=warn, suppress_traceback=False)
        except Exception as e:
            logger.error(f"Error initializing Kconfig parser: {e}")
            self.environment_context.restore_environment()
            raise e

        config_file = self.nuttx_path / self.KCONFIG_CONFIG
        if config_file.exists():
            logger.debug(f"Loading existing .config from {config_file}")
            super().load_config(str(config_file))
        else:
            self.environment_context.restore_environment()
            raise RuntimeError(
                f".config file not found at {config_file}. "
                "NuttX must be initialized first."
            )

        self.environment_context.restore_environment()

    @kconfig_chdir
    def kconfig_read(self, config: str) -> str:
        """Read the current state of a Kconfig option.

        Args:
            config: The name of the Kconfig option to read. The "CONFIG_"
                prefix is optional and will be removed if present.

        Returns:
            str: The current value of the Kconfig option. Returns "y", "n", "m"
                for bool/tristate options, or the string/int/hex value for other
                types. Returns empty string if not set.

        Raises:
            KeyError: If the config option does not exist.
        """
        try:
            if config not in self.syms:
                raise KeyError(f"Kconfig option '{config}' not found")

            symbol = self.syms[config]
            value = symbol.str_value

            logger.debug(
                f"Read symbol '{config}': returns {value} "
                f"of type: {kconfiglib.TYPE_TO_STR[symbol.type]} "
                f"assignable: {symbol.assignable}"
            )

            logger.info(f"Kconfig read: {config}={value}")
            print(f"{config}={value}")
            return value
        except Exception as e:
            self.environment_context.restore_environment()
            raise e

    @kconfig_chdir
    def kconfig_enable(self, config: str) -> int:
        """Enable a Kconfig option.

        Args:
            config: The name of the Kconfig option to enable. The "CONFIG_"
                prefix is optional and will be removed if present.

        Returns:
            int: Returns 0 on success, non-zero on failure.

        Raises:
            KeyError: If the config option does not exist.
            ValueError: If the config option cannot be enabled (e.g., not
                assignable or wrong symbol type).
        """
        try:
            if config not in self.syms:
                raise KeyError(f"Kconfig option '{config}' not found")

            symbol = self.syms[config]
            symbol_type = kconfiglib.TYPE_TO_STR[symbol.type]

            if not symbol.assignable:
                raise ValueError(
                    f"Kconfig option '{config}' can't be enabled: "
                    f"symbol type is {symbol_type}"
                )

            ret = symbol.set_value("y")
            if ret:
                logger.info(f"Kconfig option '{config}' enabled")
            else:
                logger.error(f"Kconfig option '{config}' enable failed")
            self.write_config()
            return ret
        except Exception as e:
            self.environment_context.restore_environment()
            raise e

    @kconfig_chdir
    def kconfig_disable(self, config: str) -> int:
        """Disable a Kconfig option.

        Args:
            config: The name of the Kconfig option to disable. The "CONFIG_"
                prefix is optional and will be removed if present.

        Returns:
            int: Returns 0 on success, non-zero on failure.

        Raises:
            KeyError: If the config option does not exist.
            ValueError: If the config option cannot be disabled (e.g., not
                assignable or wrong symbol type).
        """
        try:
            if config not in self.syms:
                raise KeyError(f"Kconfig option '{config}' not found")

            symbol = self.syms[config]
            symbol_type = kconfiglib.TYPE_TO_STR[symbol.type]

            if not symbol.assignable:
                raise ValueError(
                    f"Kconfig option '{config}' can't be disabled: "
                    f"symbol type is {symbol_type}"
                )

            ret = symbol.set_value("n")
            if ret:
                logger.info(f"Kconfig option '{config}' disabled")
            else:
                logger.error(f"Kconfig option '{config}' disable failed")
            self.write_config()
            return ret
        except Exception as e:
            self.environment_context.restore_environment()
            raise e

    @kconfig_chdir
    def kconfig_apply_changes(self) -> int:
        """Apply Kconfig changes by writing the configuration.

        This method writes the current Kconfig state to .config file.
        kconfiglib automatically handles dependency resolution.

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        try:
            ret = self.write_config()
            logger.info(f"Kconfig apply changes: {ret}")
            return ret
        except Exception as e:
            self.environment_context.restore_environment()
            raise e

    @kconfig_chdir
    def kconfig_set_value(self, config: str, value: str) -> int:
        """Set a numerical Kconfig option value.

        Sets the value for INT or HEX type Kconfig options. For HEX options,
        the value must be prefixed with "0x". For INT options, hexadecimal
        values are not allowed.

        Args:
            config: The name of the Kconfig option. The "CONFIG_" prefix is
                optional and will be removed if present.
            value: The numerical value to set as a string. Must be convertible
                to int. For HEX options, must start with "0x".

        Returns:
            int: Returns 0 on success, non-zero on failure.

        Raises:
            AssertionError: If value is not a string.
            ValueError: If the value cannot be converted to an integer, if
                the config option is not INT or HEX type, if the symbol is
                assignable (should use enable/disable instead), if INT type
                receives hexadecimal value, or if HEX type doesn't have "0x"
                prefix.
            KeyError: If the config option does not exist.
        """
        try:
            if config not in self.syms:
                raise KeyError(f"Kconfig option '{config}' not found")

            symbol = self.syms[config]
            symbol_type = kconfiglib.TYPE_TO_STR[symbol.type]

            if symbol.type not in (kconfiglib.INT, kconfiglib.HEX):
                raise ValueError(
                    f"{config} ({symbol_type}) requires a numerical or "
                    "hexadecimal input"
                )

            if symbol.assignable:
                raise ValueError(
                    f"Kconfig value for '{config}' can't be set: "
                    f"symbol type is {symbol_type}"
                )

            if symbol.type == kconfiglib.INT and value.startswith("0x"):
                raise ValueError(
                    f"{config} ({symbol_type}) requires a int input, not hexadecimal"
                )

            if symbol.type == kconfiglib.HEX and not value.startswith("0x"):
                raise ValueError(
                    f"{config} ({symbol_type}) requires a hexadecimal input (0x<hex>), "
                    "not int."
                )

            ret = symbol.set_value(value)
            if not ret:
                logger.error(f"Kconfig set value: {config}={value} failed")
            logger.info(f"Kconfig set value: {config}={value}")
            self.write_config()
            return ret

        except Exception as e:
            self.environment_context.restore_environment()
            raise e

    @kconfig_chdir
    def kconfig_set_str(self, config: str, value: str) -> int:
        """Set a string Kconfig option value.

        Args:
            config: The name of the Kconfig option. The "CONFIG_" prefix is
                optional and will be removed if present.
            value: The string value to set.

        Returns:
            int: Returns 0 on success, non-zero on failure.

        Raises:
            KeyError: If the config option does not exist.
            ValueError: If the config option is not a STRING type.
        """
        try:
            if config not in self.syms:
                raise KeyError(f"Kconfig option '{config}' not found")

            symbol = self.syms[config]
            symbol_type = kconfiglib.TYPE_TO_STR[symbol.type]

            if symbol.type != kconfiglib.STRING:
                raise ValueError(f"{config} ({symbol_type}) requires a string input")

            ret = symbol.set_value(value)
            if not ret:
                logger.error(f"Kconfig set string: {config}={value} failed")
            else:
                logger.info(f"Kconfig set string: {config}={value}")
            self.write_config()
            return ret
        except Exception as e:
            self.environment_context.restore_environment()
            raise e

    def kconfig_merge_config_file(self, source_file: str) -> int:
        """Merge a Kconfig file into the current configuration.

        Merges configuration options from a source file into the current
        Kconfig state using kconfiglib's load_config method. The merged
        configuration is not automatically written to disk; call
        kconfig_apply_changes() to persist changes.

        Args:
            source_file: Path to the source configuration file to merge.

        Returns:
            int: Always returns 0. The actual merge result is available
                from load_config but is not currently exposed.

        Raises:
            ValueError: If source_file is not provided or is empty.
        """
        try:
            if not source_file:
                raise ValueError("Source file is required")

            logger.info(f"Kconfig merge config file: {source_file}")
            source_file = Path(source_file).resolve().as_posix()
            result = self.load_config(str(source_file), replace=False)
            self.write_config()
            logger.info(f"Kconfig merge config file result: {result}")
        except Exception as e:
            self.environment_context.restore_environment()
            raise e
        return 0


class KconfigTweak:
    """Manages Kconfig tweak operations.

    This class provides methods to read, modify, and manage Kconfig
    options for NuttX builds using the kconfig-tweak tool.
    """

    def __init__(self, nuttx_path: Path):
        """Initialize the KconfigTweak class.

        Args:
            nuttx_path: Path to the NuttX repository.
                If using CMake, should be the build directory.
        """
        self.nuttx_path = nuttx_path
        self.config_file = Path(self.nuttx_path) / ".config"

        if not self.config_file.exists():
            raise RuntimeError(f".config file not found at {self.config_file}")

        self.content = self.config_file.read_text().splitlines()

    def kconfig_read(self, config: str) -> str:
        """Read the current state of a Kconfig option.

        Args:
            config: The name of the Kconfig option to read. The "CONFIG_"
                prefix is optional.

        Returns:
            str: The current value of the Kconfig option. Returns "y", "n", "m"
                for bool/tristate options, or the string/int/hex value for other
                types. Returns empty string if not set.

        Raises:
            KeyError: If the config option does not exist.
        """
        self._check_config_exists(config)
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.STATE, config], cwd=self.nuttx_path
        )
        value = result.stdout.strip()
        logger.info(f"Kconfig read: {config}={value}")
        print(f"{config}={value}")
        return value

    def kconfig_enable(self, config: str) -> int:
        """Enable a Kconfig option.

        Args:
            config: The name of the Kconfig option to enable. The "CONFIG_"
                prefix is optional.

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        self._check_config_exists(config)
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.ENABLE, config], cwd=self.nuttx_path
        )
        return result.returncode

    def kconfig_disable(self, config: str) -> int:
        """Disable a Kconfig option.

        Args:
            config: The name of the Kconfig option to disable. The "CONFIG_"
                prefix is optional.

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        self._check_config_exists(config)
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.DISABLE, config], cwd=self.nuttx_path
        )
        return result.returncode

    def kconfig_apply_changes(self) -> int:
        """Apply Kconfig changes by writing the configuration.

        This method runs 'make olddefconfig' to apply any pending
        Kconfig changes and update the configuration.

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        result = utils.run_make_command(["make", "olddefconfig"], cwd=self.nuttx_path)
        if result.returncode != 0:
            logger.error("Kconfig change apply may have failed")
        else:
            logger.info("Kconfig changes applied")
        return result.returncode

    def kconfig_set_value(self, config: str, value: str) -> int:
        """Set a numerical Kconfig option value.

        Sets the value for INT or HEX type Kconfig options. For HEX options,
        the value must be prefixed with "0x". For INT options, hexadecimal
        values are not allowed.

        Args:
            config: The name of the Kconfig option. The "CONFIG_" prefix is
                optional and will be removed if present.
            value: The numerical value to set as a string. Must be convertible
                to int. For HEX options, must start with "0x".

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        self._check_config_exists(config)
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.SET_VAL, config, str(value)],
            cwd=self.nuttx_path,
        )
        logger.info(f"Kconfig set value: {config}={value}")
        return result.returncode

    def kconfig_set_str(self, config: str, value: str) -> int:
        """Set a string Kconfig option value.

        Args:
            config: The name of the Kconfig option. The "CONFIG_" prefix is
                optional.
            value: The string value to set.

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        self._check_config_exists(config)
        result = utils.run_kconfig_command(
            [KCONFIG_TWEAK, KconfigTweakAction.SET_STR, config, value],
            cwd=self.nuttx_path,
        )
        logger.info(f"Kconfig set string: {config}={value}")
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
            int: Returns 0 on success, non-zero on failure.

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

    def _check_config_exists(self, config: str) -> bool:
        for line in self.content:
            if config in line.strip():
                logger.debug(f"match: {config}")
                return
        raise KeyError(f"Kconfig option '{config}' not found")


class ConfigManager:
    """Manages NuttX build configurations.

    This class provides methods to read, modify, and manage Kconfig
    options for NuttX builds.
    """

    def __init__(
        self,
        nuttxspace_path: Path,
        apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
        nuttx_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
        build_tool: BuildTool = BuildTool.MAKE,
        build_dir: str = "build",
        warnings: bool = False,
    ):
        """Initialize the ConfigManager.

        Args:
            nuttxspace_path: Path to the NuttX repository workspace.
            apps_dir: Name of the NuttX apps directory within the workspace.
            warnings: Whether to show warnings. Defaults to False.

        Raises:
            FileNotFoundError: If the apps directory does not exist.
            RuntimeError: If the .config file is not found (NuttX must be
                initialized first).
        """
        self.nuttxspace_path = Path(nuttxspace_path)
        self.nuttx_path = self.nuttxspace_path / nuttx_dir
        self.apps_path = self.nuttxspace_path / apps_dir
        self.build_tool = build_tool
        self.build_dir = build_dir
        self.build_path = self.nuttx_path
        if build_tool == BuildTool.CMAKE:
            self.build_path = self.nuttx_path / self.build_dir

        if not self.apps_path.exists():
            raise FileNotFoundError(f"Apps path not found at {self.apps_path}")

        if not self.build_path.exists():
            raise RuntimeError(f"Build path not found at {self.build_path}")

        if not (self.build_path / ".config").exists():
            raise RuntimeError(f".config file not found at {self.build_path}")

        if self.build_tool == BuildTool.MAKE:
            self._manager = KconfigParser(self.nuttxspace_path, apps_dir, nuttx_dir)
            logger.debug("Using kconfiglib for config management (Make build)")
        elif self.build_tool == BuildTool.CMAKE:
            self._manager = KconfigTweak(self.build_path)
            logger.debug("Using kconfig-tweak for config management (CMake build)")
        else:
            raise ValueError(f"Invalid build tool: {build_tool}")

    def kconfig_read(self, config: str) -> str:
        config = config.removeprefix("CONFIG_")
        return self._manager.kconfig_read(config)

    def kconfig_enable(self, config: str) -> int:
        config = config.removeprefix("CONFIG_")
        return self._manager.kconfig_enable(config)

    def kconfig_disable(self, config: str) -> int:
        config = config.removeprefix("CONFIG_")
        return self._manager.kconfig_disable(config)

    def kconfig_apply_changes(self) -> int:
        return self._manager.kconfig_apply_changes()

    def kconfig_set_value(self, config: str, value: str) -> int:
        assert isinstance(value, str), (
            "Set value must be string representation of a numerical or "
            "hexadecimal value."
        )
        try:
            int(value, 0)
        except ValueError:
            raise ValueError(
                "Set value must be string representation of a numerical or "
                "hexadecimal value"
            )

        config = config.removeprefix("CONFIG_")
        return self._manager.kconfig_set_value(config, value)

    def kconfig_set_str(self, config: str, value: str) -> int:
        config = config.removeprefix("CONFIG_")
        return self._manager.kconfig_set_str(config, value)

    def kconfig_menuconfig(self) -> int:
        logger.debug("Opening menuconfig")
        if self.build_tool == BuildTool.MAKE:
            utils.run_curses_command(["make", "menuconfig"], cwd=self.nuttx_path)
        else:
            utils.run_curses_command(
                ["cmake", "--build", self.build_dir, "-t", "menuconfig"],
                cwd=self.build_dir,
            )

    def kconfig_merge_config_file(self, source_file: str) -> int:
        return self._manager.kconfig_merge_config_file(source_file)
