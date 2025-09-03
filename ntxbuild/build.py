"""
Build system module for NuttX.
"""

import logging
import os
from pathlib import Path
from enum import Enum

from . import utils

# Get logger for this module
logger = logging.getLogger(__name__)


class BuilderAction(str, Enum):
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    BUILD = "build"
    CLEAN = "clean"
    DISTCLEAN = "distclean"
    CONFIGURE = "configure"
    INFO = "info"
    MAKE = "make"


class MakeAction(str, Enum):
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    ALL = "all"
    APPS_CLEAN = "apps_clean"
    BOOTLOADER = "bootloader"
    CLEAN = "clean"
    CLEAN_BOOTLOADER = "clean_bootloader"
    CRYPTO = "crypto/"
    DISTCLEAN = "distclean"
    FLASH = "flash"
    HOST_INFO = "host_info"
    MENUCONFIG = "menuconfig"
    OLDCONFIG = "oldconfig"
    OLDDEFCONFIG = "olddefconfig"
    SCHED_CLEAN = "sched_clean"


class NuttXBuilder:
    """Main builder class for NuttX projects."""

    def __init__(self, nuttxspace_path: Path = None):
        self.nuttxspace_path = nuttxspace_path
        self.nuttx_path = nuttxspace_path / "nuttx"
        self.apps_path = nuttxspace_path / "nuttx-apps"
        self.rel_apps_path = None

    def build(self, parallel: int = None):
        """Build the NuttX project."""
        logger.info(f"Starting build with parallel={parallel}")
        if parallel:
            args = [f"-j{parallel}"]
        else:
            args = []

        return utils.run_make_command([BuilderAction.MAKE] + args, cwd=self.nuttx_path)

    def distclean(self):
        """Distclean the NuttX project."""
        logger.info("Running distclean")
        utils.run_make_command(
            [BuilderAction.MAKE, MakeAction.DISTCLEAN], cwd=self.nuttx_path
        )

    def clean(self):
        """Clean build artifacts."""
        logger.info("Running clean")
        utils.run_make_command(
            [BuilderAction.MAKE, MakeAction.CLEAN], cwd=self.nuttx_path
        )

    def validate_nuttx_environment(self) -> tuple[bool, str]:
        """Validate NuttX environment and return (is_valid, error_message)."""
        logger.info(
            f"Validating NuttX environment: nuttx_dir={self.nuttx_path},"
            f" apps_dir={self.apps_path}"
        )

        # Check for NuttX environment files
        makefile_path = self.nuttx_path / "Makefile"
        inviolables_path = self.nuttx_path / "INVIOLABLES.md"

        if not makefile_path.exists():
            logger.error(f"Makefile not found at: {makefile_path}")
            return False, f"Invalid NuttX directory: {self.nuttx_path}"

        if not inviolables_path.exists():
            logger.error(f"INVIOLABLES.md not found at: {inviolables_path}")
            return False, f"Invalid NuttX directory: {self.nuttx_path}"

        # Validate apps directory
        if self.nuttx_path.parent == self.apps_path.parent:
            app_dir_name = self.apps_path.stem
            self.rel_apps_path = f"../{app_dir_name}"
        else:
            self.rel_apps_path = self.apps_path

        if not self.apps_path.exists():
            logger.error(f"Apps directory not found: {self.apps_path}")
            return False, f"Apps directory not found: {self.apps_path}"

        if not self.apps_path.is_dir():
            logger.error(f"Apps path is not a directory: {self.apps_path}")
            return False, f"Apps path is not a directory: {self.apps_path}"

        # Validate apps directory structure
        if not (self.apps_path / "Make.defs").exists():
            logger.error(f"Make.defs not found in apps directory: {self.apps_path}")
            return (
                False,
                f"Apps directory may not be properly configured (Make.defs missing):"
                f" {self.apps_path}",
            )

        logger.info("NuttX environment validation successful")
        return True, ""

    def setup_nuttx(self, board: str, defconfig: str) -> int:
        """Run NuttX setup commands in the NuttX directory."""
        logger.info(f"Setting up NuttX: board={board}, defconfig={defconfig}")
        try:
            # Validate environment first
            is_valid, error_msg = self.validate_nuttx_environment()
            if not is_valid:
                logger.error(f"Validation failed: {error_msg}")
                return 1

            # Change to NuttX directory
            logger.debug(f"Changing to NuttX directory: {self.nuttx_path}")
            os.chdir(self.nuttx_path)

            # Run configure script
            logger.info(
                f"Running configure.sh with args: -a {self.rel_apps_path}"
                f" {board}:{defconfig}"
            )
            config_result = utils.run_bash_script(
                "./tools/configure.sh",
                args=[f"-a {self.rel_apps_path}", f"{board}:{defconfig}"],
                cwd=self.nuttx_path,
            )
            if config_result != 0:
                logger.error(f"Configure script failed with exit code: {config_result}")
                return config_result

            logger.info("NuttX setup completed successfully")
            return 0

        except Exception as e:
            logger.error(f"Setup failed with error: {e}", exc_info=True)
            return 1
