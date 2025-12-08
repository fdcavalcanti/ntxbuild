"""
NuttX environment setup.
Downloads NuttX and NuttX Apps.
"""

import logging
from pathlib import Path

from git import Repo

NUTTX_URL = "https://github.com/apache/nuttx.git"
NUTTX_APPS_URL = "https://github.com/apache/nuttx-apps.git"


def download_nuttx_repo(
    source: str = NUTTX_URL,
    destination: Path = None,
    depth: int = 1,
    single_branch: bool = True,
    branch_name: str = "master",
):
    """Download NuttX repository to current directory if no path destination
    path is provided.
    """

    if not destination:
        current_dir = Path.cwd()
        nuttx_dir = current_dir / "nuttx"
    else:
        nuttx_dir = destination

    logging.info(f"Cloning apache/nuttx to {nuttx_dir}")

    Repo.clone_from(
        source,
        nuttx_dir,
        depth=depth,
        single_branch=single_branch,
        branch=branch_name,
    )


def download_nuttx_apps_repo(
    source: str = NUTTX_APPS_URL,
    destination: Path = None,
    depth: int = 1,
    single_branch: bool = True,
    branch_name: str = "master",
):
    """Download NuttX Apps repository to current directory if no destination
    path is provided.
    """
    if not destination:
        current_dir = Path.cwd()
        apps_dir = current_dir / "nuttx-apps"
    else:
        apps_dir = destination

    logging.info(f"Cloning apache/nuttx-apps to {apps_dir}")

    Repo.clone_from(
        source,
        apps_dir,
        depth=depth,
        single_branch=single_branch,
        branch=branch_name,
    )
