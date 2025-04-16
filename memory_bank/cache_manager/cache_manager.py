"""
Cache manager implementation.

This module provides the CacheManager class for managing in-memory cache of memory banks.
Enhanced with diagnostics and monitoring capabilities.
"""

import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List

from .file_sync import FileSynchronizer
from .bank_operations import BankOperations
from .content_processing import ContentProcessor
from .core_operations import CoreOperations
from .cache_diagnostics import CacheDiagnostics
from memory_bank.utils.recovery import ConsistencyChecker

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages the in-memory cache of memory banks."""
    
    _instance = None  # Singleton instance
    
    @classmethod
    def get_instance(cls, debug_memory_dump=True):
        """Get or create the singleton instance of CacheManager.
        
        Args:
            debug_memory_dump: Whether to enable memory dump for debugging
            
        Returns:
            CacheManager instance
        """
        if cls._instance is None:
            cls._instance = CacheManager(debug_memory_dump)
        return cls._instance
    
    def __init__(self, debug_memory_dump=True, sync_interval=60, enable_diagnostics=True):
        """Initialize the cache manager with optional debug dump support.
        
        Args:
            debug_memory_dump: Whether to enable memory dump for debugging
            sync_interval: Interval in seconds between automatic synchronizations
            enable_diagnostics: Whether to enable enhanced diagnostics
        """
        # If singleton already exists, return that instance
        if CacheManager._instance is not None:
            return
            
        self.cache = {}  # Dictionary mapping bank keys to content
        self.debug_memory_dump = debug_memory_dump
        self.pending_updates = {}  # Track updates pending disk synchronization
        self.error_history = []  # Store recent processing errors (max 100)
        self.enable_diagnostics = enable_diagnostics
        
        # Operation counters for diagnostics
        self.operation_counts = {
            "cache_hits": 0,
            "cache_misses": 0,
            "load_operations": 0,
            "update_operations": 0,
            "sync_operations": 0,
            "sync_failures": 0
        }
        
        # Performance timing tracking
        self.operation_timings = {
            "load_ms": [],
            "update_ms": [],
            "sync_ms": []
        }
        
        # Storage root path
        self.storage_root = Path.home() / ".claude-desktop" / "memory"
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Initialize file synchronizer
        self.file_sync = FileSynchronizer(sync_interval=sync_interval, storage_root=self.storage_root)
        self.file_sync.start()
        
        # Debug dump path
        self.debug_dump_path = self.storage_root / "cache_memory_dump.json"
        
        # Diagnostics directory
        self.diagnostics_dir = self.storage_root / "diagnostics"
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize consistency checker
        if enable_diagnostics:
            self.consistency_checker = ConsistencyChecker(self.storage_root)
        
        # Start time for uptime tracking
        self.start_time = datetime.now(UTC)
        
        # Enhanced logging
        logger.info(f"Cache Manager initialized with debug_memory_dump={debug_memory_dump}, " +
                    f"sync_interval={sync_interval}s, enable_diagnostics={enable_diagnostics}")
    
    def get_bank_key(self, bank_type: str, bank_id: str) -> str:
        """Generate a unique key for a bank.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            Bank key string
        """
        return f"{bank_type}:{bank_id}"
    
    def has_bank(self, bank_type: str, bank_id: str) -> bool:
        """Check if a bank exists in the cache.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            True if the bank exists in the cache, False otherwise
        """
        key = self.get_bank_key(bank_type, bank_id)
        exists = key in self.cache
        
        # Record cache hit/miss metrics if diagnostics enabled
        if self.enable_diagnostics:
            if exists:
                self.operation_counts["cache_hits"] += 1
            else:
                self.operation_counts["cache_misses"] += 1
                
        return exists
    
    def get_bank(self, bank_type: str, bank_id: str) -> Dict[str, str]:
        """Get a bank from the cache or load it if missing.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            Dict containing bank content
        """
        return CoreOperations.bank_get_operation(
            bank_type, bank_id,
            self.cache,
            self._load_bank_from_disk,
            self.operation_timings,
            self.operation_counts,
            self.enable_diagnostics
        )
    
    def update_bank(self, bank_type: str, bank_id: str, content: str, 
                    immediate_sync: bool = False) -> Dict[str, Any]:
        """Update a bank's content in memory.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            content: New content to add
            immediate_sync: Whether to synchronize to disk immediately
            
        Returns:
            Dict containing status information
        """
        return CoreOperations.update_bank_operation(
            bank_type, bank_id, content,
            self.cache,
            self.pending_updates,
            self.error_history,
            ContentProcessor.process_content,
            ContentProcessor.merge_content,
            BankOperations.is_large_update,
            self.file_sync,
            self._sync_to_disk,
            self.dump_debug_memory,
            self.operation_timings,
            self.operation_counts,
            self.enable_diagnostics,
            immediate_sync
        )
    
    def _load_bank_from_disk(self, bank_type: str, bank_id: str) -> None:
        """Load bank content from disk files into memory cache.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
        """
        BankOperations.load_bank_from_disk(
            bank_type, bank_id, 
            self.storage_root, 
            self.cache, 
            self.file_sync.last_sync_time, 
            self.error_history,
            self.enable_diagnostics,
            self.operation_counts
        )
        
        # Write debug memory dump
        self.dump_debug_memory()
    
    def _sync_to_disk(self, bank_type: str, bank_id: str) -> bool:
        """Synchronize a bank to disk.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            True if sync was successful, False otherwise
        """
        consistency_checker = self.consistency_checker if self.enable_diagnostics else None
        
        return BankOperations.sync_to_disk(
            bank_type, bank_id, 
            self.cache,
            self.file_sync, 
            self.pending_updates, 
            self.error_history,
            self.enable_diagnostics,
            self.operation_counts,
            self.operation_timings,
            consistency_checker
        )
    
    def sync_all_pending(self) -> Dict[str, bool]:
        """Synchronize all banks with pending updates to disk.
        
        Returns:
            Dict mapping bank keys to sync success status
        """
        return CoreOperations.sync_all_pending_banks(
            self.pending_updates,
            self._sync_to_disk
        )
    
    def get_error_history(self) -> list:
        """Return recent processing errors.
        
        Returns:
            List of recent error entries
        """
        return self.error_history[-10:] if self.error_history else []
        
    def close(self) -> None:
        """Close the cache manager and clean up resources."""
        logger.info("Closing cache manager")
        
        # Sync any pending changes
        if self.pending_updates:
            logger.info(f"Syncing {len(self.pending_updates)} pending updates before closing")
            self.sync_all_pending()
        
        # Stop the file synchronizer
        self.file_sync.stop()
        
        # Final debug memory dump
        if self.debug_memory_dump:
            self.dump_debug_memory()
            
        logger.info("Cache manager closed")
    
    def dump_debug_memory(self) -> bool:
        """Write current cache state to cache_memory_dump.json if debug enabled.
        
        Returns:
            True if dump was successful, False otherwise
        """
        return CacheDiagnostics.dump_debug_memory(self)
        
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get diagnostic information about the cache manager.
        
        Returns:
            Dict containing diagnostic information
        """
        return CacheDiagnostics.get_diagnostics(self)
        
    def perform_consistency_check(self, bank_type: Optional[str] = None, 
                                bank_id: Optional[str] = None) -> Dict[str, Any]:
        """Perform a consistency check on one or all banks.
        
        Args:
            bank_type: Type of bank to check, or None to check all
            bank_id: ID of bank to check, or None to check all of given type
            
        Returns:
            Dict containing check results
        """
        return CacheDiagnostics.perform_consistency_check(self, bank_type, bank_id)
    
    def export_diagnostics(self, path: Optional[Path] = None) -> bool:
        """Export diagnostic information to a file.
        
        Args:
            path: Path to write the diagnostics file, or None to use default
            
        Returns:
            True if export was successful, False otherwise
        """
        return CacheDiagnostics.export_diagnostics(self, path)
