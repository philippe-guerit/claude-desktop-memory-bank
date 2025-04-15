"""
Integration tests for diagnostics and monitoring.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from memory_bank.cache_manager import CacheManager
from memory_bank.utils.metrics import MetricsCollector
from memory_bank.utils.recovery import ConsistencyChecker


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def setup_environment(temp_dir):
    """Set up the test environment."""
    # Reset singletons
    CacheManager._instance = None
    MetricsCollector._instance = None
    
    # Create storage structure
    storage_root = temp_dir / ".claude-desktop" / "memory"
    global_dir = storage_root / "global" / "default"
    global_dir.mkdir(parents=True)
    
    # Create test files
    (global_dir / "context.md").write_text("Test context")
    (global_dir / "preferences.md").write_text("Test preferences")
    
    # Create diagnostics directory
    diag_dir = storage_root / "diagnostics"
    diag_dir.mkdir(parents=True)
    
    return {
        "storage_root": storage_root,
        "global_dir": global_dir,
        "diag_dir": diag_dir
    }


@patch.object(Path, 'home')
def test_diagnostic_export_integration(mock_home, setup_environment, temp_dir):
    """Test integration between CacheManager and diagnostic exports."""
    # Configure home path mock
    mock_home.return_value = temp_dir
    
    # Create a cache manager with the correct init parameters
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer'):
        # Get the singleton instance first
        cm = CacheManager.get_instance(debug_memory_dump=True)
        
        # Manually set enable_diagnostics to True
        cm.enable_diagnostics = True
        
        # Populate cache with test data
        cm.cache = {
            "global:default": {
                "context.md": "Updated context",
                "preferences.md": "Updated preferences"
            }
        }
        
        # Get diagnostics
        diagnostics = cm.get_diagnostics()
        
        # Check basic structure
        assert "timestamp" in diagnostics
        assert "operation_counts" in diagnostics
        assert "cache_size" in diagnostics
        
        # Export diagnostics
        success = cm.export_diagnostics()
        assert success is True
        
        # Check file was created
        export_files = list((temp_dir / ".claude-desktop" / "memory" / "diagnostics").glob("*.json"))
        assert len(export_files) > 0


@patch.object(Path, 'home')
def test_consistency_check_integration(mock_home, setup_environment, temp_dir):
    """Test integration between CacheManager and consistency checks."""
    # Configure home path mock
    mock_home.return_value = temp_dir
    
    # Create a cache manager with the correct init parameters
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer'):
        # Get the singleton instance first
        cm = CacheManager.get_instance(debug_memory_dump=True)
        
        # Manually set enable_diagnostics to True and create consistency checker
        cm.enable_diagnostics = True
        cm.consistency_checker = ConsistencyChecker(cm.storage_root)
        
        # Populate cache with consistent data
        cm.cache = {
            "global:default": {
                "context.md": "Test context",
                "preferences.md": "Test preferences"
            }
        }
        
        # Perform consistency check
        results = cm.perform_consistency_check("global", "default")
        
        # Check results
        assert "banks_checked" in results
        assert results["banks_checked"] == 1
        assert results["banks_consistent"] == 1
        
        # Now introduce inconsistency
        cm.cache["global:default"]["context.md"] = "Modified content"
        
        # Check again
        results = cm.perform_consistency_check("global", "default")
        
        # Should be inconsistent now
        assert results["banks_consistent"] == 0
        assert results["banks_inconsistent"] == 1


@patch.object(Path, 'home')
def test_metrics_integration(mock_home, setup_environment, temp_dir):
    """Test integration between CacheManager and MetricsCollector."""
    # Configure home path mock
    mock_home.return_value = temp_dir
    
    # Create instances
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer'):
        # Get the singleton instance first
        cm = CacheManager.get_instance(debug_memory_dump=True)
        
        # Manually set enable_diagnostics to True
        cm.enable_diagnostics = True
        
        # Create metrics collector
        mc = MetricsCollector.get_instance()
        
        # Record some operations
        mc.record_operation(
            operation_type="load",
            duration_ms=15.5,
            bank_type="global",
            bank_id="default",
            success=True
        )
        
        mc.record_cache_hit("global", "default")
        mc.record_cache_hit("global", "default")
        mc.record_cache_miss("global", "default")
        
        # Get metrics summary
        summary = mc.get_metrics_summary()
        
        # Check metrics
        assert summary["counters"]["load_operations"] == 1
        assert summary["counters"]["cache_hits"] == 2
        assert summary["counters"]["cache_misses"] == 1
        assert summary["cache_hit_rate"] == (2/3) * 100  # 66.67%
        
        # Export metrics
        export_path = temp_dir / "metrics_export.json"
        success = mc.export_metrics(export_path)
        
        # Check export
        assert success is True
        assert export_path.exists()


@patch.object(Path, 'home')
def test_recovery_action_integration(mock_home, setup_environment, temp_dir):
    """Test integration between recovery actions and metrics."""
    # Configure home path mock
    mock_home.return_value = temp_dir
    
    # Create instances
    with patch('memory_bank.cache_manager.cache_manager.FileSynchronizer'):
        # Get the singleton instance first
        cm = CacheManager.get_instance(debug_memory_dump=True)
        
        # Manually set enable_diagnostics to True
        cm.enable_diagnostics = True
        
        # Create metrics collector
        mc = MetricsCollector.get_instance()
        
        # Record a recovery action
        mc.record_recovery_action(
            bank_type="global",
            bank_id="default",
            action_type="consistency_fix",
            details="Fixed missing file",
            success=True
        )
        
        # Check recovery events in metrics
        assert mc.counters["recovery_actions"] == 1
        assert len(mc.metrics["recovery_events"]) == 1
        
        # Get metrics summary
        summary = mc.get_metrics_summary()
        
        # Check recovery events in summary
        assert len(summary["recent_recovery_events"]) == 1
        event = summary["recent_recovery_events"][0]
        assert event["bank"] == "global:default"
        assert event["action_type"] == "consistency_fix"
