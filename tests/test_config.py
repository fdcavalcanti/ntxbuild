from pathlib import Path

import pytest

from ntxbuild.build import nuttx_builder
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
NUM_CONFIGS = ["CONFIG_FAT_MAXFNAME", "CONFIG_SYSTEM_NSH_PRIORITY"]
HEX_CONFIGS = ["CONFIG_SYSLOG_DEFAULT_MASK", "CONFIG_RAM_START"]

TEST_STR_VALUE = "test_123456"
TEST_NUM_VALUE = 50


@pytest.fixture(scope="module", autouse=True)
def setup_board_sim_environment(nuttxspace_path):
    builder = nuttx_builder(nuttxspace_path)
    builder.distclean()
    builder.initialize(CONFIG_BOARD, CONFIG_DEFCONFIG)
    yield
    builder.distclean()


@pytest.fixture
def nuttx_path(nuttxspace_path):
    return nuttxspace_path / "nuttx"


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", STR_CONFIGS)
def test_config_read_write_str(config, nuttxspace_path):
    config_manager = ConfigManager(nuttxspace_path, "nuttx")
    initial_val = config_manager.kconfig_read(config)
    config_manager.kconfig_set_str(config, TEST_STR_VALUE)
    config_manager.kconfig_apply_changes()
    new_val = config_manager.kconfig_read(config)

    assert new_val == TEST_STR_VALUE
    assert new_val != initial_val


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", BOOL_CONFIGS)
def test_config_read_write_bool(config, nuttxspace_path):
    config_manager = ConfigManager(nuttxspace_path, "nuttx")
    initial_val = config_manager.kconfig_read(config)
    if initial_val == "y":
        config_manager.kconfig_disable(config)
    else:
        config_manager.kconfig_enable(config)
    config_manager.kconfig_apply_changes()
    new_val = config_manager.kconfig_read(config)

    assert new_val != initial_val
    assert new_val in ("y", "n")


@pytest.mark.parametrize("config", NUM_CONFIGS)
def test_config_read_write_num(config, nuttxspace_path):
    config_manager = ConfigManager(nuttxspace_path, "nuttx")
    initial_val = config_manager.kconfig_read(config)
    config_manager.kconfig_set_value(config, str(TEST_NUM_VALUE))
    config_manager.kconfig_apply_changes()
    new_val = config_manager.kconfig_read(config)

    assert new_val == str(TEST_NUM_VALUE)
    assert new_val != initial_val


def test_read_write_invalid_num(nuttxspace_path):
    config_manager = ConfigManager(nuttxspace_path, "nuttx")
    with pytest.raises(ValueError):
        config_manager.kconfig_set_value(NUM_CONFIGS[0], "invalid")


def test_merge_config(nuttxspace_path):
    config_manager = ConfigManager(nuttxspace_path, "nuttx")
    this_file = Path(__file__).resolve()

    config_manager.kconfig_merge_config_file(
        this_file.parent / "configs" / "test_config", None
    )
    config_manager.kconfig_apply_changes()

    value = config_manager.kconfig_read("CONFIG_NSH_SYSINITSCRIPT")
    assert value == "test_value"
    value = config_manager.kconfig_read("CONFIG_SYSTEM_DD")
    assert value == "n"
    value = config_manager.kconfig_read("CONFIG_DEV_GPIO_NSIGNALS")
    assert value == "2"
