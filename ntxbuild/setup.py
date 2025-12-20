"""
NuttX environment setup module.

This module provides functions to download and set up the NuttX OS
and NuttX Apps repositories from their GitHub sources.
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
) -> None:
    """Download NuttX repository from GitHub.

    Clones the NuttX OS repository to the specified destination or to
    a "nuttx" subdirectory in the current working directory if no
    destination is provided.

    Args:
        source: URL of the NuttX repository to clone.
            Defaults to the official Apache NuttX repository.
        destination: Path where the repository should be cloned.
            If None, clones to "nuttx" in the current directory.
            Defaults to None.
        depth: Depth for shallow clone. 1 means only the latest commit.
            Defaults to 1.
        single_branch: If True, clone only the specified branch.
            Defaults to True.
        branch_name: Name of the branch to clone. Defaults to "master".

    Raises:
        git.exc.GitCommandError: If the git clone operation fails.
        git.exc.InvalidGitRepositoryError: If the destination path
            already exists and is not a valid git repository.
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
) -> None:
    """Download NuttX Apps repository from GitHub.

    Clones the NuttX Apps repository to the specified destination or to
    a "nuttx-apps" subdirectory in the current working directory if no
    destination is provided.

    Args:
        source: URL of the NuttX Apps repository to clone.
            Defaults to the official Apache NuttX Apps repository.
        destination: Path where the repository should be cloned.
            If None, clones to "nuttx-apps" in the current directory.
            Defaults to None.
        depth: Depth for shallow clone. 1 means only the latest commit.
            Defaults to 1.
        single_branch: If True, clone only the specified branch.
            Defaults to True.
        branch_name: Name of the branch to clone. Defaults to "master".

    Raises:
        git.exc.GitCommandError: If the git clone operation fails.
        git.exc.InvalidGitRepositoryError: If the destination path
            already exists and is not a valid git repository.
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
