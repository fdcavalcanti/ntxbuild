"""
Tests for build module.
"""

import pytest
from ntxbuild.build import NuttXBuilder

def test_builder_initialization():
    """Test NuttXBuilder initialization."""
    builder = NuttXBuilder()
    assert builder.config_path is None
    assert builder.config == {}

def test_builder_with_config():
    """Test NuttXBuilder with config path."""
    config_path = "/path/to/config"
    builder = NuttXBuilder(config_path)
    assert builder.config_path == config_path
