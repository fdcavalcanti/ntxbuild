"""
Utility functions for NuttX builds.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional


def run_command(
    cmd: List[str], cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None
) -> int:
    """Run a shell command and return exit code."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, env=env, check=True, capture_output=True, text=True
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e}")
        return e.returncode


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
