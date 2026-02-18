"""Helpers to discover boards and defconfigs inside a NuttX repository.

This module defines small data classes that represent defconfig directories
and board directories under the NuttX source tree (typically
`<nuttxspace>/nuttx/boards/<arch>/<soc>/<board>/configs/<defconfig>/defconfig`).

The classes are intentionally lightweight and used by the CLI and
other higher-level helpers to enumerate available boards and defconfigs.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from tabulate import tabulate

logger = logging.getLogger(__name__)


@dataclass
class Defconfig:
    path: Path
    name: str = None
    """Representation of a defconfig directory.

    Attributes:
        path: Path to the defconfig directory (the folder that contains the
            file named `defconfig`).
        name: Optional explicit name for the defconfig. If not provided, the
            directory name (path.stem) is used.
    """

    def __post_init__(self):
        if not self.name:
            logger.debug(f"Set defconfig name to {self.path.stem} from {self.path}")
            self.name = self.path.stem

    @property
    def content(self):
        """Return the text content of the `defconfig` file.

        Returns:
            The defconfig file contents as a string.
        """
        return (self.path / "defconfig").read_text()


@dataclass
class Board:
    path: Path
    name: str = None
    arch: str = None
    soc: str = None
    defconfigs: list[Defconfig] = field(default_factory=list)
    """Representation of a NuttX board directory.

    The expected layout for `path` is:
    `.../boards/<arch>/<soc>/<board>`.

    If only the Path is provided, the other files are inferred from it.

    Attributes:
        path: Path to the board directory.
        name: Board name (inferred from path.stem if not provided).
        arch: Architecture name (inferred from path.parents[1].stem if not
            provided).
        soc: SoC/chip name (inferred from path.parents[0].stem if not
            provided).
        defconfigs: List of `Defconfig` objects found under the
            `configs/` subdirectory.
    """

    def __post_init__(self):
        if not self.name:
            self.name = self.path.stem
        if not self.arch:
            self.arch = self.path.parents[1].stem
        if not self.soc:
            self.soc = self.path.parents[0].stem
        self._parse_defconfigs()

    def _parse_defconfigs(self):
        """Discover defconfig directories under the board `configs/` folder.

        This will look for `configs/*` and create a `Defconfig` object for
        each match.
        """
        matches = self.path.glob("configs/*")
        self.defconfigs = [Defconfig(m) for m in matches]
        self.defconfigs.sort(key=lambda x: x.name)
        logger.debug(f"Found {len(self.defconfigs)} configs")

    def print_defconfig_summary(self):
        """Print the defconfigs for the board."""
        if len(self.defconfigs) == 0:
            logger.error(f"No defconfigs found for board {self.name}")
            return

        if len(self.defconfigs) > 15:
            names = [config.name for config in self.defconfigs]
            rows = [names[i : i + 2] for i in range(0, len(names), 2)]
            print(
                tabulate(
                    rows, headers=["Defconfigs", "Defconfigs"], tablefmt="fancy_grid"
                )
            )
        else:
            names = [[config.name] for config in self.defconfigs]
            print(tabulate(names, headers=["Defconfigs"], tablefmt="fancy_grid"))

        board_path = self.path.relative_to(self.path.parents[2])
        print(
            tabulate(
                [[len(self.defconfigs), self.name, self.arch, self.soc, board_path]],
                headers=["Total", "Board", "Arch", "Soc", "Path (nuttx/boards/)"],
                tablefmt="fancy_grid",
            )
        )

    def get_defconfig(self, name: str):
        """Iterate available defconfigs and return the one with the given name."""
        for defconfig in self.defconfigs:
            if defconfig.name == name:
                return defconfig
        return None


class NuttxBoardExplorer:
    """Helper to search for boards inside a NuttX repository.
    User must set filtering criteria before searching and
    retrieve results via the `boards` property.

    Args:
        nuttx_path: Path to the root of the NuttX repository (the folder
            that contains the `boards/` subdirectory).
    """

    def __init__(self, nuttx_path: Path):
        self.boards_dir = Path(nuttx_path) / "boards"

    @property
    def boards(self) -> list:
        return self._search_board()

    def set_arch(self, arch: str):
        """Filter search results by architecture name.

        Example filter pattern produced: `<arch>/*/*/configs`.
        """
        self.filter = f"{arch}/*/*/configs"
        return self

    def set_soc(self, soc: str):
        """Filter search results by SoC/chip name.

        Example filter pattern produced: `*/<soc>/*/configs`.
        """
        self.filter = f"*/{soc}/*/configs"
        return self

    def set_board(self, board: str):
        """Filter search results by board name.

        Example filter pattern produced: `*/*/<board>/configs`.
        """
        self.filter = f"*/*/{board}/configs"
        return self

    def _search_board(self):
        """Execute the glob search and return a list of `Board` objects.

        The `filter` attribute must be set by one of the `set_*` helpers
        before calling this method (or accessing the `boards` property).
        """
        matches = self.boards_dir.glob(self.filter)
        board_list = []
        for match in matches:
            board_path = match.parent
            board = Board(board_path)
            board_list.append(board)
        board_list.sort(key=lambda x: x.name)
        logger.debug(f"Found {len(board_list)} boards")
        return board_list

    def print_board_summary(self):
        """Print the board summary."""
        logger.debug("Printing board summary")
        if len(self.boards) == 0:
            logger.error("No boards found")
            return

        if len(self.boards) > 15:
            names = [board.name for board in self.boards]
            rows = [names[i : i + 2] for i in range(0, len(names), 2)]
            print(tabulate(rows, headers=["Boards", "Boards"], tablefmt="fancy_grid"))
        else:
            names = [[board.name] for board in self.boards]
            print(tabulate(names, headers=["Boards"], tablefmt="fancy_grid"))

        print(f"Total boards: {len(self.boards)}\n")
