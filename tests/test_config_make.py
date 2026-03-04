import pytest

from ntxbuild.build import nuttx_builder
from ntxbuild.config import BuildTool, ConfigManager

NUTTX_APPS_DIR = "nuttx-apps"
CONFIG_DEFCONFIG = "nsh"
CONFIG_BOARD = "sim"


@pytest.fixture(scope="module", autouse=True)
def setup_board_sim_environment(nuttxspace_path):
    builder = nuttx_builder(nuttxspace_path)
    builder.distclean()
    builder.initialize(CONFIG_BOARD, CONFIG_DEFCONFIG)
    yield
    builder.distclean()


@pytest.fixture
def config_manager(nuttxspace_path):
    return ConfigManager(nuttxspace_path, NUTTX_APPS_DIR, build_tool=BuildTool.MAKE)


# Import tests - they will use fixtures defined in this module
from _test_config import *  # noqa: F401,F403,E402
