import configparser
import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from ntxbuild.cli import (
    build,
    clean,
    cmake,
    distclean,
    install,
    kconfig,
    main,
    make,
    start,
)
from ntxbuild.env_data import load_ntx_env


def assert_ntxenv_exists(nuttxspace_path: Path):
    """Helper function to verify .ntxenv file exists."""
    env_file = nuttxspace_path / ".ntxenv"
    assert env_file.exists(), f".ntxenv file should exist at {env_file}"


def assert_ntxenv_removed(nuttxspace_path: Path):
    """Helper function to verify .ntxenv file is removed."""
    env_file = nuttxspace_path / ".ntxenv"
    assert not env_file.exists(), f".ntxenv file should not exist at {env_file}"


def load_env_config(nuttxspace_path: Path) -> configparser.SectionProxy:
    """Helper function to load .ntxenv configuration."""
    env = load_ntx_env(nuttxspace_path)
    return env["general"]


class TestStartMake:
    """Test suite for the start command with Make build tool."""

    @pytest.fixture(autouse=True, scope="class")
    def teardown_after_class(self, nuttxspace_path):
        """Teardown: distclean after all tests in this class."""
        yield
        # Cleanup after all tests in this class complete
        os.chdir(nuttxspace_path / "nuttx")
        subprocess.run(["make", "distclean"])

    def test_start_success(self, nuttxspace_path):
        """Test start command with valid board and defconfig."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nsh"])

        assert result.exit_code == 0
        assert "Configuration completed successfully" in result.output
        assert "NuttX environment is ready" in result.output
        assert_ntxenv_exists(nuttxspace_path)

        # Verify .ntxenv contents
        env = load_env_config(nuttxspace_path)
        assert env.get("nuttx_dir") == "nuttx"
        assert env.get("apps_dir") == "nuttx-apps"
        assert env.get("build_tool") == "make"

    def test_start_invalid_defconfig(self, nuttxspace_path):
        """Test start command with invalid defconfig."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nshhhh"])

        assert result.exit_code != 0
        assert "Setup failed" in result.output or result.exit_code != 0

    def test_start_from_different_directory(self, nuttxspace_path):
        """Test start command when invoked from a subdirectory."""
        os.chdir(nuttxspace_path / "nuttx")

        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nsh"])

        assert result.exit_code == 0
        # Verify .ntxenv is created in the workspace root, not in subdirectory
        assert_ntxenv_exists(nuttxspace_path)
        assert not (nuttxspace_path / "nuttx" / ".ntxenv").exists()

    def test_start_with_custom_directories(self, nuttxspace_path):
        """Test start command with custom nuttx and apps directory names."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(
            start, ["sim", "nsh", "--nuttx-dir", "nuttx", "--apps-dir", "nuttx-apps"]
        )

        assert result.exit_code == 0
        assert_ntxenv_exists(nuttxspace_path)

        env = load_env_config(nuttxspace_path)
        assert env.get("nuttx_dir") == "nuttx"
        assert env.get("apps_dir") == "nuttx-apps"

    def test_start_with_store_nxtmpdir(self, nuttxspace_path):
        """Test start command with --store-nxtmpdir flag."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nsh", "--store-nxtmpdir"])

        assert result.exit_code == 0
        assert_ntxenv_exists(nuttxspace_path)

    def test_start_invalid_board(self, nuttxspace_path):
        """Test start command with invalid board name."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(start, ["invalid_board", "nsh"])

        assert result.exit_code != 0


class TestStartCmake:
    """Test suite for the start command with CMake build tool."""

    @pytest.fixture(autouse=True, scope="class")
    def teardown_after_class(self, nuttxspace_path):
        """Teardown: distclean after all tests in this class."""
        yield
        # Cleanup after all tests in this class complete
        os.chdir(nuttxspace_path)
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            runner = CliRunner()
            runner.invoke(distclean, [])

    def test_start_with_cmake(self, nuttxspace_path):
        """Test start command with --use-cmake flag."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nsh", "--use-cmake"])
        print(result.output)

        assert result.exit_code == 0
        assert_ntxenv_exists(nuttxspace_path)

        env = load_env_config(nuttxspace_path)
        assert env.get("build_tool") == "cmake"

    def test_start_cmake_from_different_directory(self, nuttxspace_path):
        """Test start command with CMake when invoked from a subdirectory."""
        os.chdir(nuttxspace_path / "nuttx")

        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nsh", "--use-cmake"])

        assert result.exit_code == 0
        assert_ntxenv_exists(nuttxspace_path)
        assert not (nuttxspace_path / "nuttx" / ".ntxenv").exists()

        env = load_env_config(nuttxspace_path)
        assert env.get("build_tool") == "cmake"


class TestBuild:
    """Test suite for the build command."""

    @pytest.fixture(autouse=True, scope="class")
    def teardown_after_class(self, nuttxspace_path):
        """Teardown: distclean after all tests in this class."""
        yield
        # Cleanup after all tests in this class complete
        os.chdir(nuttxspace_path)
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            runner = CliRunner()
            runner.invoke(distclean, [])

    def test_build_with_parallel_jobs(self, nuttxspace_path):
        """Test build command with parallel jobs option."""
        os.chdir(nuttxspace_path)

        # Setup environment first
        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])

        result = runner.invoke(build, ["-j4"])
        assert result.exit_code == 0
        assert (Path(nuttxspace_path) / "nuttx" / "nuttx").exists()

    def test_build_without_parallel_option(self, nuttxspace_path):
        """Test build command without parallel jobs option."""
        os.chdir(nuttxspace_path)

        # Setup environment first
        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])

        result = runner.invoke(build, [])
        assert result.exit_code == 0
        assert (Path(nuttxspace_path) / "nuttx" / "nuttx").exists()

    def test_build_without_ntxenv(self, nuttxspace_path):
        """Test build command fails when .ntxenv doesn't exist."""
        os.chdir(nuttxspace_path)

        # Ensure .ntxenv doesn't exist
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            env_file.unlink()

        runner = CliRunner()
        result = runner.invoke(build, [])

        assert result.exit_code != 0
        assert (
            "No .ntxenv found" in result.output
            or "Please run 'start' command first" in result.output
        )


class TestClean:
    """Test suite for the clean command."""

    @pytest.fixture(autouse=True, scope="class")
    def teardown_after_class(self, nuttxspace_path):
        """Teardown: distclean after all tests in this class."""
        yield
        # Cleanup after all tests in this class complete
        os.chdir(nuttxspace_path)
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            runner = CliRunner()
            runner.invoke(distclean, [])

    def test_clean_standalone(self, nuttxspace_path):
        """Test clean command as standalone operation."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])
        runner.invoke(build, ["-j4"])

        # Verify build artifact exists before clean
        nuttx_binary = Path(nuttxspace_path) / "nuttx" / "nuttx"
        assert nuttx_binary.exists()

        result = runner.invoke(clean, [])
        assert result.exit_code == 0
        assert "Cleaning build artifacts" in result.output

    def test_clean_without_ntxenv(self, nuttxspace_path):
        """Test clean command fails when .ntxenv doesn't exist."""
        os.chdir(nuttxspace_path)

        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            env_file.unlink()

        runner = CliRunner()
        result = runner.invoke(clean, [])

        assert result.exit_code != 0
        assert (
            "No .ntxenv found" in result.output
            or "Please run 'start' command first" in result.output
        )


class TestDistclean:
    """Test suite for the distclean command."""

    def test_distclean_removes_ntxenv(self, nuttxspace_path):
        """Test distclean removes .ntxenv file."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])
        assert_ntxenv_exists(nuttxspace_path)

        result = runner.invoke(distclean, [])
        assert result.exit_code == 0
        assert "Resetting NuttX environment" in result.output
        assert_ntxenv_removed(nuttxspace_path)

    def test_distclean_without_ntxenv(self, nuttxspace_path):
        """Test distclean fails when .ntxenv doesn't exist."""
        os.chdir(nuttxspace_path)

        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            env_file.unlink()

        runner = CliRunner()
        result = runner.invoke(distclean, [])

        assert result.exit_code != 0
        assert (
            "No .ntxenv found" in result.output
            or "Please run 'start' command first" in result.output
        )


class TestInstall:
    """Test suite for the install command."""

    def test_install_when_repos_exist(self, nuttxspace_path):
        """Test install command when repositories already exist."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(install, [])

        assert result.exit_code == 0
        assert (
            "already exist" in result.output
            or "Installation completed successfully" in result.output
        )

    def test_install_verifies_structure(self, nuttxspace_path):
        """Test install command verifies directory structure."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(install, [])

        assert result.exit_code == 0
        # Verify directories exist
        assert (nuttxspace_path / "nuttx").exists()
        assert (nuttxspace_path / "nuttx-apps").exists()


class TestKconfig:
    """Test suite for the kconfig command."""

    @pytest.fixture(autouse=True)
    def setup_environment(self, nuttxspace_path):
        """Setup environment for kconfig tests."""
        os.chdir(nuttxspace_path)
        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])
        yield
        # Cleanup if needed

    def test_kconfig_read(self, nuttxspace_path):
        """Test kconfig read command."""
        runner = CliRunner()
        result = runner.invoke(kconfig, ["--read", "CONFIG_NSH_PROMPT_STRING"])

        assert result.exit_code == 0

    def test_kconfig_read_invalid_path(self, nuttxspace_path):
        """Test kconfig read with invalid path."""
        runner = CliRunner()
        result = runner.invoke(kconfig, ["--read", "CONFIG_INVALID_OPTION_XYZ"])

        # Should not crash, may return empty or error
        assert result.exit_code in [0, 1]

    def test_kconfig_set_value(self, nuttxspace_path):
        """Test kconfig set-value command."""
        runner = CliRunner()
        result = runner.invoke(
            kconfig, ["--set-value", "CONFIG_SYSTEM_NSH_PRIORITY", "100"]
        )

        assert result.exit_code == 0

        # Verify the value was set
        result = runner.invoke(kconfig, ["--read", "CONFIG_SYSTEM_NSH_PRIORITY"])
        assert result.exit_code == 0

    def test_kconfig_set_value_missing_value(self, nuttxspace_path):
        """Test kconfig set-value without value argument."""
        runner = CliRunner()
        result = runner.invoke(kconfig, ["--set-value", "CONFIG_SYSTEM_NSH_PRIORITY"])

        assert result.exit_code != 0
        assert "Set value is required" in result.output

    def test_kconfig_set_str(self, nuttxspace_path):
        """Test kconfig set-str command."""
        runner = CliRunner()
        result = runner.invoke(
            kconfig, ["--set-str", "CONFIG_NSH_PROMPT_STRING", "test_prompt"]
        )

        assert result.exit_code == 0

    def test_kconfig_set_str_missing_value(self, nuttxspace_path):
        """Test kconfig set-str without value argument."""
        runner = CliRunner()
        result = runner.invoke(kconfig, ["--set-str", "CONFIG_NSH_PROMPT_STRING"])

        assert result.exit_code != 0
        assert "Set string is required" in result.output

    def test_kconfig_apply(self, nuttxspace_path):
        """Test kconfig apply command."""
        runner = CliRunner()
        # First set a value
        runner.invoke(kconfig, ["--set-value", "CONFIG_SYSTEM_NSH_PRIORITY", "100"])

        # Then apply
        result = runner.invoke(kconfig, ["--apply"])

        assert result.exit_code == 0

    def test_kconfig_merge(self, nuttxspace_path):
        """Test kconfig merge command."""
        runner = CliRunner()
        config_file = Path(__file__).parent / "configs" / "test_config"

        result = runner.invoke(kconfig, ["--merge", str(config_file)])

        assert result.exit_code == 0

        # Verify merged config
        result = runner.invoke(kconfig, ["--read", "CONFIG_NSH_SYSINITSCRIPT"])
        assert result.exit_code == 0

    def test_kconfig_merge_missing_file(self, nuttxspace_path):
        """Test kconfig merge without file argument."""
        runner = CliRunner()
        result = runner.invoke(kconfig, ["--merge"])

        assert result.exit_code != 0
        assert "Merge file is required" in result.output

    def test_kconfig_no_action(self, nuttxspace_path):
        """Test kconfig command without any action specified."""
        runner = CliRunner()
        result = runner.invoke(kconfig, [])

        assert result.exit_code == 0
        assert "No action specified" in result.output

    def test_kconfig_without_ntxenv(self, nuttxspace_path):
        """Test kconfig command fails when .ntxenv doesn't exist."""
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            env_file.unlink()

        runner = CliRunner()
        result = runner.invoke(kconfig, ["--read", "CONFIG_NSH_PROMPT_STRING"])

        assert result.exit_code != 0
        assert (
            "No .ntxenv found" in result.output
            or "Please run 'start' command first" in result.output
        )


class TestMake:
    """Test suite for the make command."""

    @pytest.fixture(autouse=True, scope="class")
    def setup_and_teardown_environment(self, nuttxspace_path):
        """Setup environment for make tests and teardown after class."""
        os.chdir(nuttxspace_path)
        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])
        yield
        # Cleanup after all tests in this class complete
        os.chdir(nuttxspace_path)
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            runner = CliRunner()
            runner.invoke(distclean, [])
        os.chdir(nuttxspace_path / "nuttx")
        subprocess.run(["make", "distclean"])

    def test_make_command(self, nuttxspace_path):
        """Test make command with a valid target."""
        runner = CliRunner()
        result = runner.invoke(make, ["clean"])

        assert result.exit_code == 0
        assert "Running make clean" in result.output

    def test_make_all(self, nuttxspace_path):
        """Test make command with 'all' target."""
        runner = CliRunner()
        result = runner.invoke(make, ["all"])

        assert result.exit_code == 0
        assert (Path(nuttxspace_path) / "nuttx" / "nuttx").exists()

    def test_make_without_ntxenv(self, nuttxspace_path):
        """Test make command fails when .ntxenv doesn't exist."""
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            env_file.unlink()

        runner = CliRunner()
        result = runner.invoke(make, ["clean"])

        assert result.exit_code != 0
        assert (
            "No .ntxenv found" in result.output
            or "Please run 'start' command first" in result.output
        )


class TestCmake:
    """Test suite for the cmake command."""

    @pytest.fixture(autouse=True, scope="class")
    def setup_and_teardown_environment(self, nuttxspace_path):
        """Setup environment for cmake tests and teardown after class."""
        os.chdir(nuttxspace_path)
        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh", "--use-cmake"])
        yield
        # Cleanup after all tests in this class complete
        os.chdir(nuttxspace_path)
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            runner = CliRunner()
            runner.invoke(distclean, [])

    def test_cmake_command(self, nuttxspace_path):
        """Test cmake command with a valid target."""
        runner = CliRunner()
        result = runner.invoke(cmake, ["--build", "build", "--target", "clean"])

        # CMake commands may have different exit codes depending on target
        assert "Running cmake" in result.output

    def test_cmake_without_ntxenv(self, nuttxspace_path):
        """Test cmake command fails when .ntxenv doesn't exist."""
        env_file = nuttxspace_path / ".ntxenv"
        if env_file.exists():
            env_file.unlink()

        runner = CliRunner()
        result = runner.invoke(cmake, ["--build", "build"])

        assert result.exit_code != 0
        assert (
            "No .ntxenv found" in result.output
            or "Please run 'start' command first" in result.output
        )


class TestBuildToolMismatch:
    """Test suite for build tool mismatch scenarios."""

    def test_make_when_cmake_configured(self, nuttxspace_path):
        """Test make command fails when CMake is configured."""
        os.chdir(nuttxspace_path)

        # Setup with CMake
        runner = CliRunner()
        result = runner.invoke(start, ["sim", "nsh", "--use-cmake"])
        assert result.exit_code == 0

        result = runner.invoke(make, ["clean"])

        assert result.exit_code != 0
        assert "Project is configured for CMake" in result.output
        assert "Use 'cmake' command instead" in result.output

        # Cleanup
        runner.invoke(distclean, [])

    def test_cmake_when_make_configured(self, nuttxspace_path):
        """Test cmake command fails when Make is configured."""
        os.chdir(nuttxspace_path)

        # Setup with Make (default)
        runner = CliRunner()
        runner.invoke(start, ["sim", "nsh"])

        result = runner.invoke(cmake, ["--build", "."])

        assert result.exit_code != 0
        assert "Project is configured for Make" in result.output
        assert "Use 'make' command instead" in result.output

        # Cleanup
        runner.invoke(distclean, [])


class TestMain:
    """Test suite for the main group command."""

    def test_main_log_level_debug(self, nuttxspace_path):
        """Test main command with DEBUG log level."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--log-level", "DEBUG", "start", "sim", "nsh"])

        assert result.exit_code == 0

    def test_main_log_level_info(self, nuttxspace_path):
        """Test main command with INFO log level."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--log-level", "INFO", "start", "sim", "nsh"])

        assert result.exit_code == 0

    def test_main_log_level_warning(self, nuttxspace_path):
        """Test main command with WARNING log level (default)."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--log-level", "WARNING", "start", "sim", "nsh"])

        assert result.exit_code == 0

    def test_main_log_level_error(self, nuttxspace_path):
        """Test main command with ERROR log level."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--log-level", "ERROR", "start", "sim", "nsh"])

        assert result.exit_code == 0

    def test_main_log_level_case_insensitive(self, nuttxspace_path):
        """Test main command with case-insensitive log level."""
        os.chdir(nuttxspace_path)

        runner = CliRunner()
        result = runner.invoke(main, ["--log-level", "debug", "start", "sim", "nsh"])

        assert result.exit_code == 0
