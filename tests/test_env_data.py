from ntxbuild.env_data import (
    append_to_general_section,
    clear_ntx_env,
    create_base_env_file,
    load_ntx_env,
    remove_from_general_section,
)


def test_save_and_load_ntx_env(nuttxspace_path):
    """Test save and load ntxenv."""
    create_base_env_file(nuttxspace_path, "nuttx", "apps", "make")
    env = load_ntx_env(nuttxspace_path)
    assert env["general"]["nuttxspace_path"] == str(nuttxspace_path)
    assert env["general"]["nuttx_dir"] == "nuttx"
    assert env["general"]["apps_dir"] == "apps"
    assert env["general"]["build_tool"] == "make"
    clear_ntx_env(nuttxspace_path)


def test_append_to_general_section(nuttxspace_path):
    """Test append to general section of ntxenv."""
    env_file = nuttxspace_path / ".ntxenv"
    create_base_env_file(nuttxspace_path, "nuttx", "apps", "make")
    append_to_general_section(env_file, "test_field", "test_value")
    env = load_ntx_env(nuttxspace_path)
    assert env["general"]["test_field"] == "test_value"
    clear_ntx_env(nuttxspace_path)


def test_remove_from_general_section(nuttxspace_path):
    """Test remove from general section of ntxenv."""
    env_file = nuttxspace_path / ".ntxenv"
    create_base_env_file(nuttxspace_path, "nuttx", "apps", "make")
    append_to_general_section(env_file, "test_field", "test_value")
    env = load_ntx_env(nuttxspace_path)
    assert env["general"]["test_field"] == "test_value"
    remove_from_general_section(env_file, "test_field")
    env = load_ntx_env(nuttxspace_path)
    assert "test_field" not in env["general"]
    clear_ntx_env(nuttxspace_path)
