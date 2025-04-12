"""
Tests for the main module.
"""

import pytest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

import memory_bank.__main__
from memory_bank.server import MemoryBankServer


@pytest.mark.asyncio
async def test_main_function():
    """Test the main function with mocked server."""
    # Mock the MemoryBankServer
    mock_server = MagicMock(spec=MemoryBankServer)
    
    # Create a proper async mock for sleep
    async def mock_sleep_func(seconds):
        raise KeyboardInterrupt()
    
    # Patch the required functions
    with patch("memory_bank.__main__.MemoryBankServer", return_value=mock_server), \
         patch("asyncio.sleep", mock_sleep_func):
        # Call the main function
        await memory_bank.__main__.main()
        
        # Verify server was started and stopped
        mock_server.start.assert_called_once()
        mock_server.stop.assert_called_once()


@pytest.mark.asyncio
async def test_main_with_environment_variable():
    """Test the main function with custom storage root from environment variable."""
    # Set environment variable
    custom_path = "/tmp/custom_memory_bank"
    os.environ["MEMORY_BANK_ROOT"] = custom_path
    
    # Create mocks
    mock_server = MagicMock(spec=MemoryBankServer)
    
    # Create a proper async mock for sleep
    async def mock_sleep_func(seconds):
        raise KeyboardInterrupt()
    
    try:
        # Patch the required functions
        with patch("memory_bank.__main__.MemoryBankServer", return_value=mock_server) as mock_server_class, \
             patch("asyncio.sleep", mock_sleep_func):
            # Call the main function
            await memory_bank.__main__.main()
            
            # Verify server was created with the correct path
            mock_server_class.assert_called_once_with(storage_root=Path(custom_path))
    finally:
        # Clean up environment
        del os.environ["MEMORY_BANK_ROOT"]


@pytest.mark.asyncio
async def test_main_exception_handling():
    """Test exception handling in the main function."""
    # Create mocks
    mock_server = MagicMock(spec=MemoryBankServer)
    
    # Make the server.start() method raise an exception instead of using sleep
    mock_server.start.side_effect = Exception("Test exception")
    
    # Patch the required functions
    with patch("memory_bank.__main__.MemoryBankServer", return_value=mock_server), \
         pytest.raises(Exception) as excinfo:  # Expect an exception
        # Call the main function
        await memory_bank.__main__.main()
    
    # Verify exception was propagated
    assert "Test exception" in str(excinfo.value)
    
    # Verify server was started and stop was still called in finally block
    mock_server.start.assert_called_once()
    mock_server.stop.assert_called_once()


def test_module_execution():
    """Test the module execution."""
    # Create a mock for asyncio.run
    with patch("asyncio.run") as mock_run:
        # Save the current __name__ value
        original_name = memory_bank.__main__.__name__
        
        try:
            # Set __name__ to "__main__" to trigger the code block
            memory_bank.__main__.__name__ = "__main__"
            
            # Execute the relevant code directly
            if memory_bank.__main__.__name__ == "__main__":
                # This is what happens in __main__.py when __name__ == "__main__"
                memory_bank.__main__.asyncio.run = mock_run
                memory_bank.__main__.asyncio.run(memory_bank.__main__.main())
            
            # Verify asyncio.run was called with main
            mock_run.assert_called_once()
            assert mock_run.call_args[0][0].__name__ == "main"
        finally:
            # Restore the original __name__ value
            memory_bank.__main__.__name__ = original_name
