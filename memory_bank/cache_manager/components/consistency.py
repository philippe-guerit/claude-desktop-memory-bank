"""
Consistency checking functionality for the cache manager.

This module provides consistency checking and validation for memory banks.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from memory_bank.utils.recovery import ConsistencyChecker

logger = logging.getLogger(__name__)


class ConsistencyManager:
    """Manages consistency checking for memory banks."""

    def __init__(self, cache_manager):
        """Initialize the consistency manager.
        
        Args:
            cache_manager: The cache manager instance
        """
        self.cache_manager = cache_manager
        self.consistency_checker = cache_manager.consistency_checker
        
    def check_bank_consistency(
        self,
        bank_type: str,
        bank_id: str,
        cache_content: Dict[str, str]
    ) -> Tuple[bool, List[str]]:
        """Check if a memory bank is consistent between cache and disk.
        
        Args:
            bank_type: Type of memory bank
            bank_id: ID of the memory bank
            cache_content: Current cache content for the bank
            
        Returns:
            Tuple of (is_consistent, list of inconsistencies)
        """
        return self.consistency_checker.check_bank_consistency(
            bank_type,
            bank_id,
            cache_content
        )
        
    def log_diagnostic_info(
        self,
        bank_type: str,
        bank_id: str,
        issue: str
    ) -> None:
        """Log detailed diagnostic information about a bank.
        
        Args:
            bank_type: Type of memory bank
            bank_id: ID of the memory bank
            issue: Description of the issue
        """
        self.consistency_checker.log_diagnostic_info(
            bank_type,
            bank_id,
            issue
        )
