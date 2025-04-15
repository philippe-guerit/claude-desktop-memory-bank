"""
Tests for the CacheDiagnostics class.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from memory_bank.cache_manager.cache_diagnostics import CacheDiagnostics


@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager for testing."""
    cm = MagicMock()
    cm.enable_diagnostics = True
    cm.operation_counts = {"cache_hits": 50, "cache_misses": 20}
    cm.operation_timings = {"load_ms": [10.5, 20.3]}
    cm.cache = {"global:default": {"test.md": "content"}}
    cm.pending_updates = {"global:default": True}
    cm.error_history = [{"description": "Test error"}]
    cm.diagnostics_dir = Path("/tmp/diagnostics")
    cm.debug_dump_path = Path("/tmp/cache_memory_dump.json")
    cm.file_sync = MagicMock()
    cm.consistency_checker = MagicMock()
    
    return cm


@patch('memory_bank.cache_manager.cache_diagnostics.DiagnosticUtils.get_diagnostics')
def test_get_diagnostics(mock_get_diagnostics, mock_cache_manager):
    """Test get_diagnostics method."""
    # Configure mock to return test diagnostics
    mock_get_diagnostics.return_value = {"test": "diagnostics"}
    
    # Call the method
    result = CacheDiagnostics.get_diagnostics(mock_cache_manager)
    
    # Verify result
    assert result == {"test": "diagnostics"}
    
    # Verify DiagnosticUtils was called with correct parameters
    mock_get_diagnostics.assert_called_once_with(
        mock_cache_manager.enable_diagnostics,
        mock_cache_manager.operation_counts,
        mock_cache_manager.operation_timings,
        mock_cache_manager.cache,
        mock_cache_manager.pending_updates,
        mock_cache_manager.error_history,
        mock_cache_manager.start_time
    )


@patch('memory_bank.cache_manager.cache_diagnostics.DiagnosticUtils.perform_consistency_check')
def test_perform_consistency_check(mock_check, mock_cache_manager):
    """Test perform_consistency_check method."""
    # Configure mock to return test results
    mock_check.return_value = {"test": "consistency_results"}
    
    # Call the method
    result = CacheDiagnostics.perform_consistency_check(
        mock_cache_manager,
        bank_type="global",
        bank_id="default"
    )
    
    # Verify result
    assert result == {"test": "consistency_results"}
    
    # Verify DiagnosticUtils was called with correct parameters
    mock_check.assert_called_once_with(
        mock_cache_manager.enable_diagnostics,
        mock_cache_manager.consistency_checker,
        mock_cache_manager.cache,
        "global",
        "default"
    )


@patch('memory_bank.cache_manager.cache_diagnostics.DiagnosticUtils.perform_consistency_check')
def test_perform_consistency_check_disabled(mock_check, mock_cache_manager):
    """Test perform_consistency_check when diagnostics are disabled."""
    # Disable diagnostics
    mock_cache_manager.enable_diagnostics = False
    
    # Call the method
    result = CacheDiagnostics.perform_consistency_check(
        mock_cache_manager,
        bank_type="global",
        bank_id="default"
    )
    
    # Verify result
    assert result == {"consistency_check_enabled": False}
    
    # Verify DiagnosticUtils was not called
    mock_check.assert_not_called()


@patch('memory_bank.cache_manager.cache_diagnostics.DiagnosticUtils.export_diagnostics')
def test_export_diagnostics(mock_export, mock_cache_manager):
    """Test export_diagnostics method."""
    # Configure mock to return success
    mock_export.return_value = True
    
    # Call the method
    result = CacheDiagnostics.export_diagnostics(
        mock_cache_manager,
        path=Path("/tmp/test_export.json")
    )
    
    # Verify result
    assert result is True
    
    # Verify DiagnosticUtils was called with correct parameters
    mock_export.assert_called_once()
    assert mock_export.call_args[0][0] == mock_cache_manager.enable_diagnostics
    assert mock_export.call_args[0][1] == mock_cache_manager.diagnostics_dir
    assert callable(mock_export.call_args[0][2])  # get_diagnostics_func
    assert mock_export.call_args[0][3] == Path("/tmp/test_export.json")


@patch('memory_bank.cache_manager.cache_diagnostics.DiagnosticUtils.export_diagnostics')
def test_export_diagnostics_default_path(mock_export, mock_cache_manager):
    """Test export_diagnostics with default path."""
    # Configure mock to return success
    mock_export.return_value = True
    
    # Call the method
    result = CacheDiagnostics.export_diagnostics(
        mock_cache_manager,
        path=None
    )
    
    # Verify result
    assert result is True
    
    # Verify DiagnosticUtils was called with correct parameters
    mock_export.assert_called_once()
    assert mock_export.call_args[0][0] == mock_cache_manager.enable_diagnostics
    assert mock_export.call_args[0][1] == mock_cache_manager.diagnostics_dir
    assert callable(mock_export.call_args[0][2])  # get_diagnostics_func
    assert mock_export.call_args[0][3] is None


def test_dump_debug_memory(mock_cache_manager):
    """Test dump_debug_memory method."""
    # Configure mocks
    mock_cache_manager.debug_memory_dump = True
    mock_cache_manager.file_sync.write_debug_dump.return_value = True
    
    # Call the method
    result = CacheDiagnostics.dump_debug_memory(mock_cache_manager)
    
    # Verify result
    assert result is True
    
    # Verify file_sync was called with correct parameters
    mock_cache_manager.file_sync.write_debug_dump.assert_called_once_with(
        mock_cache_manager.cache,
        mock_cache_manager.debug_dump_path
    )


def test_dump_debug_memory_disabled(mock_cache_manager):
    """Test dump_debug_memory when debugging is disabled."""
    # Disable debug memory dump
    mock_cache_manager.debug_memory_dump = False
    
    # Call the method
    result = CacheDiagnostics.dump_debug_memory(mock_cache_manager)
    
    # Verify result
    assert result is False
    
    # Verify file_sync was not called
    mock_cache_manager.file_sync.write_debug_dump.assert_not_called()
