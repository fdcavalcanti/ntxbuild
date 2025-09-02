"""
Configuration management for NuttX builds.
"""

import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Dict

import yaml


class KconfigTweakAction(str, Enum):
    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)

    ENABLE = "--enable"
    DISABLE = "--disable"
    MODULE = "--module"
    SET_STR = "--set-str"
    SET_VAL = "--set-val"
    UNDEFINE = "--undefine"
    STATE = "--state"
    ENABLE_AFTER = "--enable-after"
    DISABLE_AFTER = "--disable-after"
    MODULE_AFTER = "--module-after"
    FILE = "--file"
    KEEP_CASE = "--keep-case"


class ConfigManager:
    """Manages NuttX build configurations."""

    def __init__(self):
        self.config = {}

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(path, "r") as f:
            self.config = yaml.safe_load(f)

        return self.config

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def validate_config(self) -> bool:
        """Validate configuration."""
        # TODO: Implement configuration validation
        return True

    def kconfig_read(self, config: str, nuttx_dir: Path):
        """Read Kconfig file. Returns the value read from the .config file."""
        try:
            result = subprocess.run(
                ["kconfig-tweak", KconfigTweakAction.STATE, config],
                cwd=nuttx_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            value = result.stdout.strip()
            print(f"{config}={value}")
            if result.returncode != 0:
                raise ValueError(f"Kconfig read failed: {result.stderr.strip()}")
            return value
        except subprocess.CalledProcessError as e:
            print(f"Kconfig read failed: {e}")
            return e.returncode

    def kconfig_apply_changes(self, nuttx_dir: Path):
        """Show all Kconfig options"""
        try:
            result = subprocess.run(
                ["make", "olddefconfig"],
                cwd=nuttx_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.returncode
        except subprocess.CalledProcessError as e:
            print(f"Kconfig apply changes failed: {e}")
            return e.returncode

    def kconfig_set_value(self, config: str, value: str, nuttx_dir: Path):
        """Set Kconfig value"""
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Value must be numerical")

        try:
            result = subprocess.run(
                ["kconfig-tweak", KconfigTweakAction.SET_VAL, config, str(value)],
                cwd=nuttx_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.returncode
        except subprocess.CalledProcessError as e:
            print(f"Kconfig set value failed: {e}")
            return e.returncode

    def kconfig_set_str(self, config: str, value: str, nuttx_dir: Path):
        """Set Kconfig string"""
        try:
            result = subprocess.run(
                ["kconfig-tweak", KconfigTweakAction.SET_STR, config, value],
                cwd=nuttx_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.returncode
        except subprocess.CalledProcessError as e:
            print(f"Kconfig set string failed: {e}")
            return e.returncode
