import os
from pathlib import Path

from click.testing import CliRunner

from ntxbuild.cli import build, clean, distclean, start


def test_start(nuttxspace_path):
    os.chdir(nuttxspace_path)

    runner = CliRunner()
    result = runner.invoke(start, ["sim", "nshhhh"])
    assert result.exit_code != 0

    result = runner.invoke(start, ["sim", "nsh"])
    assert result.exit_code == 0


def test_build_and_clean(nuttxspace_path):
    os.chdir(nuttxspace_path)

    runner = CliRunner()
    result = runner.invoke(build, ["-j4"])
    assert result.exit_code == 0

    result = runner.invoke(clean, [])
    assert result.exit_code == 0

    result = runner.invoke(build, ["-j4"])
    assert result.exit_code == 0
    assert (Path(nuttxspace_path) / "nuttx" / "nuttx").exists()


def test_distclean(nuttxspace_path):
    os.chdir(nuttxspace_path)

    runner = CliRunner()
    result = runner.invoke(distclean, [])
    assert result.exit_code == 0
