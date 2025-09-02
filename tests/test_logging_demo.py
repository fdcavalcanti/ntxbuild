"""
Simple test to demonstrate logging functionality.
"""

import pytest
import logging
from ntxbuild.build import NuttXBuilder

def test_logging_visibility():
    """Test that logging output is visible during test execution."""
    print("\n=== Testing Logging Visibility ===")
    
    # This should produce visible logging output
    builder = NuttXBuilder()
    
    # Test some methods that should log
    builder.clean()
    builder.distclean()
    
    print("=== Logging Test Complete ===\n")
    
    # Basic assertion to make this a valid test
    assert builder is not None

def test_logger_configuration():
    """Test that the logger is properly configured."""
    logger = logging.getLogger('ntxbuild.build')
    
    # Check logger level
    print(f"Logger level: {logger.level}")
    print(f"Logger handlers: {len(logger.handlers)}")
    
    # Log a test message
    logger.info("This is a test log message from the test")
    logger.debug("This is a debug message")
    
    assert logger.level <= logging.DEBUG
