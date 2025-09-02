"""
Pytest configuration and fixtures for ntxbuild tests.
"""

import logging
import shutil
from pathlib import Path

import pytest
from git import Repo


@pytest.fixture(scope="session", autouse=True)
def nuttxspace():
    """
    Session fixture that creates a temporary workspace with NuttX repositories.

    Creates a 'nuttxspace' folder under tests/ and clones:
    - apache/nuttx (light clone)
    - apache/nuttx-apps (light clone)

    Yields the path to the workspace.
    Automatically cleans up the workspace after all tests complete.
    """
    # Create the temporary workspace
    logging.info("Creating NuttX workspace for tests")
    workspace = Path(__file__).parent / "nuttxspace"
    workspace.mkdir(exist_ok=True)

    # Check if workspace already exists
    if workspace.exists():
        logging.info(
            f"NuttX workspace already exists at {workspace}, "
            "skipping clone and cleanup."
        )
        yield workspace
        return

    try:
        # Clone NuttX repository (light clone)
        nuttx_dir = workspace / "nuttx"
        logging.info(f"Cloning apache/nuttx to {nuttx_dir}")
        Repo.clone_from(
            "https://github.com/apache/nuttx.git",
            nuttx_dir,
            depth=1,  # Light clone - only latest commit
            single_branch=True,  # Only main branch
            branch="master",
        )

        # Clone NuttX apps repository (light clone)
        apps_dir = workspace / "nuttx-apps"
        logging.info(f"Cloning apache/nuttx-apps to {apps_dir}")
        Repo.clone_from(
            "https://github.com/apache/nuttx-apps.git",
            apps_dir,
            depth=1,  # Light clone - only latest commit
            single_branch=True,  # Only main branch
            branch="master",
        )

        logging.info(f"✅ NuttX workspace created at {workspace}")
        yield workspace

    finally:
        # Cleanup: remove the entire workspace
        if workspace.exists():
            logging.info(f"🧹 Cleaning up NuttX workspace at {workspace}")
            shutil.rmtree(workspace)
            logging.info("✅ Workspace cleanup completed")


@pytest.fixture(scope="session")
def nuttxspace_path():
    """
    Fixture that returns the path to the NuttX workspace.
    """
    return Path(__file__).parent / "nuttxspace"
