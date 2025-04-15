"""
Tests for the MetricsCollector class.
"""

import json
import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from memory_bank.utils.metrics import MetricsCollector


@pytest.fixture
def reset_singleton():
    """Reset the MetricsCollector singleton before each test."""
    MetricsCollector._instance = None
    yield
    MetricsCollector._instance = None


@pytest.fixture
def metrics_collector(reset_singleton):
    """Create a MetricsCollector instance for testing."""
    return MetricsCollector.get_instance()


@pytest.fixture
def populated_collector(reset_singleton):
    """Create a MetricsCollector with pre-populated data."""
    collector = MetricsCollector.get_instance()
    
    # Add test data
    collector.counters["cache_hits"] = 75
    collector.counters["cache_misses"] = 25
    collector.timings["load_time_ms"] = [10.5, 20.3, 15.8]
    collector.bank_metrics = {
        "global:default": {"operations_count": 50, "failures_count": 5},
        "project:test": {"operations_count": 30, "failures_count": 2}
    }
    
    return collector


def test_singleton_pattern(reset_singleton):
    """Test that MetricsCollector follows the singleton pattern."""
    mc1 = MetricsCollector.get_instance()
    mc2 = MetricsCollector.get_instance()
    assert mc1 is mc2


def test_record_operation(metrics_collector):
    """Test record_operation functionality."""
    metrics_collector.record_operation(
        operation_type="load",
        duration_ms=15.5,
        bank_type="global",
        bank_id="default",
        success=True
    )
    
    # Check counter incremented
    assert metrics_collector.counters["load_operations"] == 1
    
    # Check timing recorded
    assert 15.5 in metrics_collector.timings["load_time_ms"]
    
    # Check bank-specific metrics
    bank_key = "global:default"
    assert bank_key in metrics_collector.bank_metrics
    assert metrics_collector.bank_metrics[bank_key]["operations_count"] == 1


def test_record_operation_failure(metrics_collector):
    """Test record_operation with failure."""
    metrics_collector.record_operation(
        operation_type="sync",
        duration_ms=25.0,
        bank_type="global",
        bank_id="default",
        success=False
    )
    
    # Check counters
    assert metrics_collector.counters["sync_operations"] == 1
    assert metrics_collector.counters["sync_failures"] == 1
    
    # Check bank-specific metrics
    bank_key = "global:default"
    assert metrics_collector.bank_metrics[bank_key]["failures_count"] == 1


def test_record_cache_hit(metrics_collector):
    """Test record_cache_hit functionality."""
    metrics_collector.record_cache_hit("global", "default")
    
    # Check counter
    assert metrics_collector.counters["cache_hits"] == 1
    
    # Check bank-specific metrics
    bank_key = "global:default"
    assert metrics_collector.bank_metrics[bank_key]["cache_hits"] == 1


def test_record_cache_miss(metrics_collector):
    """Test record_cache_miss functionality."""
    metrics_collector.record_cache_miss("global", "default")
    
    # Check counter
    assert metrics_collector.counters["cache_misses"] == 1
    
    # Check bank-specific metrics
    bank_key = "global:default"
    assert metrics_collector.bank_metrics[bank_key]["cache_misses"] == 1


def test_record_recovery_action(metrics_collector):
    """Test record_recovery_action functionality."""
    metrics_collector.record_recovery_action(
        bank_type="global",
        bank_id="default",
        action_type="consistency_fix",
        details="Fixed inconsistency",
        success=True
    )
    
    # Check counter
    assert metrics_collector.counters["recovery_actions"] == 1
    
    # Check recovery events
    assert len(metrics_collector.metrics["recovery_events"]) == 1
    event = metrics_collector.metrics["recovery_events"][0]
    assert event["bank"] == "global:default"
    assert event["action_type"] == "consistency_fix"


def test_update_system_health(metrics_collector):
    """Test update_system_health functionality."""
    metrics_collector.update_system_health(
        status="degraded",
        details={"reason": "High error rate"}
    )
    
    # Check system health
    health = metrics_collector.metrics["system_health"]
    assert health["status"] == "degraded"
    assert health["details"]["reason"] == "High error rate"


def test_get_metrics_summary(populated_collector):
    """Test get_metrics_summary functionality."""
    summary = populated_collector.get_metrics_summary()
    
    # Check summary structure
    assert "counters" in summary
    assert "timing_stats" in summary
    assert "cache_hit_rate" in summary
    assert "top_active_banks" in summary
    assert "system_health" in summary
    
    # Check specific values
    assert summary["counters"]["cache_hits"] == 75
    assert summary["counters"]["cache_misses"] == 25
    assert summary["cache_hit_rate"] == 75.0  # 75/(75+25) * 100


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


def test_export_metrics(populated_collector, temp_dir):
    """Test export_metrics functionality."""
    export_path = temp_dir / "test_metrics.json"
    
    # Export metrics
    result = populated_collector.export_metrics(export_path)
    
    # Check result
    assert result is True
    assert export_path.exists()
    
    # Check file content
    with open(export_path) as f:
        data = json.load(f)
        assert "counters" in data
        assert "bank_metrics" in data
        assert data["counters"]["cache_hits"] == 75


def test_reset_counters(populated_collector):
    """Test reset_counters functionality."""
    # Verify counters have values before reset
    assert populated_collector.counters["cache_hits"] == 75
    
    # Reset counters
    populated_collector.reset_counters()
    
    # Check all counters are zero
    for counter, value in populated_collector.counters.items():
        assert value == 0
    
    # Check other metrics are preserved
    assert len(populated_collector.timings["load_time_ms"]) > 0
    assert len(populated_collector.bank_metrics) > 0


def test_clear_all_metrics(populated_collector):
    """Test clear_all_metrics functionality."""
    # Clear all metrics
    populated_collector.clear_all_metrics()
    
    # Check counters are zero
    for counter, value in populated_collector.counters.items():
        assert value == 0
    
    # Check timings are empty
    for timing_key, values in populated_collector.timings.items():
        assert len(values) == 0
    
    # Check bank metrics are empty
    assert len(populated_collector.bank_metrics) == 0
    
    # Check system health preserved but reset
    assert "start_time" in populated_collector.metrics["system_health"]
    assert populated_collector.metrics["system_health"]["status"] == "healthy"
