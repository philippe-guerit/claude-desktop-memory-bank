"""
Cache diagnostics implementation.

This module provides diagnostic methods for the cache manager.
"""

import logging
from typing import Dict, Any, Optional

from .diagnostic_utils import DiagnosticUtils

logger = logging.getLogger(__name__)

class CacheDiagnostics:
    """Provides diagnostic functionality for the cache manager."""
    
    @staticmethod
    def get_diagnostics(cache_manager) -> Dict[str, Any]:
        """Get diagnostic information about the cache manager.
        
        Args:
            cache_manager: The cache manager instance
            
        Returns:
            Dict containing diagnostic information
        """
        return DiagnosticUtils.get_diagnostics(
            cache_manager.enable_diagnostics,
            cache_manager.operation_counts,
            cache_manager.operation_timings,
            cache_manager.cache,
            cache_manager.pending_updates,
            cache_manager.error_history,
            cache_manager.start_time
        )
    
    @staticmethod
    def perform_consistency_check(
        cache_manager,
        bank_type: Optional[str] = None,
        bank_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform a consistency check on one or all banks.
        
        Args:
            cache_manager: The cache manager instance
            bank_type: Type of bank to check, or None to check all
            bank_id: ID of bank to check, or None to check all of given type
            
        Returns:
            Dict containing check results
        """
        if not cache_manager.enable_diagnostics:
            return {"consistency_check_enabled": False}
            
        return DiagnosticUtils.perform_consistency_check(
            cache_manager.enable_diagnostics,
            cache_manager.consistency_checker,
            cache_manager.cache,
            bank_type,
            bank_id
        )
    
    @staticmethod
    def export_diagnostics(
        cache_manager,
        path: Optional[str] = None
    ) -> bool:
        """Export diagnostic information to a file.
        
        Args:
            cache_manager: The cache manager instance
            path: Path to write the diagnostics file, or None to use default
            
        Returns:
            True if export was successful, False otherwise
        """
        return DiagnosticUtils.export_diagnostics(
            cache_manager.enable_diagnostics,
            cache_manager.diagnostics_dir,
            lambda: CacheDiagnostics.get_diagnostics(cache_manager),
            path
        )
    
    @staticmethod
    def dump_debug_memory(cache_manager) -> bool:
        """Write current cache state to cache_memory_dump.json if debug enabled.
        
        Args:
            cache_manager: The cache manager instance
            
        Returns:
            True if dump was successful, False otherwise
        """
        if not cache_manager.debug_memory_dump:
            return False
        
        # Write debug memory dump
        return cache_manager.file_sync.write_debug_dump(
            cache_manager.cache, 
            cache_manager.debug_dump_path
        )
