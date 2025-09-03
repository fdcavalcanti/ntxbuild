"""
Test the conftest fixtures.
"""


def test_nuttxspace_fixture(nuttxspace):
    """Test that the nuttxspace fixture creates the expected structure."""
    # Check that the workspace exists
    assert nuttxspace.exists()
    assert nuttxspace.is_dir()

    # Check that nuttx directory exists and has expected files
    nuttx_dir = nuttxspace / "nuttx"
    assert nuttx_dir.exists()
    assert nuttx_dir.is_dir()
    assert (nuttx_dir / "Makefile").exists()
    assert (nuttx_dir / "INVIOLABLES.md").exists()

    # Check that nuttx-apps directory exists and has expected files
    apps_dir = nuttxspace / "nuttx-apps"
    assert apps_dir.exists()
    assert apps_dir.is_dir()
    assert (apps_dir / "Make.defs").exists()

    # Verify these are git repositories
    assert (nuttx_dir / ".git").exists()
    assert (apps_dir / ".git").exists()
