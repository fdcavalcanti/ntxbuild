"""
Test the build module functionality.
"""

import logging
import subprocess

import pytest

from ntxbuild.build import NuttXBuilder

CONFIG_BOARD = "sim"
CONFIG_DEFCONFIG = "nsh"
NUTTX_BIN = "nuttx"
PARALLEL_NPROCS = 4


@pytest.fixture(scope="module", autouse=True)
def builder(nuttxspace_path):
    builder = NuttXBuilder(nuttxspace_path)
    yield builder
    builder.distclean()


def test_builder_initialization(builder):
    """Test that NuttXBuilder initializes properly."""
    assert builder is not None
    assert hasattr(builder, "nuttxspace_path")
    assert hasattr(builder, "nuttx_path")
    assert hasattr(builder, "apps_path")


def test_builder_methods(builder):
    """Test that builder methods exist and are callable."""

    # Test that methods exist
    assert hasattr(builder, "build")
    assert hasattr(builder, "clean")
    assert hasattr(builder, "distclean")
    assert hasattr(builder, "validate_nuttx_environment")
    assert hasattr(builder, "setup_nuttx")

    # Test that methods are callable
    assert callable(builder.build)
    assert callable(builder.clean)
    assert callable(builder.distclean)


def test_environment_validation(builder):
    """Test that environment validation works with the test workspace."""

    # Test validation
    is_valid, error_msg = builder.validate_nuttx_environment()

    # Should be valid since we have the test workspace
    assert is_valid is True
    assert error_msg == ""


def test_setup_nuttx(builder):
    """Test that setup_nuttx works with the test workspace."""
    subprocess.run(
        ["git", "clean", "-xfd"],
        cwd=builder.nuttx_path,
        check=True,
        capture_output=True,
        text=True,
    )
    builder.distclean()
    ans = builder.setup_nuttx(CONFIG_BOARD, CONFIG_DEFCONFIG)
    assert ans == 0


def test_build_sim(builder):
    """Test that build works with the test workspace."""
    ans = builder.build(PARALLEL_NPROCS)
    assert ans.returncode == 0


def test_build_success(builder):
    """Test that nuttx.bin exists in the nuttx directory after
    build (recursive search).
    """
    files = subprocess.run(
        ["git", "clean", "-xfdn"],
        cwd=builder.nuttx_path,
        check=True,
        capture_output=True,
        text=True,
    )
    files = files.stdout.split()
    assert isinstance(files, list)
    assert "nuttx" in files
    assert "nuttx.map" in files
    assert "include/nuttx/config.h" in files
    assert "boards/Make.dep" in files
    assert "boards/libboards.a" in files
    assert "boards/boardctl.o" in files


def test_clean(builder):
    """Test that clean works with the test workspace."""
    builder.clean()
    files = subprocess.run(
        ["git", "clean", "-xfdn"],
        cwd=builder.nuttx_path,
        check=True,
        capture_output=True,
        text=True,
    )
    files = files.stdout.split()

    assert isinstance(files, list)
    assert "include/nuttx/config.h" in files
    assert "boards/Make.dep" in files
    assert "nuttx" not in files
    assert "nuttx.map" not in files
    assert "boards/libboards.a" not in files
    assert "boards/boardctl.o" not in files


def test_distclean(builder):
    """Test that distclean works with the test workspace."""
    builder.distclean()
    files = subprocess.run(
        ["git", "clean", "-xfdn"],
        cwd=builder.nuttx_path,
        check=True,
        capture_output=True,
        text=True,
    )
    files = files.stdout.split()

    assert isinstance(files, list)
    assert "include/nuttx/config.h" not in files
    assert "boards/Make.dep" not in files
    assert "nuttx" not in files
    assert "nuttx.map" not in files
    assert "boards/libboards.a" not in files
    assert "boards/boardctl.o" not in files
    assert len(files) < 5


def test_logging_is_configured():
    """Test that logging is properly configured."""
    # Check that the root logger has handlers
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0

    # Check that our module logger exists
    module_logger = logging.getLogger("ntxbuild.build")
    assert module_logger is not None

    # Check that logging level is set to DEBUG
    assert module_logger.level <= logging.DEBUG
