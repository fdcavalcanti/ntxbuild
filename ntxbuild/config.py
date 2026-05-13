"""
Configuration management for NuttX builds.

This module provides classes and utilities for managing Kconfig-based
configuration for NuttX builds, including reading, modifying, and merging
configuration options.
"""

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from pathlib import Path

import kconfiglib
import menuconfig

from . import utils
from .build import BuildTool

logger = logging.getLogger("ntxbuild.config")


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
        kconfig_config: Path to the Kconfig configuration file (e.g., .config).
    """

    bindir: Path
    appsbindir: Path
    appsdir: Path
    externaldir: Path
    kconfig_config: Path = Path(".config")

    def _kconfig_env_vars(self) -> dict[str, str]:
        return {
            "BINDIR": str(self.bindir),
            "APPSBINDIR": str(self.appsbindir),
            "APPSDIR": str(self.appsdir),
            "EXTERNALDIR": str(self.externaldir),
            "KCONFIG_CONFIG": str(self.kconfig_config),
        }

    @contextmanager
    def scoped_environment(self):
        """Temporarily set Kconfig environment variables and restore them."""
        env_vars = self._kconfig_env_vars()
        previous = {key: os.environ.get(key) for key in env_vars}

        os.environ.update(env_vars)
        try:
            yield
        finally:
            for key, previous_value in previous.items():
                if previous_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = previous_value


@contextmanager
def scoped_working_directory(path: Path):
    """Temporarily switch process working directory and restore it."""
    previous_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous_cwd)


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
        with scoped_working_directory(self.nuttx_path):
            with self.environment_context.scoped_environment():
                return f(self, *args, **kwargs)

    return wrap


class KconfigParser(kconfiglib.Kconfig):
    """Parser for NuttX Kconfig files.

    Extends :class:`kconfiglib.Kconfig` to provide NuttX-specific
    initialization and environment management. Handles setting up
    environment variables, loading an existing ``.config`` and managing the
    working directory while performing kconfig operations.

    Args:
        nuttxspace_path: Path to the NuttX workspace containing the
            NuttX source and apps directories.
        build_dir: Name of the build directory (default: "build").
        apps_dir: Name of the apps directory within the workspace.
        nuttx_dir: Name of the NuttX source directory within the workspace.
        build_tool: :class:`BuildTool` value indicating Make or CMake usage.
        warn: Whether to enable kconfiglib warnings (default: False).
    """

    def __init__(
        self,
        kconfig_file: Path,
        config_file: Path,
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
        self.kconfig_file = kconfig_file
        self.config_file = config_file

        logger.debug(f"Init Kconfig parser: {self.kconfig_file}")
        super().__init__(self.kconfig_file, warn=warn, suppress_traceback=False)

        logger.debug(f"Load .config: {self.config_file}")
        super().load_config(str(self.config_file))

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

    def kconfig_apply_changes(self) -> int:
        """Apply Kconfig changes by writing the configuration.

        This method writes the current Kconfig state to .config file.
        kconfiglib automatically handles dependency resolution.

        Returns:
            int: Returns 0 on success, non-zero on failure.
        """
        ret = self.write_config()
        logger.info(f"Kconfig apply changes: {ret}")
        return 0

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
        if config not in self.syms:
            raise KeyError(f"Kconfig option '{config}' not found")

        symbol = self.syms[config]
        symbol_type = kconfiglib.TYPE_TO_STR[symbol.type]

        if symbol.type not in (kconfiglib.INT, kconfiglib.HEX):
            raise ValueError(
                f"{config} ({symbol_type}) requires a numerical or " "hexadecimal input"
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
        if not source_file:
            raise ValueError("Source file is required")

        logger.info(f"Kconfig merge config file: {source_file}")
        source_file = Path(source_file).resolve().as_posix()
        result = self.load_config(str(source_file), replace=False)
        self.write_config()
        logger.info(f"Kconfig merge config file result: {result}")
        return 0


class ConfigManager:
    """Manages NuttX build configurations.

    This class provides methods to read, modify, and manage Kconfig
    options for NuttX builds.
    """

    KCONFIG_FILE = "Kconfig"
    CONFIG_FILE = ".config"

    def __init__(
        self,
        nuttxspace_path: Path,
        apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
        nuttx_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
        build_tool: BuildTool = BuildTool.MAKE,
        build_dir: str = "build",
    ):
        """Initialize the ConfigManager.

        Args:
            nuttxspace_path: Path to the NuttX repository workspace.
            apps_dir: Name of the NuttX apps directory within the workspace.
            nuttx_dir: Name of the NuttX kernel directory within the workspace.
            build_dir: Name of the build directory (CMake only).

        Raises:
            FileNotFoundError: If the nuttxspace or apps directory does not exist.
            RuntimeError: If the .config file is not found (NuttX must be
                initialized first).
        """
        self.nuttxspace_path = Path(nuttxspace_path)
        self.nuttx_path = self.nuttxspace_path / nuttx_dir
        self.build_tool = build_tool
        self.build_dir = build_dir
        apps_path = self.nuttxspace_path / apps_dir

        build_path = self.nuttx_path
        if build_tool == BuildTool.CMAKE:
            build_path = self.nuttx_path / self.build_dir

        if (
            self.build_tool == BuildTool.MAKE
            and (self.nuttx_path / "external" / "Kconfig").is_file()
        ):
            external_path = Path("external")
        else:
            external_path = Path("dummy")

        if not self.nuttxspace_path.exists():
            raise FileNotFoundError(f"Nuttxspace not found at {self.nuttxspace_path}")

        if not apps_path.exists():
            raise FileNotFoundError(f"Apps path not found at {apps_path}")

        if not build_path.exists():
            raise RuntimeError(f"Build path not found at {build_path}")

        if not (build_path / ".config").exists():
            raise RuntimeError(f".config file not found at {build_path}")

        if self.build_tool == BuildTool.CMAKE:
            self.environment_context = KconfigEnvironmentContext(
                bindir=build_path,
                appsbindir=build_path / apps_dir,
                appsdir=apps_path,
                externaldir=external_path,
                kconfig_config=build_path / self.CONFIG_FILE,
            )
        else:
            self.environment_context = KconfigEnvironmentContext(
                bindir=build_path,
                appsbindir=apps_path,
                appsdir=apps_path,
                externaldir=external_path,
            )

        with scoped_working_directory(self.nuttx_path):
            with self.environment_context.scoped_environment():
                self._manager = KconfigParser(
                    kconfig_file=self.nuttx_path / self.KCONFIG_FILE,
                    config_file=build_path / self.CONFIG_FILE,
                )

    @kconfig_chdir
    def kconfig_read(self, config: str) -> str:
        return self._manager.kconfig_read(self._normalize_config_name(config))

    @kconfig_chdir
    def kconfig_enable(self, config: str) -> int:
        return self._manager.kconfig_enable(self._normalize_config_name(config))

    @kconfig_chdir
    def kconfig_disable(self, config: str) -> int:
        return self._manager.kconfig_disable(self._normalize_config_name(config))

    @kconfig_chdir
    def kconfig_apply_changes(self) -> int:
        return self._manager.kconfig_apply_changes()

    @kconfig_chdir
    def kconfig_set_value(self, config: str, value: str) -> int:
        assert isinstance(value, str), (
            "Set value must be string representation of a numerical or "
            "hexadecimal value."
        )
        try:
            int(value, 0)
        except ValueError as exc:
            raise ValueError(
                "Set value must be string representation of a numerical or "
                "hexadecimal value"
            ) from exc

        return self._manager.kconfig_set_value(
            self._normalize_config_name(config), value
        )

    @kconfig_chdir
    def kconfig_set_str(self, config: str, value: str) -> int:
        return self._manager.kconfig_set_str(self._normalize_config_name(config), value)

    @kconfig_chdir
    def kconfig_menuconfig(self) -> int:
        logger.debug("Opening menuconfig")
        menuconfig.menuconfig(self._manager)
        return 0

    @kconfig_chdir
    def kconfig_merge_config_file(self, source_file: str) -> int:
        return self._manager.kconfig_merge_config_file(source_file)

    @staticmethod
    def _normalize_config_name(config: str) -> str:
        return config.removeprefix("CONFIG_")
