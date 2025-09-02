import pytest
from pathlib import Path
from ntxbuild.config import ConfigManager
from ntxbuild.build import NuttXBuilder

CONFIG_BOARD = "sim"
CONFIG_DEFCONFIG = "nsh"
STR_CONFIGS = ["CONFIG_ARCH_CHIP", "CONFIG_BASE_DEFCONFIG", "CONFIG_EXAMPLES_HELLO_PROGNAME"]
# CONFIG_BOARDCTL_SPINLOCK should be "not set"
BOOL_CONFIGS = ["CONFIG_ARCH_BOARD_SIM", "CONFIG_BOARDCTL_SPINLOCK", "CONFIG_EXAMPLES_HELLO"]
NUM_CONFIGS = ["CONFIG_FAT_MAXFNAME", "CONFIG_EXAMPLES_HELLO_PRIORITY"]
HEX_CONFIGS = ["CONFIG_SYSLOG_DEFAULT_MASK", "CONFIG_RAM_START"]

TEST_STR_VALUE = "test_123456"


@pytest.fixture(scope="module", autouse=True)
def setup_board_sim_environment(nuttxspace_path):
    builder = NuttXBuilder()
    nuttx_dir = nuttxspace_path / "nuttx"
    apps_path = nuttxspace_path / "nuttx-apps"

    builder.setup_nuttx(nuttx_dir, apps_path, CONFIG_BOARD, CONFIG_DEFCONFIG)
    yield
    builder.distclean()


@pytest.fixture
def nuttx_path(nuttxspace_path):
    return nuttxspace_path / "nuttx"


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", STR_CONFIGS)
def test_config_read_write_str(config, nuttx_path):
    config_manager = ConfigManager()
    initial_val = config_manager.kconfig_read(config, nuttx_path)
    config_manager.kconfig_set_str(config, TEST_STR_VALUE, nuttx_path)

    new_val = config_manager.kconfig_read(config, nuttx_path)
    assert new_val == TEST_STR_VALUE
    assert new_val != initial_val
