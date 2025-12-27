"""
Build system module for NuttX.
"""
import abc
import logging
import subprocess
from enum import Enum
from pathlib import Path

from . import utils

# Get logger for this module
logger = logging.getLogger("ntxbuild.build")


class BuildTool(str, Enum):
    """Enumeration of build tools.

    This enum defines the available build tools that can be used
    with NuttX build system.
    """

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    MAKE = "make"
    CMAKE = "cmake"


class MakeAction(str, Enum):
    """Enumeration of make targets.

    This enum defines the available make targets that can be used
    with NuttX.
    """

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


class CMakeAction(str, Enum):
    """Enumeration of CMake actions."""

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    BUILD_PATH = "-B"
    BUILD = "--build"
    TARGET = "--target"
    CLEAN = "clean"
    MENUCONFIG = "menuconfig"


class BaseBuilder(abc.ABC):
    def __init__(
        self,
        nuttxspace_path: Path = None,
        os_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
        apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
    ):
        """Initialize the NuttX builder class.

        Args:
            nuttxspace_path: Path to the NuttX repository workspace.
                If None, must be set later. Defaults to None.
            os_dir: Name of the NuttX OS directory within the workspace.
                Defaults to "nuttx".
            apps_dir: Name of the NuttX apps directory within the workspace.
                Defaults to "nuttx-apps".
        """
        self.nuttxspace_path = nuttxspace_path
        self.nuttx_path = nuttxspace_path / os_dir
        self.apps_path = nuttxspace_path / apps_dir
        self.no_stdout = False
        self.no_stderr = False
        self.rel_apps_path = None

        self._validate_nuttx_environment()
        logging.debug(
            f"NuttXBuilder initialized: nuttxspace_path={self.nuttxspace_path},"
            f" nuttx_path={self.nuttx_path}, apps_path={self.apps_path}"
        )

    @abc.abstractmethod
    def build(self, parallel: int = None) -> subprocess.CompletedProcess:
        ...

    @abc.abstractmethod
    def clean(self) -> subprocess.CompletedProcess:
        ...

    @abc.abstractmethod
    def initialize(self) -> int:
        ...

    @abc.abstractmethod
    def menuconfig(self) -> int:
        ...

    @abc.abstractmethod
    def distclean(self) -> subprocess.CompletedProcess:
        ...

    def supress_stdout(self, enable: bool) -> None:
        """Suppress stdout output from commands.

        Controls whether stdout from subsequent commands should be
        suppressed or displayed.

        Args:
            enable: If True, suppress stdout. If False, show stdout.
        """
        self.no_stdout = enable

    def supress_stderr(self, enable: bool) -> None:
        """Suppress stderr output from commands.

        Controls whether stderr from subsequent commands should be
        suppressed or displayed.

        Args:
            enable: If True, suppress stderr. If False, show stderr.
        """
        self.no_stderr = enable

    def _validate_nuttx_environment(self) -> tuple[bool, str]:
        """Validate NuttX environment.

        Checks for required NuttX files (Makefile, INVIOLABLES.md) and
        validates the apps directory structure.

        Returns:
            tuple[bool, str]: A tuple containing:
                - bool: True if environment is valid, False otherwise.
                - str: Error message if validation failed, empty string if valid.
        """
        logger.debug(
            f"Validating NuttX environment: nuttx_dir={self.nuttx_path},"
            f" apps_dir={self.apps_path}, "
            f"nuttxspace_path={self.nuttxspace_path}"
        )

        # Check for NuttX environment files
        makefile_path = self.nuttx_path / "Makefile"
        inviolables_path = self.nuttx_path / "INVIOLABLES.md"

        if not makefile_path.exists():
            raise FileNotFoundError(f"Makefile not found at: {self.nuttx_path}")

        if not inviolables_path.exists():
            raise FileNotFoundError(f"INVIOLABLES.md not found at: {inviolables_path}")

        # Validate apps directory
        if self.nuttx_path.parent == self.apps_path.parent:
            app_dir_name = self.apps_path.stem
            self.rel_apps_path = f"../{app_dir_name}"
        else:
            self.rel_apps_path = self.apps_path

        if not self.apps_path.exists():
            raise FileNotFoundError(f"Apps directory not found: {self.apps_path}")

        if not self.apps_path.is_dir():
            raise FileNotFoundError(f"Apps path is not a directory: {self.apps_path}")

        # Validate apps directory structure
        if not (self.apps_path / "Make.defs").exists():
            raise FileNotFoundError(
                f"Make.defs not found in apps directory: {self.apps_path}"
            )

        logger.debug("NuttX environment validation successful")


class MakeBuilder(BaseBuilder):
    """Main builder class for NuttX projects.

    This class allows you to trigger make commands, setup NuttX for a
    board:config, build, distclean, clean, menuconfig, etc.
    """

    def __init__(
        self,
        nuttxspace_path: Path,
        os_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
        apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
    ):
        """Initialize the NuttX builder class.

        Args:
            nuttxspace_path: Path to the NuttX repository workspace.
            os_dir: Name of the NuttX OS directory within the workspace.
                Defaults to "nuttx".
            apps_dir: Name of the NuttX apps directory within the workspace.
                Defaults to "nuttx-apps".
        """
        super().__init__(
            nuttxspace_path=nuttxspace_path,
            os_dir=os_dir,
            apps_dir=apps_dir,
        )

    def make(self, command: str) -> subprocess.CompletedProcess:
        """Run any make command inside NuttX directory.

        Args:
            command: The make command to run. It can be any make command,
                such as "all", "clean", "distclean", "menuconfig", etc.
                Multiple arguments can be space-separated.

        Returns:
            subprocess.CompletedProcess: The result of the make command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info(f"Running make command: {command}")
        return self._execute_make(command.split())

    def build(self, parallel: int = None) -> subprocess.CompletedProcess:
        """Build the NuttX project using Make.

        Args:
            parallel: Number of parallel jobs to use for building.
                If None, uses default make parallelism. Defaults to None.

        Returns:
            subprocess.CompletedProcess: The result of the build command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info(f"Starting build with parallel={parallel}")
        if parallel:
            args = [f"-j{parallel}"]
        else:
            args = []

        return self._execute_make(args)

    def distclean(self) -> subprocess.CompletedProcess:
        """Perform a distclean on the NuttX project using Make.

        This removes all generated files including configuration files.

        Returns:
            subprocess.CompletedProcess: The result of the distclean command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info("Running distclean")
        return self._execute_make([MakeAction.DISTCLEAN])

    def clean(self) -> subprocess.CompletedProcess:
        """Clean build artifacts using Make.

        Removes object files and other build artifacts, but preserves
        configuration files.

        Returns:
            subprocess.CompletedProcess: The result of the clean command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info("Running clean")
        return self._execute_make([MakeAction.CLEAN])

    def initialize(self, board: str, defconfig: str, extra_args: list[str] = []) -> int:
        """Run NuttX setup commands in the NuttX directory using Make.

        Configures NuttX for the specified board and defconfig by running
        the configure.sh script. This method validates the environment
        before attempting configuration.

        Args:
            board: The board name (e.g., "stm32f4discovery").
            defconfig: The defconfig name (e.g., "nsh").
            extra_args: Additional arguments to pass to configure.sh.
                Defaults to empty list.

        Returns:
            int: Exit code of the configure script. Returns 0 on success,
                1 on validation failure or exception, or the configure script's
                exit code if it fails.
        """
        logger.info(f"Setting up NuttX: board={board}, defconfig={defconfig}")
        logger.debug(f"Changing to NuttX directory: {self.nuttx_path}")

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
        if config_result != 0:
            logger.error(f"Configure script failed with exit code: {config_result}")
            return config_result

        logger.info("NuttX setup completed successfully")
        return config_result

    def menuconfig(self) -> subprocess.CompletedProcess:
        """Run menuconfig using Make.

        Opens the interactive menu configuration interface for NuttX.
        This is a curses-based interface that allows interactive configuration
        of NuttX build options.

        Returns:
            subprocess.CompletedProcess: The result of the menuconfig command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info("Running menuconfig")
        return utils.run_curses_command(
            [BuildTool.MAKE, MakeAction.MENUCONFIG], cwd=self.nuttx_path
        )

    def _execute_make(self, args: list[str]) -> subprocess.CompletedProcess:
        """Helper method to execute Make commands.

        Args:
            args: List of arguments to pass to the Make command.

        Returns:
            subprocess.CompletedProcess: The result of the Make command.
                Check the returncode attribute to determine success (0) or failure.
        """
        cmd_list = [BuildTool.MAKE] + args
        return utils.run_make_command(
            cmd_list,
            cwd=self.nuttx_path.absolute(),
            no_stdout=self.no_stdout,
            no_stderr=self.no_stderr,
        )


class CMakeBuilder(BaseBuilder):
    """Main builder class for NuttX projects using CMake.

    This class allows you to trigger CMake commands, setup NuttX for a
    board:config, build, clean, menuconfig, etc.
    """

    DEFAULT_BUILD_DIR = "build"
    NINJA_FLAG = "-GNinja"

    def __init__(
        self,
        nuttxspace_path: Path,
        os_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
        apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
    ):
        """Initialize the NuttX builder class.

        Args:
            nuttxspace_path: Path to the NuttX repository workspace.
            os_dir: Name of the NuttX OS directory within the workspace.
                Defaults to "nuttx".
            apps_dir: Name of the NuttX apps directory within the workspace.
                Defaults to "nuttx-apps".
        """
        super().__init__(
            nuttxspace_path=nuttxspace_path,
            os_dir=os_dir,
            apps_dir=apps_dir,
        )
        self.use_ninja = True
        self.build_dir = self.DEFAULT_BUILD_DIR

        build_path = self.nuttx_path / self.build_dir
        if not build_path.exists():
            build_path.mkdir(parents=True, exist_ok=True)

    def cmake(self, command: str) -> subprocess.CompletedProcess:
        """Run any CMake command inside NuttX directory.

        Args:
            command: The CMake command to run. It can be any CMake command.
                Multiple arguments can be space-separated.

        Returns:
            subprocess.CompletedProcess: The result of the CMake command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info(f"Running CMake command: {command}")
        return self._execute_cmake(command.split())

    def build(self, parallel: int = None) -> subprocess.CompletedProcess:
        """Build the NuttX project using CMake.

        Args:
            parallel: Number of parallel jobs to use for building.
                If None, uses default CMake parallelism. Defaults to None.

        Returns:
            subprocess.CompletedProcess: The result of the build command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info(f"Starting build with parallel={parallel}")
        if parallel:
            args = [f"-j{parallel}"]
        else:
            args = []

        args.extend([CMakeAction.BUILD, self.build_dir])
        return self._execute_cmake(args)

    def clean(self) -> subprocess.CompletedProcess:
        """Clean build artifacts using CMake.

        Removes object files and other build artifacts, but preserves
        configuration files.

        Returns:
            subprocess.CompletedProcess: The result of the clean command.
                Check the returncode attribute to determine success (0) or failure.
        """
        logger.info("Running clean")
        cmd_list = [
            CMakeAction.BUILD,
            self.build_dir,
            CMakeAction.TARGET,
            CMakeAction.CLEAN,
        ]
        return self._execute_cmake(cmd_list)

    def menuconfig(self) -> int:
        """Run menuconfig using CMake.

        Opens the interactive menu configuration interface for NuttX.
        This is a curses-based interface that allows interactive configuration
        of NuttX build options.

        Returns:
            int: Exit code of the menuconfig command. Returns 0 on success.
        """
        logger.info("Running menuconfig")
        cmd_list = [
            BuildTool.CMAKE,
            CMakeAction.BUILD,
            self.build_dir,
            CMakeAction.TARGET,
            CMakeAction.MENUCONFIG,
        ]
        return utils.run_curses_command(cmd_list, cwd=self.nuttx_path)

    def distclean(self) -> None:
        """Perform a distclean on the NuttX project using CMake.

        Note: Distclean is not available on CMake builds. This method
        raises a RuntimeError to indicate that 'clean' should be used instead.

        Raises:
            RuntimeError: Always raised, as distclean is not available for CMake builds.
        """
        raise RuntimeError(
            "Distclean is not available on CMake builds. Use 'clean' instead."
        )

    def initialize(self, board: str, defconfig: str, extra_args: list[str] = []) -> int:
        """Run NuttX setup commands using CMake.

        Configures NuttX for the specified board and defconfig using CMake.
        This method sets up the build directory and configuration.

        Args:
            board: The board name (e.g., "stm32f4discovery").
            defconfig: The defconfig name (e.g., "nsh").
            extra_args: Additional arguments to pass to CMake.
                Defaults to empty list.

        Returns:
            int: Exit code of the CMake configuration. Returns 0 on success.
        """
        logger.info(f"Setting up NuttX: board={board}, defconfig={defconfig}")
        board_config = f"-DBOARD_CONFIG={board}:{defconfig}"

        cmd_list = [
            CMakeAction.BUILD_PATH,
            self.build_dir,
            board_config,
            self.NINJA_FLAG if self.use_ninja else "",
        ]

        ret = self._execute_cmake(cmd_list)
        return ret.returncode

    def ninja_backend(self, enable: bool) -> None:
        """Enable or disable Ninja generator for CMake.

        Args:
            enable: If True, use Ninja generator. If False, use default.
        """
        self.use_ninja = enable

    def _execute_cmake(self, args: list[str]) -> subprocess.CompletedProcess:
        """Helper method to execute CMake commands.

        Args:
            args: List of arguments to pass to the CMake command.

        Returns:
            subprocess.CompletedProcess: The result of the CMake command.
                Check the returncode attribute to determine success (0) or failure.
        """
        cmd_list = [BuildTool.CMAKE] + args
        ret = utils.run_make_command(
            cmd_list,
            cwd=self.nuttx_path.absolute(),
            no_stdout=self.no_stdout,
            no_stderr=self.no_stderr,
        )

        return ret


def nuttx_builder(
    nuttxspace_path: Path,
    os_dir: str = utils.NUTTX_DEFAULT_DIR_NAME,
    apps_dir: str = utils.NUTTX_APPS_DEFAULT_DIR_NAME,
    build_tool: BuildTool = BuildTool.MAKE,
):
    """Wrapper function used to select between the Make and CMake builders.

    Args:
        nuttxspace_path: Path to the NuttX repository workspace.
        os_dir: Name of the NuttX OS directory within the workspace.
            Defaults to "nuttx".
        apps_dir: Name of the NuttX apps directory within the workspace.
            Defaults to "nuttx-apps".
        build_tool: Build tool to use (Make or CMake). Defaults to Make.
    """

    if build_tool == BuildTool.MAKE:
        return MakeBuilder(
            nuttxspace_path=Path(nuttxspace_path), os_dir=os_dir, apps_dir=apps_dir
        )
    elif build_tool == BuildTool.CMAKE:
        return CMakeBuilder(
            nuttxspace_path=Path(nuttxspace_path), os_dir=os_dir, apps_dir=apps_dir
        )
    else:
        raise ValueError(f"Unsupported build tool: {build_tool}")
