"""
Utility functions for NuttX builds.
"""

import logging
import select
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

NUTTX_DEFAULT_DIR_NAME = "nuttx"
NUTTX_APPS_DEFAULT_DIR_NAME = "nuttx-apps"

# Get logger for this module
logger = logging.getLogger(__name__)


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
    """Run a make command with real-time output using Popen."""
    logger.debug(f"Running make command: {' '.join(cmd)} in cwd={cwd}")

    try:
        # Use Popen for real-time output
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        stdout_lines = []
        stderr_lines = []

        # Read output in real-time
        while True:
            # Check if process has finished
            if process.poll() is not None:
                break

            # Check for available output
            reads, _, _ = select.select([process.stdout, process.stderr], [], [], 0.1)

            for stream in reads:
                if stream == process.stdout:
                    line = stream.readline()
                    if line:
                        line = line.rstrip()
                        stdout_lines.append(line)
                        print(line)  # Print stdout immediately
                elif stream == process.stderr:
                    line = stream.readline()
                    if line:
                        line = line.rstrip()
                        stderr_lines.append(line)
                        print(f"{line}", file=sys.stderr)  # Print stderr immediately

        # Read any remaining output
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            stdout_lines.extend(remaining_stdout.splitlines())
        if remaining_stderr:
            stderr_lines.extend(remaining_stderr.splitlines())

        # Create CompletedProcess-like object
        result = subprocess.CompletedProcess(
            args=cmd,
            returncode=process.returncode,
            stdout="\n".join(stdout_lines),
            stderr="\n".join(stderr_lines),
        )

        if process.returncode != 0:
            logger.error(f"Make command failed with return code: {process.returncode}")

        logger.debug(f"Make command succeeded with return code: {process.returncode}")
        return result.returncode

    except Exception as e:
        logger.error(f"Make command failed: {' '.join(cmd)}, error: {e}")
        return e.returncode


def find_nuttx_root(start_path: Path, nuttx_name: str, apps_name: str) -> Optional[str]:
    """Find the NuttX root directory."""
    logging.debug(
        f"Search NuttX root dir in {start_path} for {nuttx_name} and {apps_name}"
    )
    path = start_path.resolve()

    while path != path.parent:
        if (path / nuttx_name).exists() and (path / apps_name).exists():
            logging.debug(f"NuttX root directory found at {path}")
            return path
        path = path.parent

    raise FileNotFoundError(
        "NuttX workspace not found. "
        "Make sure nuttx and apps directories are present."
    )


def get_build_artifacts(build_dir: str) -> List[str]:
    """Get list of build artifacts."""
    artifacts = []
    build_path = Path(build_dir)

    if build_path.exists():
        for item in build_path.rglob("*"):
            if item.is_file() and item.suffix in [".o", ".a", ".elf", ".bin", ".hex"]:
                artifacts.append(str(item))

    return artifacts
