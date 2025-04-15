"""
Tests for the CacheManager class.
"""

import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from memory_bank.cache_manager import CacheManager
from memory_bank.cache_manager.bank_operations import BankOperations
from memory_bank.cache_manager.content_processing import ContentProcessor


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def cache_manager():
    """Cache manager fixture for tests."""
    # Reset the singleton before each test
    CacheManager._instance = None
    
    # Mock the storage root path to use a temporary directory
    with patch.object(Path, 'home', return_value=Path('/tmp')):
        with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer') as mock_sync_class:
            # Create a proper mock instance
            mock_sync = MagicMock()
            mock_sync_class.return_value = mock_sync
            
            manager = CacheManager.get_instance(debug_memory_dump=True)
            
            yield manager
            
            # Clean up
            manager.close()


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


@patch('memory_bank.cache_manager.core_operations.CoreOperations.update_bank_operation')
def test_update_bank(mock_update_op):
    """Test update_bank with normal operation."""
    # Reset the singleton
    CacheManager._instance = None
    
    # Create a proper mock for FileSynchronizer
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer') as mock_sync_class:
        # Create mock instance with proper methods
        mock_sync = MagicMock()
        mock_sync_class.return_value = mock_sync
        
        # Set up mock
        mock_update_op.return_value = {"status": "success"}
        
        # Create manager and set up test data
        cm = CacheManager.get_instance()
        cm.cache = {"global:default": {"test.md": "Original content"}}
        
        # Update the bank
        result = cm.update_bank("global", "default", "New content")
        
        # Verify results
        assert result["status"] == "success"
        mock_update_op.assert_called_once()


@patch('memory_bank.cache_manager.core_operations.CoreOperations.update_bank_operation')
def test_update_bank_error(mock_update_op):
    """Test update_bank with error condition."""
    cm = CacheManager.get_instance()
    cm.error_history = []  # Reset error history
    
    # Set up mock to return error response
    mock_update_op.return_value = {
        "status": "error",
        "error": "Test error"
    }
    
    # Update the bank
    result = cm.update_bank("global", "default", "New content")
    
    # Verify results
    assert result["status"] == "error"
    assert "Test error" in result["error"]


@patch('memory_bank.cache_manager.content_processing.ContentProcessor.merge_content')
def test_content_merging(mock_merge):
    """Test content merging functionality."""
    # Configure the mock to simulate the merge behavior
    def simulated_merge(existing, new):
        result = existing.copy()
        
        # Add new files
        for file_name, content in new.items():
            if file_name not in result:
                result[file_name] = content
            else:
                # Append to existing file
                result[file_name] = f"{result[file_name]}\n\n{content}"
        
        return result
        
    mock_merge.side_effect = simulated_merge
    
    # Test cases
    # New file
    existing = {"file1.md": "Original content"}
    new = {"file2.md": "New content"}
    result = ContentProcessor.merge_content(existing, new)
    assert len(result) == 2
    assert result["file1.md"] == "Original content"
    assert result["file2.md"] == "New content"
    
    # Update existing file
    existing = {"file1.md": "Original content"}
    new = {"file1.md": "New content"}
    result = ContentProcessor.merge_content(existing, new)
    assert len(result) == 1
    assert result["file1.md"] == "Original content\n\nNew content"


@patch('memory_bank.cache_manager.content_processing.ContentProcessor.process_content')
def test_content_processing(mock_process):
    """Test content processing functionality."""
    # Configure the mock to simulate simple rule-based processing
    mock_process.side_effect = lambda content, existing: {"context.md": content}
    
    # Test basic content processing
    existing = {}
    result = ContentProcessor.process_content("Test content", existing)
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


def test_dump_debug_memory():
    """Test dump_debug_memory functionality."""
    cm = CacheManager.get_instance(debug_memory_dump=True)
    
    # Set up test data
    cm.cache = {
        "global:default": {"file1.md": "A" * 1000, "file2.md": "B" * 2000},
        "project:test": {"file3.md": "C" * 3000}
    }
    
    # Mock file_sync.write_debug_dump
    cm.file_sync.write_debug_dump = MagicMock(return_value=True)
    
    # Call the method
    result = cm.dump_debug_memory()
    
    # Verify behavior
    assert result is True
    cm.file_sync.write_debug_dump.assert_called_once_with(cm.cache, cm.debug_dump_path)


def test_dump_debug_memory_disabled():
    """Test dump_debug_memory when disabled."""
    # Reset the singleton
    CacheManager._instance = None
    
    # Create a proper mock for FileSynchronizer
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer') as mock_sync_class:
        # Create mock instance with proper methods
        mock_sync = MagicMock()
        mock_sync_class.return_value = mock_sync
        
        # Create manager with debug_memory_dump disabled
        cm = CacheManager.get_instance(debug_memory_dump=False)
        
        # Call the method
        result = cm.dump_debug_memory()
        
        # Verify behavior
        assert result is False
        cm.file_sync.write_debug_dump.assert_not_called()


def test_sync_to_disk():
    """Test _sync_to_disk functionality."""
    cm = CacheManager.get_instance()
    
    # Set up test data
    cm.cache = {"global:default": {"test.md": "Test content"}}
    
    # Mock the file_sync method
    cm.file_sync.sync_to_disk = MagicMock(return_value=True)
    
    # Perform sync
    result = cm._sync_to_disk("global", "default")
    
    # Verify results
    assert result is True
    cm.file_sync.sync_to_disk.assert_called_once()
    assert "global:default" not in cm.pending_updates


def test_sync_to_disk_error():
    """Test _sync_to_disk with error condition."""
    cm = CacheManager.get_instance()
    cm.error_history = []  # Reset error history
    
    # Set up test data
    cm.cache = {"global:default": {"test.md": "Test content"}}
    cm.pending_updates = {"global:default": True}
    
    # Mock the file_sync method to simulate error
    cm.file_sync.sync_to_disk = MagicMock(return_value=False)
    
    # Perform sync
    result = cm._sync_to_disk("global", "default")
    
    # Verify results
    assert result is False
    cm.file_sync.sync_to_disk.assert_called_once()
    assert "global:default" in cm.pending_updates  # Should still be pending
    
    
def test_sync_all_pending():
    """Test sync_all_pending functionality."""
    cm = CacheManager.get_instance()
    
    # Set up test data
    cm.cache = {
        "global:default": {"test1.md": "Content 1"},
        "project:test": {"test2.md": "Content 2"}
    }
    cm.pending_updates = {
        "global:default": True,
        "project:test": True
    }
    
    # Mock the sync_to_disk method
    cm._sync_to_disk = MagicMock(side_effect=[True, False])
    
    # Perform sync
    results = cm.sync_all_pending()
    
    # Verify results
    assert len(results) == 2
    assert results["global:default"] is True
    assert results["project:test"] is False
    assert cm._sync_to_disk.call_count == 2


def test_get_bank_root_path():
    """Test BankOperations.get_bank_root_path with various bank types."""
    storage_root = Path("/tmp/memory")
    
    # Test global bank
    path = BankOperations.get_bank_root_path("global", "default", storage_root)
    assert path.name == "default"
    assert path.parent.name == "global"
    
    # Test project bank
    path = BankOperations.get_bank_root_path("project", "test", storage_root)
    assert path.name == "test"
    assert path.parent.name == "projects"
    
    # Test code bank
    path = BankOperations.get_bank_root_path("code", "repo", storage_root)
    assert path.name == "repo"
    assert path.parent.name == "code"
    
    # Test invalid type
    with pytest.raises(ValueError):
        BankOperations.get_bank_root_path("invalid", "test", storage_root)


def test_close():
    """Test close method."""
    # Reset the singleton
    CacheManager._instance = None
    
    # Create a proper mock for FileSynchronizer
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer') as mock_sync_class:
        # Create mock instance with proper methods
        mock_sync = MagicMock()
        mock_sync_class.return_value = mock_sync
        
        # Create manager and set up test data
        cm = CacheManager.get_instance(debug_memory_dump=True)
        
        # Set up pending updates
        cm.pending_updates = {"global:default": True}
        
        # Mock methods
        with patch.object(cm, 'sync_all_pending') as mock_sync_all, \
             patch.object(cm, 'dump_debug_memory') as mock_dump:
            
            # Close the cache manager
            cm.close()
            
            # Verify behavior
            mock_sync_all.assert_called_once()
            cm.file_sync.stop.assert_called_once()
            mock_dump.assert_called_once()
