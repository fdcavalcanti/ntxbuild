"""
Pytest configuration and fixtures for ntxbuild tests.
"""

import logging
import shutil
from pathlib import Path

import pytest

from ntxbuild.setup import download_nuttx_apps_repo, download_nuttx_repo


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

    # Check if workspace already exists
    if workspace.exists():
        logging.info(
            f"NuttX workspace already exists at {workspace}, "
            "skipping clone and cleanup."
        )
        yield workspace
        return

    workspace.mkdir(exist_ok=True)

    try:
        # Clone NuttX repository (light clone)
        nuttx_dir = workspace / "nuttx"
        download_nuttx_repo(destination=nuttx_dir)

        # Clone NuttX apps repository (light clone)
        apps_dir = workspace / "nuttx-apps"
        download_nuttx_apps_repo(destination=apps_dir)

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
