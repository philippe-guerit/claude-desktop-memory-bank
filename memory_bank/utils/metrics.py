"""
Metrics collection and monitoring utilities for the memory bank system.

This module provides functionality for collecting and reporting metrics on
memory bank operations, as well as monitoring system health.
"""

import logging
import json
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import threading
import os

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and manages performance metrics for the memory bank system."""
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of MetricsCollector.
        
        Returns:
            MetricsCollector instance
        """
        if cls._instance is None:
            cls._instance = MetricsCollector()
        return cls._instance
    
    def __init__(self):
        """Initialize the metrics collector."""
        # If singleton already exists, return that instance
        if MetricsCollector._instance is not None:
            return
            
        # Metrics storage by category
        self.metrics = {
            "cache_operations": {},
            "file_operations": {},
            "content_processing": {},
            "recovery_events": [],
            "system_health": {
                "start_time": datetime.now(UTC).isoformat(),
                "last_check_time": datetime.now(UTC).isoformat(),
                "status": "healthy"
            }
        }
        
        # Operation counters
        self.counters = {
            "cache_hits": 0,
            "cache_misses": 0,
            "load_operations": 0,
            "update_operations": 0,
            "sync_operations": 0,
            "sync_failures": 0,
            "content_processing_llm": 0,
            "content_processing_rules": 0,
            "recovery_actions": 0,
            "consistency_checks": 0
        }
        
        # Performance timing data
        self.timings = {
            "load_time_ms": [],        # Time to load banks from disk
            "update_time_ms": [],      # Time to update banks in memory
            "sync_time_ms": [],        # Time to sync banks to disk
            "processing_time_ms": [],  # Time to process content
        }
        
        # Bank-specific metrics
        self.bank_metrics = {}  # Keyed by bank_type:bank_id
        
        # Thread safety
        self._lock = threading.RLock()
        
        logger.info("Metrics collector initialized")
    
    def record_operation(self, operation_type: str, duration_ms: float, 
                         bank_type: Optional[str] = None, 
                         bank_id: Optional[str] = None,
                         success: bool = True, 
                         details: Optional[Dict[str, Any]] = None) -> None:
        """Record a cache operation with timing information.
        
        Args:
            operation_type: Type of operation (load, update, sync, process)
            duration_ms: Duration of the operation in milliseconds
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
            success: Whether the operation was successful
            details: Additional details about the operation
        """
        with self._lock:
            timestamp = datetime.now(UTC).isoformat()
            
            # Increment counter
            counter_key = f"{operation_type}_operations"
            if counter_key in self.counters:
                self.counters[counter_key] += 1
            
            # Add failure counter if applicable
            if not success and f"{operation_type}_failures" in self.counters:
                self.counters[f"{operation_type}_failures"] += 1
            
            # Record timing
            timing_key = f"{operation_type}_time_ms"
            if timing_key in self.timings:
                self.timings[timing_key].append(duration_ms)
                # Keep only the last 100 timings
                if len(self.timings[timing_key]) > 100:
                    self.timings[timing_key] = self.timings[timing_key][-100:]
            
            # Categorize metrics by type
            category = "cache_operations"
            if operation_type in ["sync", "write", "read"]:
                category = "file_operations"
            elif operation_type in ["process", "analyze", "optimize"]:
                category = "content_processing"
            
            # Record operation details
            metric_entry = {
                "timestamp": timestamp,
                "duration_ms": duration_ms,
                "success": success
            }
            
            if bank_type and bank_id:
                metric_entry["bank"] = f"{bank_type}:{bank_id}"
                
                # Update bank-specific metrics
                bank_key = f"{bank_type}:{bank_id}"
                if bank_key not in self.bank_metrics:
                    self.bank_metrics[bank_key] = {
                        "operations_count": 0,
                        "failures_count": 0,
                        "last_operation_time": None
                    }
                
                self.bank_metrics[bank_key]["operations_count"] += 1
                if not success:
                    self.bank_metrics[bank_key]["failures_count"] += 1
                self.bank_metrics[bank_key]["last_operation_time"] = timestamp
            
            if details:
                metric_entry["details"] = details
            
            # Store the entry
            self.metrics[category][timestamp] = metric_entry
            
            # Keep metrics size reasonable by pruning old entries
            category_metrics = self.metrics[category]
            if len(category_metrics) > 1000:  # Keep only the most recent 1000 entries
                oldest_keys = sorted(category_metrics.keys())[:len(category_metrics) - 1000]
                for key in oldest_keys:
                    del category_metrics[key]
    
    def record_cache_hit(self, bank_type: str, bank_id: str) -> None:
        """Record a cache hit.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
        """
        with self._lock:
            self.counters["cache_hits"] += 1
            
            # Update bank-specific metrics
            bank_key = f"{bank_type}:{bank_id}"
            if bank_key not in self.bank_metrics:
                self.bank_metrics[bank_key] = {
                    "operations_count": 0,
                    "cache_hits": 0,
                    "cache_misses": 0
                }
            
            if "cache_hits" not in self.bank_metrics[bank_key]:
                self.bank_metrics[bank_key]["cache_hits"] = 0
            
            self.bank_metrics[bank_key]["cache_hits"] += 1
    
    def record_cache_miss(self, bank_type: str, bank_id: str) -> None:
        """Record a cache miss.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
        """
        with self._lock:
            self.counters["cache_misses"] += 1
            
            # Update bank-specific metrics
            bank_key = f"{bank_type}:{bank_id}"
            if bank_key not in self.bank_metrics:
                self.bank_metrics[bank_key] = {
                    "operations_count": 0,
                    "cache_hits": 0,
                    "cache_misses": 0
                }
            
            if "cache_misses" not in self.bank_metrics[bank_key]:
                self.bank_metrics[bank_key]["cache_misses"] = 0
            
            self.bank_metrics[bank_key]["cache_misses"] += 1
    
    def record_recovery_action(self, bank_type: str, bank_id: str, 
                               action_type: str, details: str, 
                               success: bool = True) -> None:
        """Record a recovery action.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
            action_type: Type of recovery action
            details: Details about the recovery action
            success: Whether the recovery action was successful
        """
        with self._lock:
            timestamp = datetime.now(UTC).isoformat()
            
            # Increment counter
            self.counters["recovery_actions"] += 1
            
            # Record recovery event
            event = {
                "timestamp": timestamp,
                "bank": f"{bank_type}:{bank_id}",
                "action_type": action_type,
                "details": details,
                "success": success
            }
            
            self.metrics["recovery_events"].append(event)
            
            # Keep only the last 100 recovery events
            if len(self.metrics["recovery_events"]) > 100:
                self.metrics["recovery_events"] = self.metrics["recovery_events"][-100:]
    
    def update_system_health(self, status: str = "healthy", details: Optional[Dict[str, Any]] = None) -> None:
        """Update system health status.
        
        Args:
            status: Health status ("healthy", "degraded", "error")
            details: Additional details about the health status
        """
        with self._lock:
            self.metrics["system_health"]["last_check_time"] = datetime.now(UTC).isoformat()
            self.metrics["system_health"]["status"] = status
            
            if details:
                self.metrics["system_health"]["details"] = details
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of collected metrics.
        
        Returns:
            Dict containing metrics summary
        """
        with self._lock:
            # Calculate timing statistics
            timing_stats = {}
            for timing_key, values in self.timings.items():
                if values:
                    timing_stats[timing_key] = {
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "count": len(values)
                    }
                else:
                    timing_stats[timing_key] = {
                        "min": 0,
                        "max": 0,
                        "avg": 0,
                        "count": 0
                    }
            
            # Calculate cache hit rate
            total_cache_lookups = self.counters["cache_hits"] + self.counters["cache_misses"]
            cache_hit_rate = (self.counters["cache_hits"] / total_cache_lookups) * 100 if total_cache_lookups > 0 else 0
            
            # Get top 5 most active banks
            top_banks = sorted(
                self.bank_metrics.items(), 
                key=lambda x: x[1].get("operations_count", 0), 
                reverse=True
            )[:5]
            
            # Build summary
            summary = {
                "counters": self.counters.copy(),
                "timing_stats": timing_stats,
                "cache_hit_rate": cache_hit_rate,
                "top_active_banks": [{
                    "bank": bank,
                    "operations": metrics.get("operations_count", 0),
                    "failures": metrics.get("failures_count", 0)
                } for bank, metrics in top_banks],
                "system_health": self.metrics["system_health"].copy(),
                "recent_recovery_events": self.metrics["recovery_events"][-5:] if self.metrics["recovery_events"] else []
            }
            
            return summary
    
    def export_metrics(self, path: Path) -> bool:
        """Export collected metrics to a JSON file.
        
        Args:
            path: Path to write the metrics file
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare export data
            export_data = {
                "timestamp": datetime.now(UTC).isoformat(),
                "counters": self.counters.copy(),
                "bank_metrics": self.bank_metrics.copy(),
                "system_health": self.metrics["system_health"].copy(),
                "timings": self.timings.copy(),
                "recovery_events": self.metrics["recovery_events"].copy()
            }
            
            # Write to file
            with open(path, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info(f"Metrics exported to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export metrics to {path}: {e}")
            return False
    
    def reset_counters(self) -> None:
        """Reset operation counters while preserving other metrics."""
        with self._lock:
            for counter in self.counters:
                self.counters[counter] = 0
            
            logger.info("Metrics counters reset")
    
    def clear_all_metrics(self) -> None:
        """Clear all collected metrics."""
        with self._lock:
            self.metrics = {
                "cache_operations": {},
                "file_operations": {},
                "content_processing": {},
                "recovery_events": [],
                "system_health": {
                    "start_time": self.metrics["system_health"]["start_time"],
                    "last_check_time": datetime.now(UTC).isoformat(),
                    "status": "healthy"
                }
            }
            
            for counter in self.counters:
                self.counters[counter] = 0
                
            for timing_key in self.timings:
                self.timings[timing_key] = []
                
            self.bank_metrics = {}
            
            logger.info("All metrics cleared")
