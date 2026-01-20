"""
Tests for toolchain management classes.

This module contains tests for the class-based toolchain API including
ToolchainFileParser, ToolchainInstaller, and ManagePath.
"""

import os
import shutil
import stat
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from ntxbuild.toolchains import (
    ManagePath,
    Toolchain,
    ToolchainFileParser,
    ToolchainInstaller,
    ToolchainName,
)


class TestToolchain:
    """Tests for Toolchain dataclass."""

    def test_toolchain_creation_with_all_fields(self):
        """Test creating Toolchain with all fields."""
        toolchain = Toolchain(
            name="xtensa-esp-elf",
            url="https://example.com/toolchain.tar.xz",
            nuttx_version="12.12.0",
        )
        assert toolchain.name == "xtensa-esp-elf"
        assert toolchain.url == "https://example.com/toolchain.tar.xz"
        assert toolchain.nuttx_version == "12.12.0"

    def test_toolchain_creation_with_required_field_only(self):
        """Test creating Toolchain with only required name field."""
        toolchain = Toolchain(name="xtensa-esp-elf")
        assert toolchain.name == "xtensa-esp-elf"
        assert toolchain.url is None
        assert toolchain.nuttx_version is None

    def test_toolchain_creation_with_optional_fields(self):
        """Test creating Toolchain with some optional fields."""
        toolchain = Toolchain(
            name="gcc-arm-none-eabi", url="https://example.com/toolchain.tar.xz"
        )
        assert toolchain.name == "gcc-arm-none-eabi"
        assert toolchain.url == "https://example.com/toolchain.tar.xz"
        assert toolchain.nuttx_version is None


class TestToolchainName:
    """Tests for ToolchainName enum."""

    def test_toolchain_name_enum_values(self):
        """Test that all expected toolchain names exist in enum."""
        assert ToolchainName.CLANG_ARM_NONE_EABI == "clang-arm-none-eabi"
        assert ToolchainName.GCC_AARCH64_NONE_ELF == "gcc-aarch64-none-elf"
        assert ToolchainName.GCC_ARM_NONE_EABI == "gcc-arm-none-eabi"
        assert ToolchainName.XTENSA_ESP_ELF == "xtensa-esp-elf"
        assert ToolchainName.RISCV_NONE_ELF == "riscv-none-elf"

    def test_toolchain_name_str_method(self):
        """Test that __str__ returns the enum value."""
        assert str(ToolchainName.XTENSA_ESP_ELF) == "xtensa-esp-elf"
        assert str(ToolchainName.GCC_ARM_NONE_EABI) == "gcc-arm-none-eabi"


class TestToolchainFileParser:
    """Tests for ToolchainFileParser class."""

    def test_toolchain_file_parser_loads_from_package(self):
        """Test that ToolchainFileParser loads toolchains.ini from package."""
        parser = ToolchainFileParser()
        toolchains = parser.toolchains

        assert len(toolchains) > 0
        assert all(isinstance(t, Toolchain) for t in toolchains)
        assert all(t.name for t in toolchains)
        assert all(t.url for t in toolchains)
        assert all(t.nuttx_version for t in toolchains)

    def test_toolchain_file_parser_with_custom_path(self, tmp_path):
        """Test ToolchainFileParser with custom toolchains.ini path."""
        # Create a test toolchains.ini file
        toolchains_ini = tmp_path / "toolchains.ini"
        toolchains_ini.write_text(
            """[12.12.0]
xtensa-esp-elf = https://example.com/xtensa-esp-elf.tar.xz
"""
        )

        parser = ToolchainFileParser(toolchain_file_path=toolchains_ini)
        toolchains = parser.toolchains

        assert len(toolchains) == 1
        assert toolchains[0].name == "xtensa-esp-elf"
        assert toolchains[0].nuttx_version == "12.12.0"
        assert toolchains[0].url == "https://example.com/xtensa-esp-elf.tar.xz"

    def test_toolchain_file_parser_invalid_toolchain_name(self, tmp_path):
        """Test ToolchainFileParser raises ValueError for invalid toolchain name."""
        toolchains_ini = tmp_path / "toolchains.ini"
        toolchains_ini.write_text(
            """[12.12.0]
invalid-toolchain = https://example.com/toolchain.tar.xz
"""
        )

        with pytest.raises(ValueError, match="Invalid toolchain name"):
            ToolchainFileParser(toolchain_file_path=toolchains_ini)

    def test_toolchain_file_parser_no_sections(self, tmp_path):
        """Test ToolchainFileParser raises ValueError when no version sections found."""
        toolchains_ini = tmp_path / "toolchains.ini"
        toolchains_ini.write_text("# Empty file\n")

        with pytest.raises(ValueError, match="No version sections found"):
            ToolchainFileParser(toolchain_file_path=toolchains_ini)

    def test_toolchain_file_parser_latest_version(self):
        """Test that latest_version property returns the highest version."""
        parser = ToolchainFileParser()
        latest = parser.latest_version

        assert latest is not None
        # Should be a version object from packaging.version
        assert hasattr(latest, "major")
        assert hasattr(latest, "minor")

    def test_toolchain_file_parser_latest_version_cached(self):
        """Test that latest_version is cached after first access."""
        parser = ToolchainFileParser()
        latest1 = parser.latest_version
        latest2 = parser.latest_version

        assert latest1 is latest2  # Same object (cached)

    def test_toolchain_file_parser_toolchains_property(self):
        """Test that toolchains property returns list of Toolchain objects."""
        parser = ToolchainFileParser()
        toolchains = parser.toolchains

        assert isinstance(toolchains, list)
        assert len(toolchains) > 0
        for toolchain in toolchains:
            assert isinstance(toolchain, Toolchain)
            assert toolchain.name in [t.value for t in ToolchainName]


class TestToolchainInstaller:
    """Tests for ToolchainInstaller class."""

    # Class-level attributes to store archive paths
    archive_dir = None
    tar_xz_archive = None
    tar_gz_archive = None
    zip_archive = None

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_archives(self, tmp_path_factory):
        """Create test archives once for all tests in this class."""
        # Create a temporary directory for test archives
        archive_dir = tmp_path_factory.mktemp("test_archives")

        # Create tar.xz archive
        # Goes up to xtensa-esp-elf/bin/test_compiler
        tar_xz_path = archive_dir / "test_toolchain.tar.xz"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path_obj = Path(temp_dir)
            extracted_dir = temp_path_obj / "xtensa-esp-elf"
            extracted_dir.mkdir()
            (extracted_dir / "bin").mkdir()
            (extracted_dir / "bin" / "test_compiler").write_text(
                "#!/bin/bash\necho test\n"
            )
            os.chmod(extracted_dir / "bin" / "test_compiler", stat.S_IRWXU)

            with tarfile.open(tar_xz_path, "w:xz") as tar:
                tar.add(extracted_dir, arcname="xtensa-esp-elf")

        # Create tar.gz archive
        tar_gz_path = archive_dir / "test_toolchain.tar.gz"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path_obj = Path(temp_dir)
            extracted_dir = temp_path_obj / "riscv-none-elf"
            extracted_dir.mkdir()
            (extracted_dir / "bin").mkdir()
            (extracted_dir / "bin" / "compiler").write_text("#!/bin/bash\necho test\n")
            os.chmod(extracted_dir / "bin" / "compiler", stat.S_IRWXU)

            with tarfile.open(tar_gz_path, "w:gz") as tar:
                tar.add(extracted_dir, arcname="riscv-none-elf")

        # Create zip archive
        import zipfile

        zip_path = archive_dir / "test_toolchain.zip"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path_obj = Path(temp_dir)
            extracted_dir = temp_path_obj / "xtensa-esp-elf"
            extracted_dir.mkdir()
            (extracted_dir / "bin").mkdir()
            compiler_file = extracted_dir / "bin" / "compiler"
            compiler_file.write_text("#!/bin/bash\necho test\n")
            os.chmod(compiler_file, stat.S_IRWXU)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
                # Add the directory structure to the zip
                for root, dirs, files in os.walk(extracted_dir):
                    for file in files:
                        file_path = Path(root) / file
                        # Use relative path preserve structure
                        arcname = file_path.relative_to(extracted_dir.parent)
                        zip_ref.write(file_path, arcname)

        # Store paths as class attributes for use in tests
        TestToolchainInstaller.archive_dir = archive_dir
        TestToolchainInstaller.tar_xz_archive = tar_xz_path
        TestToolchainInstaller.tar_gz_archive = tar_gz_path
        TestToolchainInstaller.zip_archive = zip_path

        print(f"Archive directory: {archive_dir}")
        print(f"Tar.xz archive: {tar_xz_path}")
        print(f"Tar.gz archive: {tar_gz_path}")
        print(f"Zip archive: {zip_path}")

        yield

        # Cleanup happens automatically when tmp_path_factory cleans up

    def test_toolchain_installer_init_with_version(self):
        """Test ToolchainInstaller initialization with specific version."""
        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")
        assert installer._toolchain_name == "xtensa-esp-elf"
        assert installer._nuttx_version == "12.12.0"
        assert installer._toolchain_install is not None
        assert installer._toolchain_install.name == "xtensa-esp-elf"
        assert installer._toolchain_install.nuttx_version == "12.12.0"

    def test_toolchain_installer_init_without_version(self):
        """Test ToolchainInstaller initialization defaults to latest version."""
        parser = ToolchainFileParser()
        latest_version = str(parser.latest_version)

        installer = ToolchainInstaller("xtensa-esp-elf")
        assert installer._toolchain_name == "xtensa-esp-elf"
        assert installer._nuttx_version == latest_version

    def test_toolchain_installer_init_invalid_toolchain(self):
        """Test ToolchainInstaller raises AssertionError for invalid toolchain."""
        with pytest.raises(AssertionError, match="not found in toolchains.ini"):
            ToolchainInstaller("invalid-toolchain", "12.12.0")

    def test_toolchain_installer_init_invalid_version(self):
        """Test ToolchainInstaller raises AssertionError for invalid version."""
        with pytest.raises(AssertionError, match="not found in toolchains.ini"):
            ToolchainInstaller("xtensa-esp-elf", "99.99.99")

    def test_toolchain_installer_init_toolchain_not_in_version(self):
        """Test ToolchainInstaller raises ValueError when toolchain not in version."""
        # Use a toolchain that exists but not in the specified version
        with pytest.raises(AssertionError, match="not found in toolchains.ini"):
            ToolchainInstaller("clang-arm-none-eabi", "5.0.0")

    def test_toolchain_installer_install_creates_directory(self, tmp_path, monkeypatch):
        """Test that install() works when directory exists."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()  # Directory must exist before install() is called
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")

        def mock_urlretrieve(url, filename):
            shutil.copy(TestToolchainInstaller.tar_xz_archive, filename)

            with patch(
                "ntxbuild.toolchains.urllib.request.urlretrieve",
                side_effect=mock_urlretrieve,
            ):
                result = installer.install(ntxenv_dir)

            assert result == ntxenv_dir
            toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
            assert toolchain_dir.exists()
            assert (toolchain_dir / "bin").exists()

    def test_toolchain_installer_install_already_installed(self, tmp_path, monkeypatch):
        """Test that install() returns early if toolchain already installed."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Pre-create the toolchain directory
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        (toolchain_dir / "bin").mkdir(parents=True)

        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")

        # Should not download, just return
        with pytest.raises(FileExistsError):
            installer.install(ntxenv_dir)

    def test_toolchain_installer_install_mocks_url_download(
        self, tmp_path, monkeypatch
    ):
        """Test that install() uses mocked URL download instead of real download."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")

        download_called = False

        def mock_urlretrieve(url, filename):
            nonlocal download_called
            download_called = True
            shutil.copy(TestToolchainInstaller.tar_xz_archive, filename)

        with patch(
            "ntxbuild.toolchains.urllib.request.urlretrieve",
            side_effect=mock_urlretrieve,
        ):
            installer.install(ntxenv_dir)

            assert download_called, "urlretrieve should have been called"
            toolchain_dir = ntxenv_dir / "xtensa-esp-elf" / "xtensa-esp-elf"
            assert toolchain_dir.exists()
            assert (toolchain_dir / "bin").exists()

    def test_toolchain_installer_install_handles_tar_xz(self, tmp_path, monkeypatch):
        """Test that install() handles .tar.xz archives correctly."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")

        def mock_urlretrieve(url, filename):
            print(f"Mocking URL retrieve for: {url} to {filename}")
            shutil.copy(TestToolchainInstaller.tar_xz_archive, filename)

        with patch(
            "ntxbuild.toolchains.urllib.request.urlretrieve",
            side_effect=mock_urlretrieve,
        ):
            installer.install(ntxenv_dir)

            toolchain_dir = ntxenv_dir / "xtensa-esp-elf" / "xtensa-esp-elf"
            assert toolchain_dir.exists()
            assert (toolchain_dir / "bin").exists()

    def test_toolchain_installer_install_handles_tar_gz(self, tmp_path, monkeypatch):
        """Test that install() handles .tar.gz archives correctly."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a custom toolchains.ini with .tar.gz URL
        toolchains_ini = tmp_path / "toolchains.ini"
        toolchains_ini.write_text(
            """[12.12.0]
riscv-none-elf = https://example.com/riscv-none-elf.tar.gz
"""
        )

        installer = ToolchainInstaller(
            "riscv-none-elf", "12.12.0", toolchain_file_path=toolchains_ini
        )

        def mock_urlretrieve(url, filename):
            print(f"Mocking URL retrieve for: {url} to {filename}")
            shutil.copy(TestToolchainInstaller.tar_gz_archive, filename)

        with patch(
            "ntxbuild.toolchains.urllib.request.urlretrieve",
            side_effect=mock_urlretrieve,
        ):
            installer.install(ntxenv_dir)

            toolchain_dir = ntxenv_dir / "riscv-none-elf" / "riscv-none-elf"
            assert toolchain_dir.exists()
            assert (toolchain_dir / "bin").exists()

    def test_toolchain_installer_install_handles_zip(self, tmp_path, monkeypatch):
        """Test that install() handles .zip archives correctly."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a custom toolchains.ini with .zip URL
        toolchains_ini = tmp_path / "toolchains.ini"
        toolchains_ini.write_text(
            """[12.12.0]
xtensa-esp-elf = https://example.com/xtensa-esp-elf.zip
"""
        )

        installer = ToolchainInstaller(
            "xtensa-esp-elf", "12.12.0", toolchain_file_path=toolchains_ini
        )

        def mock_urlretrieve(url, filename):
            # Verify the URL ends with .zip (from our custom toolchains.ini)
            assert url.endswith(".zip"), f"URL should end with .zip but got: {url}"
            # Copy the zip archive to the destination
            shutil.copy(TestToolchainInstaller.zip_archive, filename)
            # Verify the copied file is a valid zip
            import zipfile

            assert zipfile.is_zipfile(
                filename
            ), f"Copied file is not a valid zip: {filename}"

        with patch(
            "ntxbuild.toolchains.urllib.request.urlretrieve",
            side_effect=mock_urlretrieve,
        ):
            installer.install(ntxenv_dir)

            toolchain_dir = ntxenv_dir / "xtensa-esp-elf" / "xtensa-esp-elf"
            assert toolchain_dir.exists()
            assert (toolchain_dir / "bin").exists()

    def test_toolchain_installer_install_unsupported_format(
        self, tmp_path, monkeypatch
    ):
        """Test that install() raises RuntimeError for unsupported archive format."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a custom toolchains.ini with unsupported format
        toolchains_ini = tmp_path / "toolchains.ini"
        toolchains_ini.write_text(
            """[12.12.0]
xtensa-esp-elf = https://example.com/xtensa-esp-elf.rar
"""
        )

        installer = ToolchainInstaller(
            "xtensa-esp-elf", "12.12.0", toolchain_file_path=toolchains_ini
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path_obj = Path(temp_dir)
            archive_path = temp_path_obj / "toolchain.rar"
            archive_path.write_text("fake archive")

            def mock_urlretrieve(url, filename):
                shutil.copy(archive_path, filename)

            with patch(
                "ntxbuild.toolchains.urllib.request.urlretrieve",
                side_effect=mock_urlretrieve,
            ):
                with pytest.raises(RuntimeError, match="Unsupported archive format"):
                    installer.install(ntxenv_dir)

    def test_toolchain_installer_install_download_failure(self, tmp_path, monkeypatch):
        """Test that install() raises RuntimeError when download fails."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")

        def mock_urlretrieve(url, filename):
            raise Exception("Network error")

        with patch(
            "ntxbuild.toolchains.urllib.request.urlretrieve",
            side_effect=mock_urlretrieve,
        ):
            with pytest.raises(RuntimeError, match="Failed to download toolchain"):
                installer.install(ntxenv_dir)

    def test_toolchain_installer_install_location_not_path(self, tmp_path, monkeypatch):
        """Test that install() raises AssertionError when location is not a Path."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        installer = ToolchainInstaller("xtensa-esp-elf", "12.12.0")

        with pytest.raises(AssertionError, match="must be a Path object"):
            installer.install("/some/string/path")


class TestManagePath:
    """Tests for ManagePath class."""

    def test_manage_path_init_loads_toolchains(self, tmp_path, monkeypatch):
        """Test that ManagePath loads installed toolchains on init."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a toolchain directory structure (as installed by ToolchainInstaller)
        # The structure is: ntxenv / toolchain_name / <extracted_dir> / bin
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        # Simulate extracted archive structure (version directory inside)
        version_dir = toolchain_dir / "xtensa-esp-elf-14.2.0"
        bin_dir = version_dir / "bin"
        bin_dir.mkdir(parents=True)
        compiler = bin_dir / "compiler"
        compiler.write_text("#!/bin/bash\necho test\n")
        os.chmod(compiler, stat.S_IRWXU)

        manager = ManagePath(toolchain_location=ntxenv_dir)
        assert len(manager._installed_toolchains) > 0
        assert ToolchainName.XTENSA_ESP_ELF in manager._installed_toolchains

    def test_manage_path_add_toolchain_to_path(self, tmp_path, monkeypatch):
        """Test that add_toolchain_to_path adds toolchain bin to PATH."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a toolchain directory structure (as installed by ToolchainInstaller)
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        # Simulate extracted archive structure (version directory inside)
        version_dir = toolchain_dir / "xtensa-esp-elf-14.2.0"
        bin_dir = version_dir / "bin"
        bin_dir.mkdir(parents=True)
        compiler = bin_dir / "compiler"
        compiler.write_text("#!/bin/bash\necho test\n")
        os.chmod(compiler, stat.S_IRWXU)

        original_path = os.environ.get("PATH", "")

        try:
            manager = ManagePath(toolchain_location=ntxenv_dir)
            manager.add_toolchain_to_path("xtensa-esp-elf")

            current_path = os.environ.get("PATH", "")
            assert str(bin_dir.resolve()) in current_path
            assert current_path.startswith(str(bin_dir.resolve()) + os.pathsep)
        finally:
            os.environ["PATH"] = original_path

    def test_manage_path_add_toolchain_to_path_idempotent(self, tmp_path, monkeypatch):
        """Test that add_toolchain_to_path is idempotent."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create a toolchain directory structure (as installed by ToolchainInstaller)
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        version_dir = toolchain_dir / "xtensa-esp-elf-14.2.0"
        bin_dir = version_dir / "bin"
        bin_dir.mkdir(parents=True)
        compiler = bin_dir / "compiler"
        compiler.write_text("#!/bin/bash\necho test\n")
        os.chmod(compiler, stat.S_IRWXU)

        original_path = os.environ.get("PATH", "")

        try:
            manager = ManagePath(toolchain_location=ntxenv_dir)
            manager.add_toolchain_to_path("xtensa-esp-elf")
            first_path = os.environ.get("PATH", "")

            manager.add_toolchain_to_path("xtensa-esp-elf")
            second_path = os.environ.get("PATH", "")

            assert first_path == second_path
            assert second_path.count(str(bin_dir.resolve())) == 1
        finally:
            os.environ["PATH"] = original_path

    def test_manage_path_add_toolchain_not_installed(self, tmp_path, monkeypatch):
        """Test that add_toolchain_to_path raises AssertionError for non-installed
        toolchain.
        """
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        manager = ManagePath(toolchain_location=ntxenv_dir)

        with pytest.raises(AssertionError, match="not found in"):
            manager.add_toolchain_to_path("xtensa-esp-elf")

    def test_manage_path_parse_toolchain_directory_no_subdirs(
        self, tmp_path, monkeypatch
    ):
        """Test that _parse_toolchain_directory raises RuntimeError when
        no subdirectories.
        """
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create toolchain dir with no subdirectories (only files)
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        toolchain_dir.mkdir()
        (toolchain_dir / "file.txt").write_text("test")

        manager = ManagePath(toolchain_location=ntxenv_dir)
        manager._installed_toolchains = [ToolchainName.XTENSA_ESP_ELF]

        with pytest.raises(RuntimeError, match="does not contain any subdirectories"):
            manager.add_toolchain_to_path("xtensa-esp-elf")

    def test_manage_path_parse_toolchain_directory_no_bin(self, tmp_path, monkeypatch):
        """Test that _parse_toolchain_directory raises RuntimeError when no bin
        directory.
        """
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create toolchain dir with subdirectory but no bin
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        version_dir = toolchain_dir / "xtensa-esp-elf-14.2.0"
        version_dir.mkdir(parents=True)

        manager = ManagePath(toolchain_location=ntxenv_dir)
        manager._installed_toolchains = [ToolchainName.XTENSA_ESP_ELF]

        with pytest.raises(RuntimeError, match="No 'bin' directory found"):
            manager.add_toolchain_to_path("xtensa-esp-elf")

    def test_manage_path_parse_toolchain_directory_no_executable(
        self, tmp_path, monkeypatch
    ):
        """Test that _parse_toolchain_directory raises RuntimeError when
        no executable files.
        """
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create toolchain dir with bin but no executables
        toolchain_dir = ntxenv_dir / "xtensa-esp-elf"
        version_dir = toolchain_dir / "xtensa-esp-elf-14.2.0"
        bin_dir = version_dir / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "file.txt").write_text("not executable")

        manager = ManagePath(toolchain_location=ntxenv_dir)
        manager._installed_toolchains = [ToolchainName.XTENSA_ESP_ELF]

        with pytest.raises(RuntimeError, match="No executable files found"):
            manager.add_toolchain_to_path("xtensa-esp-elf")

    def test_manage_path_match_toolchain_name(self, tmp_path):
        """Test that _match_toolchain_name returns correct ToolchainName enum."""
        manager = ManagePath(toolchain_location=tmp_path)
        result = manager._match_toolchain_name("xtensa-esp-elf")
        assert result == ToolchainName.XTENSA_ESP_ELF

    def test_manage_path_match_toolchain_name_invalid(self, tmp_path):
        """Test that _match_toolchain_name raises ValueError for invalid name."""
        manager = ManagePath(toolchain_location=tmp_path)
        with pytest.raises(ValueError, match="not found"):
            manager._match_toolchain_name("invalid-toolchain")

    def test_manage_path_multiple_toolchains(self, tmp_path, monkeypatch):
        """Test that multiple toolchains can be added to PATH."""
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()
        ntxenv_dir = fake_home / "ntxenv"
        ntxenv_dir.mkdir()
        monkeypatch.setattr(Path, "home", lambda: fake_home)

        # Create multiple toolchain directories (as installed by ToolchainInstaller)
        for toolchain_name in ["xtensa-esp-elf", "gcc-arm-none-eabi"]:
            toolchain_dir = ntxenv_dir / toolchain_name
            # Simulate extracted archive structure
            version_dir = toolchain_dir / f"{toolchain_name}-1.0.0"
            bin_dir = version_dir / "bin"
            bin_dir.mkdir(parents=True)
            compiler = bin_dir / "compiler"
            compiler.write_text("#!/bin/bash\necho test\n")
            os.chmod(compiler, stat.S_IRWXU)

        original_path = os.environ.get("PATH", "")

        try:
            manager = ManagePath(toolchain_location=ntxenv_dir)
            manager.add_toolchain_to_path("xtensa-esp-elf")
            manager.add_toolchain_to_path("gcc-arm-none-eabi")

            current_path = os.environ.get("PATH", "")
            assert "xtensa-esp-elf" in current_path
            assert "gcc-arm-none-eabi" in current_path
        finally:
            os.environ["PATH"] = original_path
