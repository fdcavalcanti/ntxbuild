"""
Utility functions for NuttX builds.
"""

import logging
import select
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional

NUTTX_DEFAULT_DIR_NAME = "nuttx"
NUTTX_APPS_DEFAULT_DIR_NAME = "nuttx-apps"

# Get logger for this module
logger = logging.getLogger("ntxbuild.utils")


def run_bash_script(
    script_path: str,
    args: List[str] = None,
    cwd: Optional[str] = None,
    no_stdout: bool = False,
    no_stderr: bool = False,
) -> int:
    """Run a bash script using subprocess.call and return exit code."""
    try:
        cmd = [script_path]
        if args:
            cmd.extend(args)

        cmd_str = " ".join(cmd)
        logger.debug(f"Running bash script: {cmd_str} in cwd={cwd}")
        result = subprocess.call(
            cmd_str,
            cwd=cwd,
            shell=True,
            stdout=subprocess.DEVNULL if no_stdout else None,
            stderr=subprocess.DEVNULL if no_stderr else None,
        )
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
    cmd: List[str],
    cwd: Optional[str] = None,
    no_stdout: bool = False,
    no_stderr: bool = False,
) -> subprocess.CompletedProcess:
    """Run a make command with real-time output using Popen."""
    logger.debug(f"Running make command: {' '.join(cmd)} in cwd={cwd}")

    try:
        # Use Popen for real-time output and binary mode to
        # preserve control characters
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE if not no_stdout else subprocess.DEVNULL,
            stderr=subprocess.PIPE if not no_stderr else subprocess.DEVNULL,
            text=False,  # Use binary mode
            bufsize=0,  # No buffering
        )

        if no_stdout and no_stderr:
            process.wait()
            return process.returncode

        # Build list of readable streams (only include pipes, not DEVNULL)
        readable_streams = []
        if not no_stdout:
            readable_streams.append(process.stdout)
        if not no_stderr:
            readable_streams.append(process.stderr)

        # Read output in real-time
        while True:
            # Check if process has finished
            if process.poll() is not None:
                break

            # Check for available output (only if we have valid streams)
            if readable_streams:
                reads, _, _ = select.select(readable_streams, [], [], 0.1)
            else:
                # No streams to read, just wait a bit
                time.sleep(0.1)
                continue

            for stream in reads:
                if stream == process.stdout:
                    chunk = stream.read(1024)  # Read in chunks
                    if chunk:
                        # Decode and print immediately, preserving control characters
                        text = chunk.decode("utf-8", errors="replace")
                        print(text, end="", flush=True)

                elif stream == process.stderr:
                    chunk = stream.read(1024)  # Read in chunks
                    if chunk:
                        # Decode and print immediately, preserving control characters
                        text = chunk.decode("utf-8", errors="replace")
                        print(text, end="", file=sys.stderr, flush=True)

        # Read any remaining output and print it
        remaining_stdout, remaining_stderr = process.communicate()
        if remaining_stdout:
            print(
                remaining_stdout.decode("utf-8", errors="replace"), end="", flush=True
            )
        if remaining_stderr:
            print(
                remaining_stderr.decode("utf-8", errors="replace"),
                end="",
                file=sys.stderr,
                flush=True,
            )

        if process.returncode != 0:
            logger.error(f"Make command failed with return code: {process.returncode}")

        logger.debug(f"Make command succeeded with return code: {process.returncode}")
        return process.returncode

    except Exception as e:
        logger.error(f"Make command failed: {' '.join(cmd)}, error: {e}")
        return e.returncode


def run_curses_command(cmd: List[str], cwd: Optional[str] = None) -> int:
    """Run a curses-based program with proper terminal handling.

    This function is designed for interactive curses programs like menuconfig,
    vim, nano, etc. that require a proper terminal interface.

    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory for the command

    Returns:
        Exit code of the command
    """
    logger.debug(f"Running curses command: {' '.join(cmd)} in cwd={cwd}")

    try:
        # For curses programs, we need to run them directly without pipes
        # to preserve the terminal interface
        process = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,  # Don't raise exception on non-zero exit codes
        )

        logger.debug(f"Curses command completed with return code: {process.returncode}")
        return process.returncode

    except Exception as e:
        logger.error(f"Curses command failed: {' '.join(cmd)}, error: {e}")
        return 1


def find_nuttx_root(start_path: Path, nuttx_name: str, apps_name: str) -> Optional[str]:
    """Find the NuttX root directory."""
    logger.debug(
        f"Search NuttX root dir in {start_path} for {nuttx_name} and {apps_name}"
    )
    path = start_path.resolve()

    while path != path.parent:
        if (path / nuttx_name).exists() and (path / apps_name).exists():
            logger.debug(f"NuttX root directory found at {path}")
            return path
        path = path.parent

    raise FileNotFoundError(
        "NuttX workspace not found. "
        "Make sure nuttx and apps directories are present or call "
        "'ntxbuild install' to download."
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


def copy_nuttxspace_to_tmp(
    nuttxspace_path: str, num_copies: int, target_dir: str = "/tmp"
) -> List[str]:
    """Copy nuttxspace to target directory for parallel builds, excluding
    unnecessary files.

    Args:
        nuttxspace_path: Path to the original nuttxspace directory
        num_copies: Number of copies to create
        target_dir: Target directory for copies (default: /tmp)

    Returns:
        List of paths to the copied directories in target directory
    """
    logger.debug(
        f"Copying nuttxspace {nuttxspace_path} to {target_dir} for {num_copies} "
        "parallel builds"
    )

    source_path = Path(nuttxspace_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Nuttxspace directory not found: {nuttxspace_path}")

    # Ensure target directory exists
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    # Define patterns to exclude for lightweight copies
    exclude_patterns = {
        ".git",
        ".gitattributes",
        ".github",
        ".vscode",
    }

    def ignore_patterns(dir_path, names):
        """Filter function to exclude unnecessary files and directories."""
        ignored = []
        for name in names:
            # Check if name matches any exclude pattern
            if name in exclude_patterns:
                ignored.append(name)
            # Check for patterns with wildcards
            elif any(
                name.endswith(pattern[1:])
                for pattern in exclude_patterns
                if pattern.startswith("*")
            ):
                ignored.append(name)
            # Check for hidden files (except .ntxenv which we might need)
            elif name.startswith(".") and name not in {".ntxenv", ".config"}:
                ignored.append(name)
        return ignored

    copied_paths = []

    try:
        for i in range(num_copies):
            # Create unique temporary directory name
            temp_dir = tempfile.mkdtemp(prefix=f"nuttxspace_{i}_", dir=target_dir)
            temp_path = Path(temp_dir)

            logger.debug(f"Copying to: {temp_path}")

            # Copy the nuttxspace directory with exclusions
            shutil.copytree(
                source_path,
                temp_path,
                ignore=ignore_patterns,
                dirs_exist_ok=True,
                symlinks=True,
            )

            copied_paths.append(str(temp_path))

        logger.info(
            f"Successfully created {num_copies} lightweight copies in {target_dir}"
        )
        return copied_paths

    except Exception as e:
        logger.error(f"Failed to copy nuttxspace: {e}")
        # Clean up any partially created copies
        for path in copied_paths:
            try:
                shutil.rmtree(path)
            except Exception:
                pass
        raise


def cleanup_tmp_copies(copied_paths: List[str]) -> None:
    """Clean up temporary copies of nuttxspace.

    Args:
        copied_paths: List of paths to temporary directories to remove
    """
    logger.debug(f"Cleaning up {len(copied_paths)} temporary copies")

    for path in copied_paths:
        try:
            if Path(path).exists():
                shutil.rmtree(path)
                logger.debug(f"Removed temporary copy: {path}")
        except Exception as e:
            logger.warning(f"Failed to remove temporary copy {path}: {e}")
