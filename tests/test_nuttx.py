from pathlib import Path

import pytest

from ntxbuild.nuttx import Board, Defconfig, NuttxBoardExplorer


def _find_some_defconfig(nuttx_repo: Path):
    # Look for defconfig files inside the nuttx repo created by tests/conftest
    pattern = "boards/*/*/*/configs/*/defconfig"
    matches = list(nuttx_repo.glob(pattern))
    return matches[0] if matches else None


def test_defconfig_name_and_content(nuttxspace_path: Path):
    nuttx_repo = nuttxspace_path / "nuttx"
    if not nuttx_repo.exists():
        pytest.skip("nuttx repo not available in tests/nuttxspace")

    defconfig_file = _find_some_defconfig(nuttx_repo)
    if not defconfig_file:
        pytest.skip("No defconfig files found in nuttx repo; skipping test")

    defconfig_dir = defconfig_file.parent
    d = Defconfig(path=defconfig_dir)

    # name should be inferred from path.stem (the defconfig folder name)
    assert d.name == defconfig_dir.stem
    # content should be readable and non-empty
    assert d.content is not None
    assert len(d.content) > 0


def test_board_parsing_and_defconfigs(nuttxspace_path: Path):
    nuttx_repo = nuttxspace_path / "nuttx"
    if not nuttx_repo.exists():
        pytest.skip("nuttx repo not available in tests/nuttxspace")

    defconfig_file = _find_some_defconfig(nuttx_repo)
    if not defconfig_file:
        pytest.skip("No defconfig files found in nuttx repo; skipping test")

    defconfig_dir = defconfig_file.parent
    # board path is two parents up from defconfig dir: .../configs/<name>/ -> board
    board_path = defconfig_dir.parent.parent
    b = Board(path=board_path)

    assert b.name == board_path.stem
    # arch is parents[1].stem (boards/<arch>/...)
    assert b.arch == board_path.parents[1].stem
    # soc is parents[0].stem
    assert b.soc == board_path.parents[0].stem

    # defconfigs should include at least the one we found
    assert any(d.path == defconfig_dir for d in b.defconfigs)


def test_nuttx_board_filter_setters_and_search(nuttxspace_path: Path):
    nuttx_repo = nuttxspace_path / "nuttx"
    if not nuttx_repo.exists():
        pytest.skip("nuttx repo not available in tests/nuttxspace")

    defconfig_file = _find_some_defconfig(nuttx_repo)
    if not defconfig_file:
        pytest.skip("No defconfig files found in nuttx repo; skipping test")

    # Derive arch/soc/board from an existing defconfig
    defconfig_dir = defconfig_file.parent
    board_path = defconfig_dir.parent.parent
    arch = board_path.parents[1].stem
    soc = board_path.parents[0].stem
    board_name = board_path.stem

    nbf = NuttxBoardExplorer(nuttx_path=nuttx_repo)

    boards_arch = nbf.set_arch(arch).boards
    assert len(boards_arch) >= 1
    assert all(b.arch == arch for b in boards_arch)

    boards_soc = nbf.set_soc(soc).boards
    assert any(b.soc == soc for b in boards_soc)

    boards_board = nbf.set_board(board_name).boards
    # There should be at least one board matching the exact board name
    assert any(b.name == board_name for b in boards_board)


def test_board_get_defconfig(nuttxspace_path: Path):
    """Test Board.get_defconfig method to retrieve defconfig by name."""
    nuttx_repo = nuttxspace_path / "nuttx"
    if not nuttx_repo.exists():
        pytest.skip("nuttx repo not available in tests/nuttxspace")

    defconfig_file = _find_some_defconfig(nuttx_repo)
    if not defconfig_file:
        pytest.skip("No defconfig files found in nuttx repo; skipping test")

    defconfig_dir = defconfig_file.parent
    board_path = defconfig_dir.parent.parent
    board = Board(path=board_path)

    # Test getting an existing defconfig
    defconfig_name = defconfig_dir.stem
    found_defconfig = board.get_defconfig(defconfig_name)
    assert found_defconfig is not None
    assert found_defconfig.name == defconfig_name
    assert found_defconfig.path == defconfig_dir
    assert found_defconfig.content is not None
    assert len(found_defconfig.content) > 0

    # Test getting a non-existent defconfig
    non_existent = board.get_defconfig("nonexistent_defconfig_xyz")
    assert non_existent is None
