from pathlib import Path

import pytest

from ntxbuild.build import BuildTool
from ntxbuild.config import ConfigManager

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

NUTTX_APPS_DIR = "nuttx-apps"


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", STR_CONFIGS)
def test_config_read_write_str(config, config_manager):
    initial_val = config_manager.kconfig_read(config)
    config_manager.kconfig_set_str(config, TEST_STR_VALUE)
    # config_manager.kconfig_apply_changes()
    new_val = config_manager.kconfig_read(config)

    assert new_val == TEST_STR_VALUE
    assert new_val != initial_val


@pytest.mark.usefixtures("setup_board_sim_environment")
@pytest.mark.parametrize("config", BOOL_CONFIGS)
def test_config_read_write_bool(config, config_manager):
    initial_val = config_manager.kconfig_read(config)
    if initial_val == "y":
        config_manager.kconfig_disable(config)
    else:
        config_manager.kconfig_enable(config)
    # config_manager.kconfig_apply_changes()
    new_val = config_manager.kconfig_read(config)

    assert new_val != initial_val
    assert new_val in ("y", "n")


@pytest.mark.parametrize("config", NUM_CONFIGS)
def test_config_read_write_num(config, config_manager):
    initial_val = config_manager.kconfig_read(config)
    config_manager.kconfig_set_value(config, str(TEST_NUM_VALUE))
    # config_manager.kconfig_apply_changes()
    new_val = config_manager.kconfig_read(config)

    assert new_val == str(TEST_NUM_VALUE)
    assert new_val != initial_val


def test_read_write_invalid_num(config_manager):
    with pytest.raises(ValueError):
        config_manager.kconfig_set_value(NUM_CONFIGS[0], "invalid")


def test_merge_config(nuttxspace_path, config_manager):
    this_file = Path(__file__).resolve()

    config_file = this_file.parent / "configs" / "test_config"

    value_before_nsh = config_manager.kconfig_read("CONFIG_NSH_SYSINITSCRIPT")
    value_before_dd = config_manager.kconfig_read("CONFIG_SYSTEM_DD")
    value_before_gpio = config_manager.kconfig_read("CONFIG_DEV_GPIO_NSIGNALS")

    assert config_file.exists()
    config_manager.kconfig_merge_config_file(config_file)
    # config_manager.kconfig_apply_changes()

    new_config_manager = ConfigManager(
        nuttxspace_path, NUTTX_APPS_DIR, build_tool=BuildTool.CMAKE
    )

    value = new_config_manager.kconfig_read("CONFIG_NSH_SYSINITSCRIPT")
    assert value == "test_value" and value != value_before_nsh
    value = new_config_manager.kconfig_read("CONFIG_SYSTEM_DD")
    assert value == "n" and value != value_before_dd
    value = new_config_manager.kconfig_read("CONFIG_DEV_GPIO_NSIGNALS")
    assert value == "2" and value != value_before_gpio


# Exception tests
def test_config_manager_file_not_found_error(nuttxspace_path):
    """Test FileNotFoundError when apps_path doesn't exist."""
    with pytest.raises(FileNotFoundError, match="Apps path not found at"):
        ConfigManager(nuttxspace_path, "nonexistent_apps", build_tool=BuildTool.CMAKE)


def test_config_manager_runtime_error_no_config(tmp_path):
    """Test RuntimeError when .config file doesn't exist."""
    # Create a temporary nuttx directory without .config
    temp_nuttx = tmp_path / "nuttx"
    temp_nuttx.mkdir()
    (temp_nuttx / "Kconfig").touch()
    (temp_nuttx / "build").mkdir()

    # Create a dummy apps directory
    temp_apps = tmp_path / "nuttx-apps"
    temp_apps.mkdir()

    with pytest.raises(RuntimeError, match=".config file not found"):
        ConfigManager(tmp_path, NUTTX_APPS_DIR, build_tool=BuildTool.CMAKE)


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_read_key_error(config_manager):
    """Test KeyError when reading non-existent config option."""
    with pytest.raises(KeyError, match="Kconfig option 'NONEXISTENT_CONFIG' not found"):
        config_manager.kconfig_read("CONFIG_NONEXISTENT_CONFIG")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_enable_key_error(config_manager):
    """Test KeyError when enabling non-existent config option."""
    with pytest.raises(KeyError, match="Kconfig option 'NONEXISTENT_CONFIG' not found"):
        config_manager.kconfig_enable("CONFIG_NONEXISTENT_CONFIG")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_disable_key_error(config_manager):
    """Test KeyError when disabling non-existent config option."""
    with pytest.raises(KeyError, match="Kconfig option 'NONEXISTENT_CONFIG' not found"):
        config_manager.kconfig_disable("CONFIG_NONEXISTENT_CONFIG")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_key_error(config_manager):
    """Test KeyError when setting value for non-existent config option."""
    with pytest.raises(KeyError, match="Kconfig option 'NONEXISTENT_CONFIG' not found"):
        config_manager.kconfig_set_value("CONFIG_NONEXISTENT_CONFIG", "123")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_str_key_error(nuttxspace_path, config_manager):
    """Test KeyError when setting string for non-existent config option."""
    with pytest.raises(KeyError, match="Kconfig option 'NONEXISTENT_CONFIG' not found"):
        config_manager.kconfig_set_str("CONFIG_NONEXISTENT_CONFIG", "test_value")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_non_string(config_manager):
    """Test ValueError when setting value with non-string input."""
    with pytest.raises(AssertionError):
        config_manager.kconfig_set_value(NUM_CONFIGS[0], 123)


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_invalid_int(config_manager):
    """Test ValueError when setting value with invalid integer."""
    with pytest.raises(ValueError, match="Set value must be string representation"):
        config_manager.kconfig_set_value(NUM_CONFIGS[0], "not_a_number")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_wrong_type(config_manager):
    """Test ValueError when setting value on non-INT/HEX config option."""
    # Try to set a value on a STRING config
    if config_manager.build_tool == BuildTool.CMAKE:
        pytest.skip("No support on CMake build tool")
    with pytest.raises(ValueError, match="requires a numerical or hexadecimal input"):
        config_manager.kconfig_set_value(STR_CONFIGS[0], "123")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_assignable_symbol(config_manager):
    """Test ValueError when setting value on assignable symbol.

    Note: This test uses a BOOL config which will fail at type check,
    not at assignable check. Testing assignable check for INT/HEX would
    require finding a specific assignable INT/HEX symbol which is fragile.
    """
    if config_manager.build_tool == BuildTool.CMAKE:
        pytest.skip(
            "CMake build tool does not support setting value on assignable symbol"
        )
    # Try to set a value on a BOOL config (which is assignable)
    # This will fail at type check since BOOL is not INT/HEX
    with pytest.raises(ValueError, match="requires a numerical or hexadecimal input"):
        config_manager.kconfig_set_value(BOOL_CONFIGS[0], "1")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_int_with_hex(config_manager):
    """Test ValueError when setting INT config with hexadecimal value."""
    if config_manager.build_tool == BuildTool.CMAKE:
        pytest.skip("No support on CMake build tool")
    with pytest.raises(ValueError, match="requires a int input, not hexadecimal"):
        config_manager.kconfig_set_value(NUM_CONFIGS[0], "0x10")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_value_hex_without_prefix(config_manager):
    """Test ValueError when setting HEX config without 0x prefix."""
    if config_manager.build_tool == BuildTool.CMAKE:
        pytest.skip(
            "CMake build tool does not support setting HEX config without 0x prefix"
        )
    with pytest.raises(ValueError, match="requires a hexadecimal input"):
        config_manager.kconfig_set_value(HEX_CONFIGS[0], "10")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_set_str_wrong_type(config_manager):
    """Test ValueError when setting string on non-STRING config option."""
    if config_manager.build_tool == BuildTool.CMAKE:
        pytest.skip("No support on CMake build tool")
    # Try to set a string on a BOOL config
    with pytest.raises(ValueError, match="requires a string input"):
        config_manager.kconfig_set_str(BOOL_CONFIGS[0], "test_value")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_merge_config_file_empty_source(config_manager):
    """Test ValueError when merging config with empty source file."""
    with pytest.raises(ValueError, match="Source file is required"):
        config_manager.kconfig_merge_config_file("")


@pytest.mark.usefixtures("setup_board_sim_environment")
def test_kconfig_merge_config_file_none_source(config_manager):
    """Test ValueError when merging config with None source file."""
    with pytest.raises(ValueError, match="Source file is required"):
        config_manager.kconfig_merge_config_file(None)
