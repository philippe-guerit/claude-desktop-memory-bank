"""
Tests for the FileSynchronizer class.
"""

import os
import json
import time
from pathlib import Path
import shutil
import tempfile
import threading
import pytest
from unittest.mock import patch, MagicMock

from memory_bank.cache_manager.file_sync import FileSynchronizer


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


def test_init():
    """Test FileSynchronizer initialization."""
    sync = FileSynchronizer(sync_interval=30)
    assert sync.sync_interval == 30
    assert not sync.running
    assert sync.sync_thread is None


def test_start_stop():
    """Test starting and stopping the synchronizer."""
    sync = FileSynchronizer(sync_interval=1)
    assert not sync.running
    
    # Start
    sync.start()
    assert sync.running
    assert sync.sync_thread is not None
    assert sync.sync_thread.is_alive()
    
    # Stop
    sync.stop()
    assert not sync.running
    assert not sync.sync_thread.is_alive()


def test_schedule_sync():
    """Test scheduling a synchronization."""
    sync = FileSynchronizer()
    
    # Schedule a sync
    sync.schedule_sync("global", "default", priority=False)
    assert sync.sync_queue.qsize() == 1
    
    # Check queue content
    bank_type, bank_id, priority = sync.sync_queue.get()
    assert bank_type == "global"
    assert bank_id == "default"
    assert priority is False
    
    # Schedule a priority sync
    sync.schedule_sync("project", "test", priority=True)
    bank_type, bank_id, priority = sync.sync_queue.get()
    assert bank_type == "project"
    assert bank_id == "test"
    assert priority is True


def test_sync_to_disk(temp_dir):
    """Test synchronizing content to disk."""
    sync = FileSynchronizer()
    
    # Create test content
    content = {
        "file1.md": "# Test File 1\n\nThis is test content.",
        "folder/file2.md": "# Test File 2\n\nThis is nested file content."
    }
    
    # Sync to disk
    result = sync.sync_to_disk("global", "test", content, temp_dir)
    assert result is True
    
    # Verify files were created
    assert (temp_dir / "file1.md").exists()
    assert (temp_dir / "folder" / "file2.md").exists()
    
    # Verify file content
    assert (temp_dir / "file1.md").read_text() == "# Test File 1\n\nThis is test content."
    assert (temp_dir / "folder" / "file2.md").read_text() == "# Test File 2\n\nThis is nested file content."
    
    # Check last sync time was updated
    key = "global:test"
    assert key in sync.last_sync_time


def test_sync_to_disk_error(temp_dir):
    """Test synchronizing with error handling."""
    sync = FileSynchronizer()
    
    # Create read-only directory to cause permission error
    if os.name != 'nt':  # Skip on Windows
        read_only_dir = temp_dir / "readonly"
        read_only_dir.mkdir()
        os.chmod(read_only_dir, 0o555)  # Read-only
        
        # Try to sync to read-only directory
        content = {"file.md": "Test content"}
        result = sync.sync_to_disk("global", "test", content, read_only_dir)
        
        # Should fail but not crash
        assert result is False
        
        # Reset permissions for cleanup
        os.chmod(read_only_dir, 0o755)


def test_write_debug_dump(temp_dir):
    """Test writing debug memory dump."""
    sync = FileSynchronizer()
    
    # Create test cache
    cache = {
        "global:default": {
            "file1.md": "Content 1",
            "file2.md": "Content 2"
        },
        "project:test": {
            "file3.md": "Content 3"
        }
    }
    
    # Write debug dump
    dump_path = temp_dir / "cache_memory_dump.json"
    result = sync.write_debug_dump(cache, dump_path)
    assert result is True
    
    # Verify dump file was created
    assert dump_path.exists()
    
    # Verify dump content
    with open(dump_path, 'r') as f:
        dump_data = json.load(f)
        
    assert "cache" in dump_data
    assert "metrics" in dump_data
    assert dump_data["cache"] == cache
    assert "total_tokens" in dump_data["metrics"]
    assert "bank_tokens" in dump_data["metrics"]
    assert "timestamp" in dump_data["metrics"]


def test_get_last_sync_time():
    """Test getting last sync time."""
    sync = FileSynchronizer()
    
    # No sync yet
    assert sync.get_last_sync_time("global", "default") is None
    
    # Set a sync time
    from datetime import datetime, UTC
    now = datetime.now(UTC)
    sync.last_sync_time["global:default"] = now
    
    # Get sync time
    assert sync.get_last_sync_time("global", "default") == now


@patch('threading.Thread')
def test_sync_worker(mock_thread):
    """Test the sync worker thread."""
    # This is a basic test since the worker is hard to test directly
    sync = FileSynchronizer(sync_interval=1)
    sync.start()
    
    # Verify thread was started
    mock_thread.assert_called_once()
    
    # Clean up
    sync.stop()
