"""
Tests for the CacheManager class.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from memory_bank.cache_manager import CacheManager


@pytest.fixture
def cache_manager():
    """Cache manager fixture for tests."""
    # Reset the singleton before each test
    CacheManager._instance = None
    manager = CacheManager.get_instance(debug_memory_dump=True)
    return manager


def test_singleton_pattern():
    """Test that CacheManager follows the singleton pattern."""
    CacheManager._instance = None  # Reset singleton
    
    # Create two instances
    cm1 = CacheManager.get_instance()
    cm2 = CacheManager.get_instance()
    
    # Should be the same object
    assert cm1 is cm2


def test_get_bank_key():
    """Test bank key generation."""
    cm = CacheManager.get_instance()
    
    # Test various bank types and IDs
    assert cm.get_bank_key("global", "default") == "global:default"
    assert cm.get_bank_key("project", "test_project") == "project:test_project"
    assert cm.get_bank_key("code", "repo_id") == "code:repo_id"


def test_has_bank_empty():
    """Test has_bank with empty cache."""
    cm = CacheManager.get_instance()
    cm.cache = {}  # Ensure empty cache
    
    # Should return False for any bank
    assert not cm.has_bank("global", "default")
    assert not cm.has_bank("project", "test_project")
    assert not cm.has_bank("code", "repo_id")


def test_has_bank_with_cache():
    """Test has_bank with populated cache."""
    cm = CacheManager.get_instance()
    
    # Add some banks to the cache
    cm.cache = {
        "global:default": {},
        "project:test_project": {}
    }
    
    # Should return True for cached banks, False for others
    assert cm.has_bank("global", "default")
    assert cm.has_bank("project", "test_project")
    assert not cm.has_bank("code", "repo_id")


@patch('memory_bank.cache_manager.cache_manager.CacheManager._load_bank_from_disk')
def test_get_bank_cached(mock_load):
    """Test get_bank when bank is already cached."""
    cm = CacheManager.get_instance()
    
    # Add a bank to the cache
    test_content = {"test.md": "Test content"}
    cm.cache = {"global:default": test_content}
    
    # Should return cached content without loading from disk
    result = cm.get_bank("global", "default")
    assert result == test_content
    mock_load.assert_not_called()


@patch('memory_bank.cache_manager.cache_manager.CacheManager._load_bank_from_disk')
def test_get_bank_not_cached(mock_load):
    """Test get_bank when bank is not cached."""
    cm = CacheManager.get_instance()
    cm.cache = {}  # Ensure empty cache
    
    # Should attempt to load from disk
    cm.get_bank("global", "default")
    mock_load.assert_called_once_with("global", "default")


@patch('memory_bank.cache_manager.cache_manager.CacheManager._process_content')
@patch('memory_bank.cache_manager.cache_manager.CacheManager._schedule_disk_sync')
@patch('memory_bank.cache_manager.cache_manager.CacheManager.dump_debug_memory')
def test_update_bank(mock_dump, mock_schedule, mock_process):
    """Test update_bank with normal operation."""
    cm = CacheManager.get_instance()
    
    # Set up mocks
    mock_process.return_value = {"test.md": "Processed content"}
    
    # Add a bank to the cache
    cm.cache = {"global:default": {"test.md": "Original content"}}
    
    # Update the bank
    result = cm.update_bank("global", "default", "New content")
    
    # Verify results
    assert result["status"] == "success"
    assert cm.pending_updates.get("global:default") is True
    mock_process.assert_called_once()
    mock_schedule.assert_called_once_with("global", "default")
    mock_dump.assert_called_once()


@patch('memory_bank.cache_manager.cache_manager.CacheManager._process_content')
def test_update_bank_error(mock_process):
    """Test update_bank with error condition."""
    cm = CacheManager.get_instance()
    cm.error_history = []  # Reset error history
    
    # Set up mock to raise exception
    mock_process.side_effect = Exception("Test error")
    
    # Update the bank
    result = cm.update_bank("global", "default", "New content")
    
    # Verify results
    assert result["status"] == "error"
    assert "Test error" in result["error"]
    assert len(cm.error_history) == 1
    assert "Test error" in cm.error_history[0]["description"]


def test_merge_content():
    """Test _merge_content with various scenarios."""
    cm = CacheManager.get_instance()
    
    # New file
    existing = {"file1.md": "Original content"}
    new = {"file2.md": "New content"}
    result = cm._merge_content(existing, new)
    assert len(result) == 2
    assert result["file1.md"] == "Original content"
    assert result["file2.md"] == "New content"
    
    # Update existing file
    existing = {"file1.md": "Original content"}
    new = {"file1.md": "New content"}
    result = cm._merge_content(existing, new)
    assert len(result) == 1
    assert result["file1.md"] == "Original content\n\nNew content"


def test_process_with_rules():
    """Test _process_with_rules basic functionality."""
    cm = CacheManager.get_instance()
    
    # Simple processing test
    existing = {}
    result = cm._process_with_rules("Test content", existing)
    assert "context.md" in result
    assert result["context.md"] == "Test content"


def test_get_error_history():
    """Test get_error_history with various scenarios."""
    cm = CacheManager.get_instance()
    
    # Empty history
    cm.error_history = []
    assert cm.get_error_history() == []
    
    # Few errors
    cm.error_history = [{"description": f"Error {i}"} for i in range(5)]
    assert len(cm.get_error_history()) == 5
    
    # Many errors (should return last 10)
    cm.error_history = [{"description": f"Error {i}"} for i in range(20)]
    result = cm.get_error_history()
    assert len(result) == 10
    assert result[0]["description"] == "Error 10"
    assert result[9]["description"] == "Error 19"


@patch('builtins.open')
@patch('json.dump')
@patch('pathlib.Path.mkdir')
def test_dump_debug_memory(mock_mkdir, mock_dump, mock_open):
    """Test dump_debug_memory functionality."""
    cm = CacheManager.get_instance(debug_memory_dump=True)
    
    # Set up test data
    cm.cache = {
        "global:default": {"file1.md": "A" * 1000, "file2.md": "B" * 2000},
        "project:test": {"file3.md": "C" * 3000}
    }
    
    # Call the method
    cm.dump_debug_memory()
    
    # Verify behavior
    mock_mkdir.assert_called_once()
    mock_open.assert_called_once()
    mock_dump.assert_called_once()
    args, kwargs = mock_dump.call_args
    assert args[0] == cm.cache  # First arg should be the cache


def test_dump_debug_memory_disabled():
    """Test dump_debug_memory when disabled."""
    cm = CacheManager.get_instance(debug_memory_dump=False)
    
    # Mock methods to verify they're not called
    cm._get_cache_size = MagicMock()
    
    # Call the method
    cm.dump_debug_memory()
    
    # Verify behavior
    cm._get_cache_size.assert_not_called()
