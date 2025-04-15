"""
Diagnostic functionality for the cache manager.

This module provides a unified interface for diagnostics features.
"""

import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..cache_diagnostics import CacheDiagnostics

logger = logging.getLogger(__name__)


class DiagnosticsManager:
    """Provides diagnostic functionality for the cache manager."""

    def __init__(self, cache_manager):
        """Initialize the diagnostics manager.
        
        Args:
            cache_manager: The cache manager instance
        """
        self.cache_manager = cache_manager
        
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about the cache manager.
        
        Returns:
            Dict containing diagnostic information
        """
        return CacheDiagnostics.get_diagnostics(self.cache_manager)
        
    def perform_consistency_check(
        self,
        bank_type: Optional[str] = None,
        bank_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform a consistency check on one or all banks.
        
        Args:
            bank_type: Type of bank to check, or None to check all
            bank_id: ID of bank to check, or None to check all of given type
            
        Returns:
            Dict containing check results
        """
        return CacheDiagnostics.perform_consistency_check(
            self.cache_manager,
            bank_type,
            bank_id
        )
    
    def export_diagnostics(
        self,
        path: Optional[Path] = None
    ) -> bool:
        """Export diagnostic information to a file.
        
        Args:
            path: Path to write the diagnostics file, or None to use default
            
        Returns:
            True if export was successful, False otherwise
        """
        return CacheDiagnostics.export_diagnostics(
            self.cache_manager,
            path
        )
