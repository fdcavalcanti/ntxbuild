"""
Build system module for NuttX.
"""

import logging
import os
import subprocess
from enum import Enum
from pathlib import Path

from . import utils

# Get logger for this module
logger = logging.getLogger("ntxbuild.build")


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
    MENUCONFIG = "menuconfig"


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

    def __init__(
        self,
        nuttxspace_path: Path = None,
        os_dir: str = "nuttx",
        apps_dir: str = "nuttx-apps",
    ):
        self.nuttxspace_path = nuttxspace_path
        self.nuttx_path = nuttxspace_path / os_dir
        self.apps_path = nuttxspace_path / apps_dir
        self.rel_apps_path = None
        self.no_stdout = False
        self.no_stderr = False

    def make(self, command: str):
        """Run make command."""
        logger.info(f"Running make command: {command}")
        cmd_list = [BuilderAction.MAKE] + command.split()
        return utils.run_make_command(
            cmd_list,
            cwd=self.nuttx_path.absolute(),
            no_stdout=self.no_stdout,
            no_stderr=self.no_stderr,
        )

    def build(self, parallel: int = None):
        """Build the NuttX project."""
        logger.info(f"Starting build with parallel={parallel}")
        if parallel:
            args = [f"-j{parallel}"]
        else:
            args = []

        return utils.run_make_command(
            [BuilderAction.MAKE] + args,
            cwd=self.nuttx_path.absolute(),
            no_stdout=self.no_stdout,
            no_stderr=self.no_stderr,
        )

    def distclean(self):
        """Distclean the NuttX project."""
        logger.info("Running distclean")
        utils.run_make_command(
            [BuilderAction.MAKE, MakeAction.DISTCLEAN],
            cwd=self.nuttx_path.absolute(),
            no_stdout=self.no_stdout,
            no_stderr=self.no_stderr,
        )

    def clean(self):
        """Clean build artifacts."""
        logger.info("Running clean")
        utils.run_make_command(
            [BuilderAction.MAKE, MakeAction.CLEAN],
            cwd=self.nuttx_path.absolute(),
            no_stdout=self.no_stdout,
            no_stderr=self.no_stderr,
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

    def setup_nuttx(
        self, board: str, defconfig: str, extra_args: list[str] = []
    ) -> int:
        """Run NuttX setup commands in the NuttX directory."""
        logger.info(f"Setting up NuttX: board={board}, defconfig={defconfig}")
        old_dir = Path.cwd()
        try:
            # Validate environment first
            is_valid, error_msg = self.validate_nuttx_environment()
            if not is_valid:
                logger.error(f"Validation failed: {error_msg}")
                return 1

            # Change to NuttX directory
            logger.debug(f"Changing to NuttX directory: {self.nuttx_path}")
            os.chdir(self.nuttx_path)

            config_args = [
                *extra_args,
                f"-a {self.rel_apps_path}",
                f"{board}:{defconfig}",
            ]

            # Run configure script
            logger.info(f"Running configure.sh with args: {config_args}")

            config_result = utils.run_bash_script(
                "./tools/configure.sh",
                args=config_args,
                cwd=self.nuttx_path,
                no_stdout=self.no_stdout,
                no_stderr=self.no_stderr,
            )

            # Return to old directory after running configure.sh
            os.chdir(old_dir)

            if config_result != 0:
                logger.error(f"Configure script failed with exit code: {config_result}")
                return config_result

            logger.info("NuttX setup completed successfully")
            return 0

        except Exception as e:
            logger.error(f"Setup failed with error: {e}", exc_info=True)
            return 1

    def run_menuconfig(self):
        """Run menuconfig"""
        logger.info("Running menuconfig")
        utils.run_curses_command(
            [BuilderAction.MAKE, MakeAction.MENUCONFIG], cwd=self.nuttx_path
        )

    def print_binary_info(self, binary_path: str = "nuttx.bin"):
        """Print binary information including file size and architecture.

        Args:
            binary_path: Path to the binary file relative to nuttx directory
        """
        logger.info(f"Printing binary information for: {binary_path}")

        # Construct full path to binary
        full_binary_path = self.nuttx_path / binary_path

        if not full_binary_path.exists():
            logger.error(f"Binary file not found: {full_binary_path}")
            print(f"Error: Binary file not found: {full_binary_path}")
            return

        try:
            # Get file size
            file_size = full_binary_path.stat().st_size
            print(f"Binary: {binary_path}")
            print(f"File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

            # Try to get architecture information using file command
            try:
                # Use subprocess.run similar to utils.py pattern
                result = subprocess.run(
                    ["file", str(full_binary_path)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                file_info = result.stdout.strip()

                # Parse and format file information nicely
                self._print_formatted_file_info(file_info)

            except subprocess.CalledProcessError as e:
                logger.error(f"File command failed: {e}")
                print("File info: Unable to determine (file command failed)")
            except FileNotFoundError:
                logger.error("File command not available")
                print("File info: Unable to determine (file command not available)")

        except Exception as e:
            logger.error(f"Error getting binary information: {e}")
            print(f"Error: {e}")

    def _print_formatted_file_info(self, file_info: str):
        """Parse and format file command output into readable lines.

        Args:
            file_info: Raw output from file command
        """
        # Remove the filename prefix (everything before the first colon)
        if ":" in file_info:
            info_part = file_info.split(":", 1)[1].strip()
        else:
            info_part = file_info

        # Split by commas and clean up
        parts = [part.strip() for part in info_part.split(",")]

        print("File type:")
        for part in parts:
            if part:
                print(f"  • {part}")

    def supress_stdout(self, enable: bool) -> None:
        """Suppress stdout."""
        self.no_stdout = enable

    def supress_stderr(self, enable: bool) -> None:
        """Suppress stderr."""
        self.no_stderr = enable
