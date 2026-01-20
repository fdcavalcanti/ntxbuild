"""
Toolchain management functions for NuttX builds.

This module provides classes and functions for installing, managing, and
configuring toolchains for NuttX development. It handles downloading,
extracting, and managing toolchain installations from various sources.
"""

import configparser
import logging
import os
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import List, Optional

from packaging import version

from .utils import NTXBUILD_DEFAULT_USER_DIR

logger = logging.getLogger("ntxbuild.toolchains")

DEFAULT_TOOLCHAIN_LOCATION = NTXBUILD_DEFAULT_USER_DIR / "toolchains"


@dataclass
class Toolchain:
    """Represents a toolchain configuration.

    This dataclass stores information about a toolchain including its name,
    download URL, associated NuttX version, and binary directory path.

    Attributes:
        name: Name of the toolchain.
        url: URL to download the toolchain archive. Defaults to None.
        nuttx_version: NuttX version this toolchain is associated with.
            Defaults to None.
    """

    name: str
    url: Optional[str] = None
    nuttx_version: Optional[str] = None


class ToolchainName(str, Enum):
    """Enumeration of supported toolchain names.

    This enum defines all available toolchain names that can be installed
    and managed by the toolchain system.

    Attributes:
        CLANG_ARM_NONE_EABI: Clang ARM none EABI toolchain.
        GCC_AARCH64_NONE_ELF: GCC AArch64 none ELF toolchain.
        GCC_ARM_NONE_EABI: GCC ARM none EABI toolchain.
        XTENSA_ESP_ELF: Xtensa ESP ELF toolchain.
        RISCV_NONE_ELF: RISC-V none ELF toolchain.
    """

    CLANG_ARM_NONE_EABI = "clang-arm-none-eabi"
    GCC_AARCH64_NONE_ELF = "gcc-aarch64-none-elf"
    GCC_ARM_NONE_EABI = "gcc-arm-none-eabi"
    XTENSA_ESP_ELF = "xtensa-esp-elf"
    RISCV_NONE_ELF = "riscv-none-elf"

    def __str__(self):
        """Return the string value of the toolchain name.

        Returns:
            str: The toolchain name as a string.
        """
        return self.value


class ToolchainFileParser:
    """Parser for toolchain configuration files.

    This class reads and parses toolchain configuration files (toolchains.ini)
    to extract toolchain information including names, URLs, and associated
    NuttX versions.
    """

    def __init__(self, toolchain_file_path: Optional[Path] = None):
        """Initialize the ToolchainFileParser.

        Args:
            toolchain_file_path: Path to the toolchain configuration file.
                If None, uses the default toolchains.ini from the package.
                Defaults to None.
        """
        if toolchain_file_path is None:
            self.toolchain_file_path = resources.files("ntxbuild").joinpath(
                "toolchains.ini"
            )
        else:
            self.toolchain_file_path = toolchain_file_path
        self._toolchains = []
        self._latest_version = None
        self._load_toolchains()

    @property
    def toolchains(self) -> List[Toolchain]:
        """Get the list of parsed toolchains.

        Returns:
            List[Toolchain]: List of Toolchain objects parsed from the
                configuration file.
        """
        if not self._toolchains:
            self._load_toolchains()
        return self._toolchains

    @property
    def latest_version(self) -> Optional[str]:
        """Get the latest NuttX version from the toolchain configurations.

        Returns:
            Optional[str]: The latest NuttX version string, or None if no
                toolchains are available.
        """
        if not self._latest_version:
            version_list = [
                version.parse(toolchain.nuttx_version) for toolchain in self.toolchains
            ]
            self._latest_version = max(version_list)
            logger.debug(f"Latest NuttX version: {self._latest_version}")
        return self._latest_version

    def _load_toolchains(self):
        """Load toolchains from the configuration file.

        Parses the toolchains.ini file and populates the internal toolchain
        list. Validates that all toolchain names match known ToolchainName
        enum values.

        Raises:
            ValueError: If no version sections are found in the configuration
                file, or if an invalid toolchain name is encountered.
        """
        with self.toolchain_file_path.open("r", encoding="utf-8") as f:
            config = configparser.ConfigParser()
            config.read_file(f)

        # Get all sections (excluding DEFAULT)
        sections = [s for s in config.sections() if s != "DEFAULT"]
        if not sections:
            raise ValueError("No version sections found in toolchains.ini")

        for section in sections:
            for toolchain_name, toolchain_url in config[section].items():
                if toolchain_name not in [t.value for t in ToolchainName]:
                    raise ValueError(f"Invalid toolchain name: {toolchain_name}")
                self._toolchains.append(
                    Toolchain(
                        name=toolchain_name, url=toolchain_url, nuttx_version=section
                    )
                )

        logger.debug(f"Loaded {len(self._toolchains)} toolchains")
        for toolchain in self._toolchains:
            logger.debug(
                f"Toolchain: {toolchain.name}, "
                f"NuttX version: {toolchain.nuttx_version}, "
                f"URL: {toolchain.url}"
            )


class ToolchainInstaller(ToolchainFileParser):
    """Installer for NuttX toolchains.

    This class handles downloading and installing toolchains from remote
    URLs. It supports various archive formats and manages the installation
    process including extraction and directory structure setup.
    """

    def __init__(
        self,
        toolchain_name: str,
        nuttx_version: Optional[str] = None,
        toolchain_file_path: Optional[Path] = None,
    ):
        """Initialize the ToolchainInstaller.

        Args:
            toolchain_name: Name of the toolchain to install. Must match
                a toolchain name in the configuration file.
            nuttx_version: NuttX version to use. If None, uses the latest
                available version. Defaults to None.
            toolchain_file_path: Path to the toolchain configuration file.
                If None, uses the default toolchains.ini from the package.
                Defaults to None.

        Raises:
            AssertionError: If the toolchain name is not found in the
                configuration file, or if the specified NuttX version
                is not found.
            ValueError: If the toolchain and NuttX version combination
                is not found in the configuration file.
        """
        super().__init__(toolchain_file_path)
        self._toolchain_name = toolchain_name
        self._toolchain_install = None
        self._nuttx_version = nuttx_version

        assert self._toolchain_name in [
            toolchain.name for toolchain in self.toolchains
        ], f"Toolchain: '{self._toolchain_name}' not found in toolchains.ini"

        if self._nuttx_version is None:
            self._nuttx_version = str(self.latest_version)
        else:
            self._nuttx_version = nuttx_version
            assert self._nuttx_version in [
                toolchain.nuttx_version for toolchain in self.toolchains
            ], f"NuttX version {self._nuttx_version} not found in toolchains.ini"

        for toolchain in self.toolchains:
            if (
                toolchain.name == self._toolchain_name
                and toolchain.nuttx_version == self._nuttx_version
            ):
                self._toolchain_install = toolchain
                break
        else:
            raise ValueError(
                f"Toolchain '{self._toolchain_name}' NuttX version "
                f"{self._nuttx_version} not found in toolchains.ini"
            )

        logger.info(
            f"Ready to install toolchain {self._toolchain_name} version "
            f"{self._nuttx_version} from {self._toolchain_install.url}"
        )

    def install(self, location: Path = DEFAULT_TOOLCHAIN_LOCATION):
        """Install the toolchain to the specified location.

        Downloads the toolchain archive, extracts it, and sets up the
        directory structure. The toolchain will be installed in a
        subdirectory named after the toolchain.

        Args:
            location: Base directory where the toolchain should be installed.
                Defaults to DEFAULT_TOOLCHAIN_LOCATION.

        Returns:
            Path: The path where the toolchain was installed.

        Raises:
            AssertionError: If location is not a Path object.
            FileExistsError: If the toolchain directory already exists.
            RuntimeError: If downloading or extracting the toolchain fails.
        """
        assert isinstance(location, Path), f"Location must be a Path object: {location}"

        location = Path(location).expanduser()
        location.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Installing toolchain {self._toolchain_name} version "
            f"{self._nuttx_version} to {location}"
        )
        self._download_and_extract_toolchain(location)
        return location

    @property
    def toolchain_name(self) -> str:
        """Get the toolchain name.

        Returns:
            str: The name of the toolchain being installed.
        """
        return self._toolchain_name

    @property
    def nuttx_version(self) -> str:
        """Get the NuttX version.

        Returns:
            str: The NuttX version associated with this toolchain installation.
        """
        return self._nuttx_version

    def _download_and_extract_toolchain(self, location: Path):
        """Download and extract the toolchain archive.

        Downloads the toolchain archive from the configured URL, extracts it
        to a temporary directory, and moves it to the final installation
        location. Supports multiple archive formats including tar.xz, tar.gz,
        tar.bz2, tar, and zip.

        Args:
            location: Base directory where the toolchain should be installed.

        Raises:
            FileExistsError: If the toolchain directory already exists.
            RuntimeError: If downloading or extracting the toolchain fails,
                or if the bin directory is not found after installation.
        """
        toolchain_dir = location / self._toolchain_name
        if toolchain_dir.exists():
            raise FileExistsError(
                f"Toolchain {self._toolchain_name} already installed at {toolchain_dir}"
            )
        else:
            toolchain_dir.mkdir(parents=True, exist_ok=True)

        # Create temporary directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            archive_path = temp_path / Path(self._toolchain_install.url).name

            # Download the archive
            logger.info("Downloading toolchain archive...")
            try:
                urllib.request.urlretrieve(self._toolchain_install.url, archive_path)
                logger.info(f"Downloaded to {archive_path}")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to download toolchain from "
                    f"{self._toolchain_install.url}: {e}"
                )

            # Extract the archive
            logger.info("Extracting toolchain archive...")
            try:
                if archive_path.suffix == ".xz" or archive_path.suffixes[-2:] == [
                    ".tar",
                    ".xz",
                ]:
                    with tarfile.open(archive_path, "r:xz") as tar:
                        tar.extractall(path=temp_path)
                elif archive_path.suffix == ".gz" or archive_path.suffixes[-2:] == [
                    ".tar",
                    ".gz",
                ]:
                    with tarfile.open(archive_path, "r:gz") as tar:
                        tar.extractall(path=temp_path)
                elif archive_path.suffix == ".bz2" or archive_path.suffixes[-2:] == [
                    ".tar",
                    ".bz2",
                ]:
                    with tarfile.open(archive_path, "r:bz2") as tar:
                        tar.extractall(path=temp_path)
                elif archive_path.suffix == ".tar":
                    with tarfile.open(archive_path, "r") as tar:
                        tar.extractall(path=temp_path)
                elif archive_path.suffix == ".zip":
                    import zipfile

                    with zipfile.ZipFile(archive_path, "r") as zip_ref:
                        zip_ref.extractall(path=temp_path)
                else:
                    raise RuntimeError(
                        f"Unsupported archive format: {archive_path.suffix}"
                    )

                logger.info(f"Extracted to {temp_path}")

                # Find the extracted directory (usually one top-level directory)
                extracted_items = list(temp_path.iterdir())
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    extracted_dir = extracted_items[0]
                else:
                    # Multiple items or files at root, use temp_path as base
                    extracted_dir = temp_path

                # Move extracted directory to final location
                if toolchain_dir.exists():
                    shutil.rmtree(toolchain_dir)
                shutil.move(str(extracted_dir), str(toolchain_dir))
                logger.info(f"Toolchain installed to {toolchain_dir}")

            except Exception as e:
                # Clean up partial installation
                if toolchain_dir.exists():
                    shutil.rmtree(toolchain_dir, ignore_errors=True)
                raise RuntimeError(f"Failed to extract toolchain: {e}")

        # Verify bin directory exists
        if not toolchain_dir.exists():
            raise RuntimeError(
                f"Toolchain installed but bin directory not found at {toolchain_dir}"
            )

        logger.info(
            f"Toolchain {self._toolchain_name} installed successfully at "
            f"{toolchain_dir}"
        )

        return toolchain_dir


class ManagePath:
    """Manages toolchain PATH environment variable.

    This class handles adding toolchain binary directories to the system PATH
    environment variable. It discovers installed toolchains and provides
    methods to manage their availability in the current environment.
    """

    def __init__(self, toolchain_location: Path = DEFAULT_TOOLCHAIN_LOCATION):
        """Initialize the ManagePath instance.

        Args:
            toolchain_location: Base directory where toolchains are installed.
                Defaults to DEFAULT_TOOLCHAIN_LOCATION.
        """
        self._toolchain_location = toolchain_location
        self._supported_toolchains = [str(t) for t in ToolchainName]
        self._installed_toolchains = []
        self._load_toolchains()

    @property
    def supported_toolchains(self) -> List[str]:
        """Get the list of supported toolchain names.

        Returns:
            List[str]: List of all supported toolchain names as strings.
        """
        return self._supported_toolchains

    @property
    def installed_toolchains(self) -> List[ToolchainName]:
        """Get the list of installed toolchains.

        Returns:
            List[ToolchainName]: List of ToolchainName enum values for
                toolchains that are currently installed.
        """
        return self._installed_toolchains

    def add_all_toolchains_to_path(self):
        """Add all installed toolchains to the PATH environment variable.

        Iterates through all installed toolchains and adds their binary
        directories to the system PATH.
        """
        for toolchain in self._installed_toolchains:
            self.add_toolchain_to_path(str(toolchain))

    def add_toolchain_to_path(self, toolchain_name: str):
        """Add a specific toolchain's binary directory to PATH.

        Finds the toolchain's bin directory and prepends it to the PATH
        environment variable. If the directory is already in PATH, it
        is not added again.

        Args:
            toolchain_name: Name of the toolchain to add to PATH.

        Raises:
            AssertionError: If the toolchain is not found in the toolchain
                location, or if adding to PATH fails.
            ValueError: If the toolchain name does not match any known
                toolchain.
            RuntimeError: If the toolchain directory structure is invalid
                or the bin directory cannot be found.
        """
        assert (
            toolchain_name in self._installed_toolchains
        ), f"Toolchain {toolchain_name} not found in {self._toolchain_location}"

        toolchain = self._match_toolchain_name(toolchain_name)
        toolchain_bin_path = self._parse_toolchain_directory(
            self._toolchain_location / str(toolchain)
        )
        bin_path_str = str(toolchain_bin_path.resolve())

        # Current PATH
        current_path = os.environ.get("PATH", "")

        # Check if already in PATH (avoid duplicates)
        path_dirs = current_path.split(os.pathsep)
        if bin_path_str in path_dirs:
            logger.debug(f"Toolchain bin directory already in PATH: {bin_path_str}")
            return

        # Prepend to PATH
        new_path = os.pathsep.join([bin_path_str, current_path])
        os.environ["PATH"] = new_path
        assert (
            bin_path_str in os.environ["PATH"]
        ), f"Failed to add toolchain bin directory to PATH: {bin_path_str}"
        logger.info(f"Added toolchain bin directory to PATH: {bin_path_str}")

    def _match_toolchain_name(self, toolchain_name: str) -> ToolchainName:
        """Match a toolchain name string to a ToolchainName enum value.

        Args:
            toolchain_name: Toolchain name as a string.

        Returns:
            ToolchainName: The corresponding ToolchainName enum value.

        Raises:
            ValueError: If the toolchain name does not match any known
                toolchain.
        """
        for toolchain in ToolchainName:
            if toolchain.value == toolchain_name:
                return toolchain
        raise ValueError(f"Toolchain {toolchain_name} not found")

    def _load_toolchains(self):
        """Load installed toolchains from the toolchain location.

        Scans the toolchain location directory and identifies which
        toolchains are currently installed by matching directory names
        against supported toolchain names.
        """
        logger.debug(f"Loading toolchains from {self._toolchain_location}")
        logger.debug(
            f"Matching to the following toolchains: {self._supported_toolchains}"
        )

        if not self._toolchain_location.exists():
            logger.debug(f"No toolchains installed at {self._toolchain_location}")
            return

        for toolchain_dir in self._toolchain_location.iterdir():
            if not toolchain_dir.is_dir():
                continue

            if toolchain_dir.name not in self._supported_toolchains:
                continue

            for toolchain in ToolchainName:
                if toolchain_dir.name == str(toolchain):
                    self._installed_toolchains.append(toolchain)
                    break

        logger.debug(
            f"Found {len(self._installed_toolchains)} toolchain(s) in "
            f"{self._toolchain_location}"
        )

    def _parse_toolchain_directory(self, toolchain_dir_path: Path) -> Path:
        """Parse a toolchain directory to find the bin directory.

        Examines the toolchain directory structure to locate the binary
        directory. Handles cases where the toolchain may be nested in a
        version-specific subdirectory.

        Args:
            toolchain_dir_path: Path to the toolchain directory.

        Returns:
            Path: Path to the toolchain's bin directory.

        Raises:
            RuntimeError: If the toolchain directory structure is invalid,
                if no bin directory is found, or if no executable files
                are found in the bin directory.
        """
        files = [f for f in list(toolchain_dir_path.iterdir()) if f.is_dir()]
        if len(files) == 0:
            raise RuntimeError(
                "Toolchain directory does not contain any subdirectories: "
                f"{toolchain_dir_path}"
            )
        if len(files) > 1:
            logger.warning(
                "Toolchain directory contains multiple versions. "
                "Using the first directory available as the toolchain version."
            )

        bin_dir = files[0] / "bin"
        if not bin_dir.exists() or not bin_dir.is_dir():
            raise RuntimeError(
                f"No 'bin' directory found in toolchain directory: {toolchain_dir_path}"
            )

        # Find at least one executable file in bin_dir
        has_executable = False
        for file in bin_dir.iterdir():
            if file.is_file() and os.access(file, os.X_OK):
                has_executable = True
                break

        if not has_executable:
            raise RuntimeError(
                f"No executable files found in 'bin' directory: {bin_dir}"
            )

        return bin_dir
