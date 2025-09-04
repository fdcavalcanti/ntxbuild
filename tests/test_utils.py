import os

from ntxbuild.utils import cleanup_tmp_copies, copy_nuttxspace_to_tmp

TEST_NUM_COPIES = 3
DIR_NAME = "nuttxspace_"


def test_nuttx_copy_to_tmp(nuttxspace, tmp_path):
    """Test that the nuttxspace is copied to /tmp"""
    copied_paths = copy_nuttxspace_to_tmp(nuttxspace, TEST_NUM_COPIES, tmp_path)
    assert len(copied_paths) == TEST_NUM_COPIES
    assert DIR_NAME + "0" in copied_paths[0]
    assert DIR_NAME + "1" in copied_paths[1]
    assert DIR_NAME + "2" in copied_paths[2]
    assert os.path.exists(copied_paths[0])
    assert os.path.exists(copied_paths[1])
    assert os.path.exists(copied_paths[2])

    cleanup_tmp_copies(copied_paths)
    assert not os.path.exists(DIR_NAME + "0")
    assert not os.path.exists(DIR_NAME + "1")
    assert not os.path.exists(DIR_NAME + "2")
