"""
Tests for the DiagnosticUtils class.
"""

import json
import pytest
import tempfile
import shutil
from datetime import datetime, UTC
from pathlib import Path
from unittest.mock import patch, MagicMock

from memory_bank.cache_manager.diagnostic_utils import DiagnosticUtils


@pytest.fixture
def test_data():
    """Sample data for testing diagnostics."""
    return {
        "operation_counts": {
            "cache_hits": 50,
            "cache_misses": 20,
            "load_operations": 30,
            "update_operations": 40,
            "sync_operations": 25,
            "sync_failures": 5
        },
        "operation_timings": {
            "load_time_ms": [10.5, 20.3, 15.8],
            "update_time_ms": [30.1, 25.7, 35.2],
            "sync_time_ms": [50.5, 45.2, 55.8]
        },
        "cache": {
            "global:default": {
                "context.md": "A" * 1000,
                "preferences.md": "B" * 2000
            },
            "project:test": {
                "readme.md": "C" * 3000,
                "architecture.md": "D" * 4000
            }
        },
        "pending_updates": {
            "global:default": True,
            "project:test": True
        },
        "error_history": [
            {
                "timestamp": "2025-04-10T14:32:10Z",
                "description": "Failed to process content for doc/design.md",
                "severity": "warning"
            },
            {
                "timestamp": "2025-04-10T15:42:20Z",
                "description": "Failed to sync content to disk",
                "severity": "error"
            }
        ],
        "start_time": datetime(2025, 4, 10, 10, 0, 0, tzinfo=UTC)
    }


def test_get_diagnostics_enabled(test_data):
    """Test get_diagnostics with diagnostics enabled."""
    result = DiagnosticUtils.get_diagnostics(
        enable_diagnostics=True,
        operation_counts=test_data["operation_counts"],
        operation_timings=test_data["operation_timings"],
        cache=test_data["cache"],
        pending_updates=test_data["pending_updates"],
        error_history=test_data["error_history"],
        start_time=test_data["start_time"]
    )
    
    # Check basic structure
    assert "timestamp" in result
    assert "uptime_seconds" in result
    assert "operation_counts" in result
    assert "cache_hit_rate_percent" in result
    assert "average_timings_ms" in result
    assert "cache_size" in result
    assert "pending_updates" in result
    assert "error_count" in result
    assert "recent_errors" in result
    
    # Check specific values
    assert result["cache_hit_rate_percent"] == (50 / (50 + 20)) * 100  # 71.43%
    assert len(result["operation_counts"]) == len(test_data["operation_counts"])
    assert result["cache_size"]["banks_count"] == 2
    assert result["cache_size"]["total_files"] == 4
    assert result["pending_updates"] == 2
    assert result["error_count"] == 2
    assert len(result["recent_errors"]) == 2


def test_get_diagnostics_disabled(test_data):
    """Test get_diagnostics with diagnostics disabled."""
    result = DiagnosticUtils.get_diagnostics(
        enable_diagnostics=False,
        operation_counts=test_data["operation_counts"],
        operation_timings=test_data["operation_timings"],
        cache=test_data["cache"],
        pending_updates=test_data["pending_updates"],
        error_history=test_data["error_history"],
        start_time=test_data["start_time"]
    )
    
    # Should return minimal response
    assert result == {"diagnostics_enabled": False}


def test_get_diagnostics_average_timings(test_data):
    """Test calculation of average timings in get_diagnostics."""
    result = DiagnosticUtils.get_diagnostics(
        enable_diagnostics=True,
        operation_counts=test_data["operation_counts"],
        operation_timings=test_data["operation_timings"],
        cache=test_data["cache"],
        pending_updates=test_data["pending_updates"],
        error_history=test_data["error_history"],
        start_time=test_data["start_time"]
    )
    
    # Check average timings
    assert "average_timings_ms" in result
    assert "load_time_ms" in result["average_timings_ms"]
    assert "update_time_ms" in result["average_timings_ms"]
    assert "sync_time_ms" in result["average_timings_ms"]
    
    # Calculate expected averages
    expected_load_avg = sum(test_data["operation_timings"]["load_time_ms"]) / len(test_data["operation_timings"]["load_time_ms"])
    expected_update_avg = sum(test_data["operation_timings"]["update_time_ms"]) / len(test_data["operation_timings"]["update_time_ms"])
    expected_sync_avg = sum(test_data["operation_timings"]["sync_time_ms"]) / len(test_data["operation_timings"]["sync_time_ms"])
    
    # Check specific values
    assert result["average_timings_ms"]["load_time_ms"] == expected_load_avg
    assert result["average_timings_ms"]["update_time_ms"] == expected_update_avg
    assert result["average_timings_ms"]["sync_time_ms"] == expected_sync_avg


def test_get_diagnostics_cache_size(test_data):
    """Test cache size calculations in get_diagnostics."""
    result = DiagnosticUtils.get_diagnostics(
        enable_diagnostics=True,
        operation_counts=test_data["operation_counts"],
        operation_timings=test_data["operation_timings"],
        cache=test_data["cache"],
        pending_updates=test_data["pending_updates"],
        error_history=test_data["error_history"],
        start_time=test_data["start_time"]
    )
    
    # Check cache size calculations
    cache_size = result["cache_size"]
    assert cache_size["banks_count"] == 2
    assert cache_size["total_files"] == 4
    
    # Calculate expected character size
    expected_char_size = 1000 + 2000 + 3000 + 4000
    assert cache_size["total_character_size"] == expected_char_size
    
    # Estimated tokens (characters / 4)
    assert cache_size["estimated_total_tokens"] == expected_char_size // 4
    
    # Check individual bank sizes
    assert "banks" in cache_size
    assert "global:default" in cache_size["banks"]
    assert "project:test" in cache_size["banks"]
    
    # Check specific bank size details
    global_bank = cache_size["banks"]["global:default"]
    assert global_bank["files_count"] == 2
    assert global_bank["character_size"] == 3000
    assert global_bank["estimated_tokens"] == 3000 // 4
    
    project_bank = cache_size["banks"]["project:test"]
    assert project_bank["files_count"] == 2
    assert project_bank["character_size"] == 7000
    assert project_bank["estimated_tokens"] == 7000 // 4


def test_get_diagnostics_empty_cache(test_data):
    """Test get_diagnostics with an empty cache."""
    # Create a copy with empty cache
    data = dict(test_data)
    data["cache"] = {}
    
    result = DiagnosticUtils.get_diagnostics(
        enable_diagnostics=True,
        operation_counts=data["operation_counts"],
        operation_timings=data["operation_timings"],
        cache=data["cache"],
        pending_updates=data["pending_updates"],
        error_history=data["error_history"],
        start_time=data["start_time"]
    )
    
    # Check cache size calculations for empty cache
    cache_size = result["cache_size"]
    assert cache_size["banks_count"] == 0
    assert cache_size["total_files"] == 0
    assert cache_size["total_character_size"] == 0
    assert cache_size["estimated_total_tokens"] == 0
    assert cache_size["banks"] == {}


def test_get_diagnostics_empty_timings(test_data):
    """Test get_diagnostics with empty timing data."""
    # Create a copy with empty timings
    data = dict(test_data)
    data["operation_timings"] = {
        "load_time_ms": [],
        "update_time_ms": [],
        "sync_time_ms": []
    }
    
    result = DiagnosticUtils.get_diagnostics(
        enable_diagnostics=True,
        operation_counts=data["operation_counts"],
        operation_timings=data["operation_timings"],
        cache=data["cache"],
        pending_updates=data["pending_updates"],
        error_history=data["error_history"],
        start_time=data["start_time"]
    )
    
    # Check average timings with empty data
    assert "average_timings_ms" in result
    assert result["average_timings_ms"]["load_time_ms"] == 0
    assert result["average_timings_ms"]["update_time_ms"] == 0
    assert result["average_timings_ms"]["sync_time_ms"] == 0


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


def test_export_diagnostics(temp_dir):
    """Test export_diagnostics functionality."""
    # Setup
    diagnostics_dir = temp_dir / "diagnostics"
    diagnostics_dir.mkdir()
    
    # Create a mock diagnostics function
    def get_diagnostics_func():
        return {
            "timestamp": "2025-04-10T15:30:00Z",
            "cache_hit_rate_percent": 75.0,
            "operation_counts": {
                "cache_hits": 75,
                "cache_misses": 25
            }
        }
    
    # Test with explicit path
    export_path = temp_dir / "test_export.json"
    result = DiagnosticUtils.export_diagnostics(
        enable_diagnostics=True,
        diagnostics_dir=diagnostics_dir,
        get_diagnostics_func=get_diagnostics_func,
        path=export_path
    )
    
    # Check result
    assert result is True
    assert export_path.exists()
    
    # Check file content
    with open(export_path) as f:
        data = json.load(f)
        assert data["timestamp"] == "2025-04-10T15:30:00Z"
        assert data["cache_hit_rate_percent"] == 75.0


def test_export_diagnostics_default_path(temp_dir):
    """Test export_diagnostics with default path generation."""
    # Setup
    diagnostics_dir = temp_dir / "diagnostics"
    diagnostics_dir.mkdir()
    
    # Create a mock diagnostics function
    def get_diagnostics_func():
        return {"test": "data"}
    
    # Test with default path
    result = DiagnosticUtils.export_diagnostics(
        enable_diagnostics=True,
        diagnostics_dir=diagnostics_dir,
        get_diagnostics_func=get_diagnostics_func,
        path=None
    )
    
    # Check result
    assert result is True
    
    # Find generated file
    files = list(diagnostics_dir.glob("cache_diagnostics_*.json"))
    assert len(files) == 1
    
    # Check file content
    with open(files[0]) as f:
        data = json.load(f)
        assert data["test"] == "data"


def test_export_diagnostics_disabled(temp_dir):
    """Test export_diagnostics when diagnostics are disabled."""
    # Setup
    diagnostics_dir = temp_dir / "diagnostics"
    diagnostics_dir.mkdir()
    
    # Create a mock diagnostics function
    def get_diagnostics_func():
        return {"test": "data"}
    
    # Test with disabled diagnostics
    result = DiagnosticUtils.export_diagnostics(
        enable_diagnostics=False,
        diagnostics_dir=diagnostics_dir,
        get_diagnostics_func=get_diagnostics_func,
        path=None
    )
    
    # Check result
    assert result is False
    
    # Check no file was created
    files = list(diagnostics_dir.glob("*.json"))
    assert len(files) == 0


def test_export_diagnostics_error(temp_dir):
    """Test export_diagnostics error handling."""
    # Setup
    diagnostics_dir = temp_dir / "diagnostics"
    diagnostics_dir.mkdir()
    
    # Create a mock diagnostics function that raises an exception
    def get_diagnostics_func():
        raise Exception("Test error")
    
    # Test with error condition
    result = DiagnosticUtils.export_diagnostics(
        enable_diagnostics=True,
        diagnostics_dir=diagnostics_dir,
        get_diagnostics_func=get_diagnostics_func,
        path=temp_dir / "should_not_exist.json"
    )
    
    # Check result
    assert result is False
    
    # Check no file was created
    assert not (temp_dir / "should_not_exist.json").exists()


@pytest.fixture
def mock_consistency_checker():
    """Create a mock consistency checker."""
    mock = MagicMock()
    mock.check_bank_consistency.return_value = (True, [])
    mock.log_diagnostic_info = MagicMock()
    return mock


def test_perform_consistency_check(mock_consistency_checker):
    """Test perform_consistency_check for a specific bank."""
    # Setup test data
    cache = {
        "global:default": {"test.md": "content"},
        "project:test": {"readme.md": "content"}
    }
    
    # Test checking a specific bank
    result = DiagnosticUtils.perform_consistency_check(
        enable_diagnostics=True,
        consistency_checker=mock_consistency_checker,
        cache=cache,
        bank_type="global",
        bank_id="default"
    )
    
    # Check result structure
    assert "timestamp" in result
    assert "banks_checked" in result
    assert "banks_consistent" in result
    assert "banks_inconsistent" in result
    assert "details" in result
    
    # Check specific values
    assert result["banks_checked"] == 1
    assert result["banks_consistent"] == 1
    assert result["banks_inconsistent"] == 0
    assert "global:default" in result["details"]
    assert result["details"]["global:default"]["consistent"] is True
    
    # Verify mock calls
    mock_consistency_checker.check_bank_consistency.assert_called_once_with(
        "global", "default", {"test.md": "content"}
    )
    mock_consistency_checker.log_diagnostic_info.assert_not_called()


def test_perform_consistency_check_inconsistent(mock_consistency_checker):
    """Test perform_consistency_check with inconsistent banks."""
    # Setup test data
    cache = {
        "global:default": {"test.md": "content"},
        "project:test": {"readme.md": "content"}
    }
    
    # Configure mock to report inconsistency
    mock_consistency_checker.check_bank_consistency.return_value = (False, ["Issue 1", "Issue 2"])
    
    # Test checking a specific bank
    result = DiagnosticUtils.perform_consistency_check(
        enable_diagnostics=True,
        consistency_checker=mock_consistency_checker,
        cache=cache,
        bank_type="global",
        bank_id="default"
    )
    
    # Check specific values
    assert result["banks_checked"] == 1
    assert result["banks_consistent"] == 0
    assert result["banks_inconsistent"] == 1
    assert "global:default" in result["details"]
    assert result["details"]["global:default"]["consistent"] is False
    assert "issues" in result["details"]["global:default"]
    assert len(result["details"]["global:default"]["issues"]) == 2
    
    # Verify diagnostic info was logged
    mock_consistency_checker.log_diagnostic_info.assert_called_once()


def test_perform_consistency_check_all_banks(mock_consistency_checker):
    """Test perform_consistency_check for all banks."""
    # Setup test data
    cache = {
        "global:default": {"test.md": "content"},
        "project:test": {"readme.md": "content"},
        "code:repo": {"code.md": "content"}
    }
    
    # Configure mock to report mixed results
    mock_consistency_checker.check_bank_consistency.side_effect = [
        (True, []),             # global:default is consistent
        (False, ["Issue"]),     # project:test has an issue
        (True, [])              # code:repo is consistent
    ]
    
    # Test checking all banks
    result = DiagnosticUtils.perform_consistency_check(
        enable_diagnostics=True,
        consistency_checker=mock_consistency_checker,
        cache=cache,
        bank_type=None,
        bank_id=None
    )
    
    # Check specific values
    assert result["banks_checked"] == 3
    assert result["banks_consistent"] == 2
    assert result["banks_inconsistent"] == 1
    assert len(result["details"]) == 3
    
    # Verify each bank was checked
    assert mock_consistency_checker.check_bank_consistency.call_count == 3
    
    # Verify diagnostic info was logged for inconsistent bank
    assert mock_consistency_checker.log_diagnostic_info.call_count == 1


def test_perform_consistency_check_by_type(mock_consistency_checker):
    """Test perform_consistency_check for all banks of a specific type."""
    # Setup test data
    cache = {
        "global:default": {"test.md": "content"},
        "project:test1": {"readme.md": "content"},
        "project:test2": {"design.md": "content"},
        "code:repo": {"code.md": "content"}
    }
    
    # Configure mock to report mixed results
    mock_consistency_checker.check_bank_consistency.side_effect = [
        (True, []),             # project:test1 is consistent
        (False, ["Issue"]),     # project:test2 has an issue
    ]
    
    # Test checking all project banks
    result = DiagnosticUtils.perform_consistency_check(
        enable_diagnostics=True,
        consistency_checker=mock_consistency_checker,
        cache=cache,
        bank_type="project",
        bank_id=None
    )
    
    # Check specific values
    assert result["banks_checked"] == 2
    assert result["banks_consistent"] == 1
    assert result["banks_inconsistent"] == 1
    assert len(result["details"]) == 2
    assert "project:test1" in result["details"]
    assert "project:test2" in result["details"]
    assert "global:default" not in result["details"]
    assert "code:repo" not in result["details"]
    
    # Verify only project banks were checked
    assert mock_consistency_checker.check_bank_consistency.call_count == 2


def test_perform_consistency_check_error(mock_consistency_checker):
    """Test perform_consistency_check error handling."""
    # Setup test data
    cache = {
        "global:default": {"test.md": "content"}
    }
    
    # Configure mock to raise an exception
    mock_consistency_checker.check_bank_consistency.side_effect = Exception("Test error")
    
    # Test with error condition
    result = DiagnosticUtils.perform_consistency_check(
        enable_diagnostics=True,
        consistency_checker=mock_consistency_checker,
        cache=cache,
        bank_type="global",
        bank_id="default"
    )
    
    # Check specific values
    assert result["banks_checked"] == 1
    assert result["banks_consistent"] == 0
    assert result["banks_inconsistent"] == 1
    assert "global:default" in result["details"]
    assert result["details"]["global:default"]["consistent"] is False
    assert "error" in result["details"]["global:default"]
    assert "Test error" in result["details"]["global:default"]["error"]


def test_perform_consistency_check_disabled():
    """Test perform_consistency_check when diagnostics are disabled."""
    # Setup test data
    cache = {
        "global:default": {"test.md": "content"}
    }
    
    # Test with disabled diagnostics
    result = DiagnosticUtils.perform_consistency_check(
        enable_diagnostics=False,
        consistency_checker=None,
        cache=cache,
        bank_type="global",
        bank_id="default"
    )
    
    # Check result
    assert result == {"consistency_check_enabled": False}
