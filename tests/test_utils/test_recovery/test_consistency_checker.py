"""
Tests for the ConsistencyChecker class.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from memory_bank.utils.recovery import ConsistencyChecker


@pytest.fixture
def temp_storage():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    root = Path(temp_dir)
    
    # Create storage structure
    global_dir = root / "global" / "default"
    global_dir.mkdir(parents=True)
    (global_dir / "context.md").write_text("Test content")
    
    project_dir = root / "projects" / "test"
    project_dir.mkdir(parents=True)
    (project_dir / "readme.md").write_text("Project content")
    
    diag_dir = root / "diagnostics"
    diag_dir.mkdir(parents=True)
    
    yield root
    shutil.rmtree(temp_dir)


@pytest.fixture
def checker(temp_storage):
    """Create a ConsistencyChecker instance with a temp storage path."""
    return ConsistencyChecker(temp_storage)


def test_check_bank_consistency_consistent(checker, temp_storage):
    """Test check_bank_consistency with a consistent bank."""
    # Setup
    cache_content = {
        "context.md": "Test content"  # Matches file on disk
    }
    
    # Check
    is_consistent, issues = checker.check_bank_consistency(
        bank_type="global",
        bank_id="default",
        cache_content=cache_content
    )
    
    # Verify
    assert is_consistent is True
    assert len(issues) == 0


def test_check_bank_consistency_inconsistent_content(checker, temp_storage):
    """Test check_bank_consistency with inconsistent content."""
    # Setup
    cache_content = {
        "context.md": "Modified content"  # Doesn't match file on disk
    }
    
    # Check
    is_consistent, issues = checker.check_bank_consistency(
        bank_type="global",
        bank_id="default",
        cache_content=cache_content
    )
    
    # Verify
    assert is_consistent is False
    assert len(issues) == 1
    assert "different content" in issues[0]


def test_check_bank_consistency_missing_file(checker, temp_storage):
    """Test check_bank_consistency with file in cache but not on disk."""
    # Setup
    cache_content = {
        "context.md": "Test content",
        "missing.md": "Content for missing file"
    }
    
    # Check
    is_consistent, issues = checker.check_bank_consistency(
        bank_type="global",
        bank_id="default",
        cache_content=cache_content
    )
    
    # Verify
    assert is_consistent is False
    assert len(issues) == 1
    assert "missing.md" in issues[0]
    assert "exists in cache but not on disk" in issues[0]


def test_check_bank_consistency_nonexistent_bank(checker, temp_storage):
    """Test check_bank_consistency with a bank that doesn't exist on disk."""
    # Setup
    cache_content = {
        "test.md": "Test content"
    }
    
    # Check
    is_consistent, issues = checker.check_bank_consistency(
        bank_type="global",
        bank_id="nonexistent",
        cache_content=cache_content
    )
    
    # Verify
    assert is_consistent is False
    assert len(issues) == 1
    assert "doesn't exist on disk" in issues[0]


@patch('pathlib.Path.read_text')
def test_check_bank_consistency_read_error(mock_read, checker, temp_storage):
    """Test check_bank_consistency with file read error."""
    # Setup
    cache_content = {
        "context.md": "Test content"
    }
    
    # Make read_text raise an exception
    mock_read.side_effect = Exception("Test read error")
    
    # Check
    is_consistent, issues = checker.check_bank_consistency(
        bank_type="global",
        bank_id="default",
        cache_content=cache_content
    )
    
    # Verify
    assert is_consistent is False
    assert len(issues) == 1
    assert "Error reading file" in issues[0]
    assert "Test read error" in str(issues[0])


def test_get_bank_path(checker, temp_storage):
    """Test _get_bank_path with various bank types."""
    # Test global bank
    path = checker._get_bank_path("global", "default")
    assert path == temp_storage / "global" / "default"
    
    # Test project bank
    path = checker._get_bank_path("project", "test")
    assert path == temp_storage / "projects" / "test"
    
    # Test code bank
    path = checker._get_bank_path("code", "repo")
    assert path == temp_storage / "code" / "repo"
    
    # Test invalid type
    with pytest.raises(ValueError):
        checker._get_bank_path("invalid", "test")


@patch('json.dump')
def test_log_diagnostic_info_existing_bank(mock_dump, checker, temp_storage):
    """Test log_diagnostic_info with an existing bank."""
    # Call the method
    checker.log_diagnostic_info(
        bank_type="global",
        bank_id="default",
        issue="Test diagnostic issue"
    )
    
    # Verify json.dump was called
    assert mock_dump.call_count == 1
    
    # Check first argument (diagnostic info)
    info = mock_dump.call_args[0][0]
    assert info["bank_type"] == "global"
    assert info["bank_id"] == "default"
    assert info["issue"] == "Test diagnostic issue"
    assert info["bank_exists"] is True
    assert len(info["files"]) == 1  # context.md


@patch('json.dump')
def test_log_diagnostic_info_nonexistent_bank(mock_dump, checker, temp_storage):
    """Test log_diagnostic_info with a bank that doesn't exist."""
    # Call the method
    checker.log_diagnostic_info(
        bank_type="global",
        bank_id="nonexistent",
        issue="Bank doesn't exist"
    )
    
    # Verify json.dump was called
    assert mock_dump.call_count == 1
    
    # Check first argument (diagnostic info)
    info = mock_dump.call_args[0][0]
    assert info["bank_type"] == "global"
    assert info["bank_id"] == "nonexistent"
    assert info["bank_exists"] is False
    assert len(info["files"]) == 0


@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
def test_log_diagnostic_info_error(mock_dump, mock_open, checker, temp_storage):
    """Test log_diagnostic_info error handling."""
    # Make json.dump raise an exception
    mock_dump.side_effect = Exception("Test dump error")
    
    # Call the method
    checker.log_diagnostic_info(
        bank_type="global",
        bank_id="default",
        issue="Test issue"
    )
    
    # Function should not raise exceptions, errors are logged
    # No assertions needed as we're just confirming it doesn't crash
