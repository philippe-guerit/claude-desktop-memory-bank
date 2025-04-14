"""
Tests for the async/sync bridge.

Verifies that the AsyncBridge correctly handles the boundary between
synchronous and asynchronous code.
"""

import pytest
import asyncio
import threading
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from memory_bank.content.async_bridge import AsyncBridge


class TestAsyncBridge:
    """Tests for the AsyncBridge."""
    
    @pytest.mark.asyncio
    async def test_run_async_in_thread(self):
        """Test running an async function in a separate thread."""
        # Create a simple async function
        async def test_func():
            await asyncio.sleep(0.1)
            return "test_result"
            
        # Since this runs in an event loop (pytest-asyncio), it should use run_async_in_thread
        result = AsyncBridge.run_async_safely(test_func())
        assert result == "test_result"
    
    def test_run_async_in_new_loop(self):
        """Test running an async function in a new event loop."""
        # Create a simple async function
        async def test_func():
            await asyncio.sleep(0.1)
            return "test_result"
            
        # Mock get_event_loop to raise RuntimeError
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No event loop")):
            result = AsyncBridge.run_async_safely(test_func())
            assert result == "test_result"
    
    def test_run_async_in_existing_loop(self):
        """Test running an async function in an existing but not running event loop."""
        # Create a simple async function
        async def test_func():
            await asyncio.sleep(0.1)
            return "test_result"
            
        # Create a mock event loop that's not running
        mock_loop = MagicMock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.return_value = "test_result"
        
        with patch('asyncio.get_event_loop', return_value=mock_loop):
            result = AsyncBridge.run_async_safely(test_func())
            assert result == "test_result"
            # Verify the right method was called
            mock_loop.run_until_complete.assert_called_once()
    
    def test_timeout_handling(self):
        """Test that timeouts are properly handled."""
        # Create a slow async function
        async def slow_func():
            await asyncio.sleep(2.0)
            return "slow_result"
            
        # This should timeout
        with pytest.raises(TimeoutError):
            AsyncBridge.run_async_safely(slow_func(), timeout=0.1)
    
    def test_process_content_sync(self):
        """Test the specialized content processing wrapper."""
        # Create a mock async processing function
        async def mock_process(content, existing_cache, bank_type, **kwargs):
            # Simulate some async processing
            await asyncio.sleep(0.1)
            return {
                "target_file": "test_file.md",
                "operation": "append",
                "content": f"Processed: {content}"
            }
            
        # Test with valid input
        result = AsyncBridge.process_content_sync(
            mock_process,
            "Test content",
            {"existing.md": "Existing content"},
            "project",
            extra_param="test"
        )
        
        assert result["target_file"] == "test_file.md"
        assert result["operation"] == "append"
        assert "Processed: Test content" in result["content"]
        
    def test_process_content_sync_invalid_result(self):
        """Test handling of invalid processing results."""
        # Create a mock async processing function that returns invalid data
        async def invalid_process(content, existing_cache, bank_type, **kwargs):
            await asyncio.sleep(0.1)
            return "Not a dictionary"
            
        # This should raise a ValueError
        with pytest.raises(ValueError, match="Invalid content processing result"):
            AsyncBridge.process_content_sync(
                invalid_process,
                "Test content",
                {},
                "project"
            )
            
    def test_process_content_sync_exception(self):
        """Test exception handling in content processing."""
        # Create a mock async processing function that raises an exception
        async def failing_process(content, existing_cache, bank_type, **kwargs):
            await asyncio.sleep(0.1)
            raise ValueError("Test failure")
            
        # This should propagate the exception
        with pytest.raises(ValueError, match="Test failure"):
            AsyncBridge.process_content_sync(
                failing_process,
                "Test content",
                {},
                "project"
            )
