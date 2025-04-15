"""
Diagnostic utilities for cache manager.

This module provides diagnostic functionality for the cache manager.
"""

import json
import logging
import traceback
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class DiagnosticUtils:
    """Provides diagnostic functionality."""
    
    @staticmethod
    def get_diagnostics(
        enable_diagnostics: bool,
        operation_counts: Dict[str, int],
        operation_timings: Dict[str, List[float]],
        cache: Dict[str, Dict[str, str]],
        pending_updates: Dict[str, bool],
        error_history: List[Dict[str, Any]],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Get diagnostic information about the cache manager.
        
        Args:
            enable_diagnostics: Whether diagnostics are enabled
            operation_counts: Operation counts dictionary
            operation_timings: Operation timings dictionary
            cache: Cache dictionary
            pending_updates: Pending updates dictionary
            error_history: Error history list
            start_time: Start time of the cache manager
            
        Returns:
            Dict containing diagnostic information
        """
        if not enable_diagnostics:
            return {"diagnostics_enabled": False}
        
        # Calculate cache hit rate
        total_lookups = operation_counts.get("cache_hits", 0) + operation_counts.get("cache_misses", 0)
        cache_hit_rate = 0
        if total_lookups > 0:
            cache_hit_rate = (operation_counts.get("cache_hits", 0) / total_lookups) * 100
            
        # Calculate average operation times
        avg_timings = {}
        for op_type, timings in operation_timings.items():
            if timings:
                avg_timings[op_type] = sum(timings) / len(timings)
            else:
                avg_timings[op_type] = 0
                
        # Get cache size information
        cache_size = {}
        total_files = 0
        total_char_size = 0
        
        for key, content in cache.items():
            files_count = len(content)
            char_size = sum(len(c) for c in content.values())
            
            cache_size[key] = {
                "files_count": files_count,
                "character_size": char_size,
                "estimated_tokens": char_size // 4  # Rough estimate of token count
            }
            
            total_files += files_count
            total_char_size += char_size
            
        # Calculate uptime
        uptime_seconds = (datetime.now(UTC) - start_time).total_seconds()
        
        # Build diagnostics object
        diagnostics = {
            "timestamp": datetime.now(UTC).isoformat(),
            "uptime_seconds": uptime_seconds,
            "operation_counts": operation_counts.copy(),
            "cache_hit_rate_percent": cache_hit_rate,
            "average_timings_ms": avg_timings,
            "cache_size": {
                "banks_count": len(cache),
                "total_files": total_files,
                "total_character_size": total_char_size,
                "estimated_total_tokens": total_char_size // 4,
                "banks": cache_size
            },
            "pending_updates": len(pending_updates),
            "error_count": len(error_history),
            "recent_errors": error_history[-10:] if error_history else []
        }
        
        return diagnostics
    
    @staticmethod
    def perform_consistency_check(
        enable_diagnostics: bool,
        consistency_checker,
        cache: Dict[str, Dict[str, str]],
        bank_type: Optional[str] = None,
        bank_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform a consistency check on one or all banks.
        
        Args:
            enable_diagnostics: Whether diagnostics are enabled
            consistency_checker: Consistency checker instance
            cache: Cache dictionary
            bank_type: Type of bank to check, or None to check all
            bank_id: ID of bank to check, or None to check all of given type
            
        Returns:
            Dict containing check results
        """
        if not enable_diagnostics:
            return {"consistency_check_enabled": False}
            
        results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "banks_checked": 0,
            "banks_consistent": 0,
            "banks_inconsistent": 0,
            "details": {}
        }
        
        # Determine which banks to check
        if bank_type and bank_id:
            # Check specific bank
            key = f"{bank_type}:{bank_id}"
            banks_to_check = {key: (bank_type, bank_id)} if key in cache else {}
        elif bank_type:
            # Check all banks of given type
            banks_to_check = {}
            for key in cache:
                if key.startswith(f"{bank_type}:"):
                    parts = key.split(":", 1)
                    if len(parts) == 2:
                        banks_to_check[key] = (bank_type, parts[1])
        else:
            # Check all banks
            banks_to_check = {}
            for key in cache:
                parts = key.split(":", 1)
                if len(parts) == 2:
                    banks_to_check[key] = (parts[0], parts[1])
                    
        # Perform checks
        for key, (check_type, check_id) in banks_to_check.items():
            logger.info(f"Checking consistency for bank {key}")
            results["banks_checked"] += 1
            
            try:
                is_consistent, issues = consistency_checker.check_bank_consistency(
                    check_type, check_id, cache[key]
                )
                
                if is_consistent:
                    results["banks_consistent"] += 1
                    results["details"][key] = {"consistent": True}
                else:
                    results["banks_inconsistent"] += 1
                    results["details"][key] = {
                        "consistent": False,
                        "issues": issues
                    }
                    
                    # Log diagnostic information for inconsistent banks
                    consistency_checker.log_diagnostic_info(
                        check_type, check_id, "Consistency check failed during manual check"
                    )
            except Exception as e:
                logger.error(f"Error checking consistency for bank {key}: {e}")
                results["details"][key] = {
                    "consistent": False,
                    "error": str(e)
                }
                results["banks_inconsistent"] += 1
                
        return results
    
    @staticmethod
    def export_diagnostics(
        enable_diagnostics: bool,
        diagnostics_dir: Path,
        get_diagnostics_func,
        path: Optional[Path] = None
    ) -> bool:
        """Export diagnostic information to a file.
        
        Args:
            enable_diagnostics: Whether diagnostics are enabled
            diagnostics_dir: Diagnostics directory
            get_diagnostics_func: Function to get diagnostics
            path: Path to write the diagnostics file, or None to use default
            
        Returns:
            True if export was successful, False otherwise
        """
        if not enable_diagnostics:
            logger.warning("Cannot export diagnostics: diagnostics not enabled")
            return False
            
        try:
            # Get diagnostics
            diagnostics = get_diagnostics_func()
            
            # Determine output path
            if path is None:
                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                path = diagnostics_dir / f"cache_diagnostics_{timestamp}.json"
                
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(path, 'w') as f:
                json.dump(diagnostics, f, indent=2)
                
            logger.info(f"Exported diagnostics to {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export diagnostics: {e}\n{traceback.format_exc()}")
            return False
