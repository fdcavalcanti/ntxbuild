import pytest

from ntxbuild.build import NuttXBuilder
from ntxbuild.config import ConfigManager

CONFIG_BOARD = "sim"
CONFIG_DEFCONFIG = "nsh"
STR_CONFIGS = [
    "CONFIG_NSH_PROMPT_STRING",
    "CONFIG_BASE_DEFCONFIG",
    "CONFIG_EXAMPLES_HELLO_PROGNAME",
]
# CONFIG_BOARDCTL_SPINLOCK should be "not set"
BOOL_CONFIGS = [
    "CONFIG_EXAMPLES_GPIO",
    "CONFIG_BOARDCTL_SPINLOCK",
    "CONFIG_EXAMPLES_HELLO",
]
NUM_CONFIGS = ["CONFIG_FAT_MAXFNAME", "CONFIG_EXAMPLES_HELLO_PRIORITY"]
HEX_CONFIGS = ["CONFIG_SYSLOG_DEFAULT_MASK", "CONFIG_RAM_START"]

TEST_STR_VALUE = "test_123456"


@pytest.fixture(scope="module", autouse=True)
def setup_board_sim_environment(nuttxspace_path):
    builder = NuttXBuilder(nuttxspace_path)
    builder.distclean()
    builder.setup_nuttx(CONFIG_BOARD, CONFIG_DEFCONFIG)
    yield
    builder.distclean()


@pytest.fixture
def nuttx_path(nuttxspace_path):
    return nuttxspace_path / "nuttx"


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", STR_CONFIGS)
def test_config_read_write_str(config, nuttxspace_path, nuttx_path):
    config_manager = ConfigManager(nuttxspace_path)
    initial_val = config_manager.kconfig_read(config, nuttx_path)
    config_manager.kconfig_set_str(config, TEST_STR_VALUE, nuttx_path)
    config_manager.kconfig_apply_changes(nuttx_path)
    new_val = config_manager.kconfig_read(config, nuttx_path)

    initial_val_str = initial_val.stdout.strip()
    new_val_str = new_val.stdout.strip()

    assert new_val_str == TEST_STR_VALUE
    assert new_val_str != initial_val_str


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", BOOL_CONFIGS)
def test_config_read_write_bool(config, nuttxspace_path, nuttx_path):
    config_manager = ConfigManager(nuttxspace_path)
    initial_val = config_manager.kconfig_read(config, nuttx_path)
    init_val_str = initial_val.stdout.strip()
    if init_val_str == "y":
        config_manager.kconfig_disable(config)
    else:
        config_manager.kconfig_enable(config)
    config_manager.kconfig_apply_changes(nuttx_path)
    new_val = config_manager.kconfig_read(config, nuttx_path)
    new_val_str = new_val.stdout.strip()

    assert new_val != initial_val
    assert new_val_str in ("y", "n")
