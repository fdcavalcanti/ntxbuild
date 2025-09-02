"""
Utility functions for NuttX builds.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Get logger for this module
logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None
) -> subprocess.CompletedProcess:
    """Run a shell command and return CompletedProcess object."""
    logger.debug(f"Running command: {' '.join(cmd)} in cwd={cwd}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, env=env, check=True, capture_output=True, text=True
        )
        logger.debug(f"Command succeeded with return code: {result.returncode}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}, error: {e}")
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e}")
        raise


def run_command_simple(
    cmd: List[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None
) -> int:
    """Run a shell command and return exit code only."""
    try:
        result = run_command(cmd, cwd, env)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode


def run_bash_script(
    script_path: str, args: List[str] = None, cwd: Optional[str] = None
) -> int:
    """Run a bash script using subprocess.call and return exit code."""
    try:
        cmd = [script_path]
        if args:
            cmd.extend(args)

        cmd_str = " ".join(cmd)
        logger.debug(f"Running bash script: {cmd_str} in cwd={cwd}")
        result = subprocess.call(cmd_str, cwd=cwd, shell=True)
        logger.debug(f"Bash script result: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to run bash script {script_path}: {e}", exc_info=True)
        print(f"Failed to run bash script {script_path}: {e}")
        return 1


def run_kconfig_command(
    cmd: List[str], cwd: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Run a kconfig-tweak command and return CompletedProcess object."""
    logger.debug(f"Running kconfig command: {' '.join(cmd)} in cwd={cwd}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True
        )
        logger.debug(f"Kconfig command succeeded with return code: {result.returncode}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Kconfig command failed: {' '.join(cmd)}, error: {e}")
        print(f"Kconfig command failed: {' '.join(cmd)}")
        print(f"Error: {e}")
        raise


def run_make_command(
    cmd: List[str], cwd: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Run a make command and return CompletedProcess object."""
    logger.debug(f"Running make command: {' '.join(cmd)} in cwd={cwd}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, check=True, capture_output=True, text=True
        )
        logger.debug(f"Make command succeeded with return code: {result.returncode}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Make command failed: {' '.join(cmd)}, error: {e}")
        print(f"Make command failed: {' '.join(cmd)}")
        print(f"Error: {e}")
        raise


def find_nuttx_root(start_path: str = ".") -> Optional[str]:
    """Find the NuttX root directory."""
    path = Path(start_path).resolve()

    while path != path.parent:
        if (path / "nuttx").exists() and (path / "apps").exists():
            return str(path)
        path = path.parent

    return None


def get_build_artifacts(build_dir: str) -> List[str]:
    """Get list of build artifacts."""
    artifacts = []
    build_path = Path(build_dir)

    if build_path.exists():
        for item in build_path.rglob("*"):
            if item.is_file() and item.suffix in [".o", ".a", ".elf", ".bin", ".hex"]:
                artifacts.append(str(item))

    return artifacts
