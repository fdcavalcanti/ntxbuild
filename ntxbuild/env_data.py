import logging
import shelve
from pathlib import Path
from typing import Optional, Tuple

# Get logger for this module
logger = logging.getLogger("ntxbuild.env_data")


def get_env_file_path() -> Path:
    """Get the path to the .ntxenv file in the current or target directory."""
    return Path.cwd() / ".ntxenv"


def save_ntx_env(nuttxspace_folder: str, nuttx_folder: str, apps_folder: str) -> None:
    """Save NuttX environment configuration to .ntxenv file.

    Args:
        nuttx_folder: Name of the NuttX folder
        apps_folder: Name of the apps folder
    """
    env_file = get_env_file_path()

    with shelve.open(str(env_file)) as db:
        db["nuttx_folder"] = nuttx_folder
        db["apps_folder"] = apps_folder
        db["nuttxspace_folder"] = nuttxspace_folder


def load_ntx_env() -> Optional[Tuple[str, str, str]]:
    """Load NuttX environment configuration from .ntxenv file.

    Returns:
        Tuple of (nuttx_folder, apps_folder) if found, None otherwise
    """
    env_file = get_env_file_path()

    if not env_file.exists():
        return None

    try:
        with shelve.open(str(env_file)) as db:
            nuttx_folder = db.get("nuttx_folder")
            apps_folder = db.get("apps_folder")
            nuttxspace_folder = db.get("nuttxspace_folder")

            if nuttx_folder and apps_folder and nuttxspace_folder:
                return nuttxspace_folder, nuttx_folder, apps_folder
            return None
    except Exception:
        return None


def clear_ntx_env() -> None:
    """Clear the NuttX environment configuration file."""
    env_file = get_env_file_path()
    logger.debug(f"Clearing NuttX environment configuration file: {env_file}")
    if env_file.exists():
        try:
            env_file.unlink()
        except Exception:
            pass


def has_ntx_env() -> bool:
    """Check if .ntxenv file exists and contains valid configuration.

    Returns:
        True if valid configuration exists, False otherwise
    """
    return load_ntx_env() is not None
