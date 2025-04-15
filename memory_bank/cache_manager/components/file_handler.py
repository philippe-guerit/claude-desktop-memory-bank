"""
File handling functionality for the cache manager.

This module provides file operations for memory banks.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..file_sync import FileSynchronizer

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file operations for memory banks."""

    def __init__(self, cache_manager):
        """Initialize the file handler.
        
        Args:
            cache_manager: The cache manager instance
        """
        self.cache_manager = cache_manager
        self.file_sync = cache_manager.file_sync
        
    def sync_to_disk(
        self,
        bank_type: str,
        bank_id: str
    ) -> bool:
        """Synchronize a bank to disk.
        
        Args:
            bank_type: Type of bank
            bank_id: ID of the bank
            
        Returns:
            True if sync was successful, False otherwise
        """
        return self.cache_manager._sync_to_disk(bank_type, bank_id)
        
    def dump_debug_memory(self) -> bool:
        """Write current cache state to debug dump file.
        
        Returns:
            True if dump was successful, False otherwise
        """
        return self.cache_manager.dump_debug_memory()
        
    def write_debug_dump(
        self,
        cache_content: Dict[str, Dict[str, str]],
        debug_dump_path: Path
    ) -> bool:
        """Write debug dump to file.
        
        Args:
            cache_content: Cache content to dump
            debug_dump_path: Path to write the dump file
            
        Returns:
            True if dump was successful, False otherwise
        """
        return self.file_sync.write_debug_dump(cache_content, debug_dump_path)
