import configparser
import logging
import os
from pathlib import Path

# Get logger for this module
logger = logging.getLogger("ntxbuild.env_data")


def save_ntx_env(
    nuttxspace_path: Path, nuttx_dir: str, apps_dir: str, build_tool: str = "make"
) -> None:
    """Save environment configuration to an INI file.

    Args:
        nuttxspace_path: Path to the NuttX workspace directory.
        nuttx_dir: Name of the NuttX OS directory.
        apps_dir: Name of the NuttX apps directory.
        build_tool: Build tool name (default: 'make').
    """
    env_file = nuttxspace_path / ".ntxenv"
    config = configparser.ConfigParser()
    config["general"] = {
        "nuttxspace_path": str(nuttxspace_path),
        "nuttx_dir": nuttx_dir,
        "apps_dir": apps_dir,
        "build_tool": build_tool,
    }

    try:
        with env_file.open("w", encoding="utf-8") as f:
            config.write(f)
    except Exception:
        logger.exception("Failed to write environment file: %s", env_file)


def load_ntx_env(nuttxspace_path: Path) -> configparser.ConfigParser:
    """Load environment configuration from the INI file and return a dict.

    Args:
        nuttxspace_path: Path to the NuttX workspace directory.

    Returns a dictionary with keys:
      - 'nuttxspace_path' (Path)
      - 'nuttx_dir' (str)
      - 'apps_dir' (str)
      - 'build_tool' (str)

    Returns None if the file is missing or invalid.
    """
    # Change into the nuttxspace directory
    os.chdir(nuttxspace_path)

    env_file = nuttxspace_path / ".ntxenv"
    if not env_file.exists():
        raise FileNotFoundError(f"Environment file does not exist: {env_file}")

    config = configparser.ConfigParser()
    try:
        config.read(env_file, encoding="utf-8")
    except Exception:
        raise RuntimeError(f"Failed to read environment file: {env_file}")

    if "general" not in config:
        raise RuntimeError(f"Missing 'general' section in environment file: {env_file}")

    section = config["general"]

    nuttxspace = section.get("nuttxspace_path")
    nuttx_dir = section.get("nuttx_dir")
    apps_dir = section.get("apps_dir")

    if not (nuttxspace and nuttx_dir and apps_dir):
        raise RuntimeError(f"Missing required sections in environment file: {env_file}")

    return config


def clear_ntx_env(nuttxspace_path: Path) -> None:
    """Remove the environment INI file if it exists."""
    env_file = Path(nuttxspace_path) / ".ntxenv"
    logger.debug("Clearing NuttX environment configuration file: %s", env_file)
    try:
        if env_file.exists():
            env_file.unlink()
    except Exception:
        logger.exception("Failed to remove environment file: %s", env_file)
