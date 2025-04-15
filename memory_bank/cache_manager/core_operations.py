"""
Core operations for cache manager.

This module provides core operational functionality for the cache manager.
"""

import logging
import time
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class CoreOperations:
    """Provides core operational functionality for the cache manager."""
    
    @staticmethod
    def add_error(
        error_history: List[Dict[str, Any]],
        description: str, 
        severity: str = "error", 
        traceback_info: Optional[str] = None,
        enable_diagnostics: bool = False
    ) -> None:
        """Add an error to the error history.
        
        Args:
            error_history: Error history list to update
            description: Error description
            severity: Error severity
            traceback_info: Optional traceback information
            enable_diagnostics: Whether diagnostics are enabled
        """
        error = {
            "timestamp": datetime.now(UTC).isoformat(),
            "description": description,
            "severity": severity
        }
        
        if traceback_info and enable_diagnostics:
            error["traceback"] = traceback_info
            
        error_history.append(error)
        
        # Keep error history at a reasonable size
        if len(error_history) > 100:
            error_history = error_history[-100:]
    
    @staticmethod
    def update_bank_operation(
        bank_type: str, 
        bank_id: str, 
        content: str,
        cache: Dict[str, Dict[str, str]],
        pending_updates: Dict[str, bool],
        error_history: List[Dict[str, Any]],
        process_content_func,
        merge_content_func,
        is_large_update_func,
        file_sync,
        sync_to_disk_func,
        dump_debug_memory_func,
        operation_timings: Optional[Dict[str, List[float]]] = None,
        operation_counts: Optional[Dict[str, int]] = None,
        enable_diagnostics: bool = False,
        immediate_sync: bool = False
    ) -> Dict[str, Any]:
        """Update a bank's content in memory.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            content: New content to add
            cache: Cache dictionary to update
            pending_updates: Pending updates dictionary to update
            error_history: Error history list to update
            process_content_func: Function to process content
            merge_content_func: Function to merge content
            is_large_update_func: Function to check if update is large
            file_sync: File synchronizer instance
            sync_to_disk_func: Function to sync to disk
            dump_debug_memory_func: Function to dump debug memory
            operation_timings: Optional operation timings dictionary to update
            operation_counts: Optional operation counts dictionary to update
            enable_diagnostics: Whether diagnostics are enabled
            immediate_sync: Whether to synchronize to disk immediately
            
        Returns:
            Dict containing status information
        """
        start_time = time.time()
        
        if enable_diagnostics and operation_counts is not None:
            operation_counts["update_operations"] = operation_counts.get("update_operations", 0) + 1
        
        key = f"{bank_type}:{bank_id}"
        if key not in cache:
            # Use load_bank_from_disk_func to load the bank
            from memory_bank.storage.manager import StorageManager
            
            # Get the storage manager
            storage = StorageManager(file_sync.storage_root)
            
            # Get the bank
            bank = storage.get_bank(bank_type, bank_id)
            if not bank:
                # Create the bank if it doesn't exist
                bank = storage.create_bank(bank_type, bank_id)
            
            # Load content
            content_loaded = bank.load_all_content()
            
            # Store in cache
            cache[key] = content_loaded
            
            # Record the load time in the synchronizer
            file_sync.last_sync_time[key] = datetime.now(UTC)
        
        # Process the content and update in-memory cache
        try:
            updated_content = process_content_func(content, cache.get(key, {}), bank_type)
            cache[key] = merge_content_func(cache.get(key, {}), updated_content)
            pending_updates[key] = True
            
            # Schedule disk synchronization
            priority = immediate_sync or is_large_update_func(updated_content)
            file_sync.schedule_sync(bank_type, bank_id, priority=priority)
            
            # If it's a high-priority update, sync now
            if priority:
                sync_to_disk_func(bank_type, bank_id)
            
            # Write debug memory dump
            dump_debug_memory_func()
            
            # Record timing if diagnostics enabled
            if enable_diagnostics and operation_timings is not None and "update_ms" in operation_timings:
                duration_ms = (time.time() - start_time) * 1000
                if len(operation_timings["update_ms"]) >= 100:
                    operation_timings["update_ms"].pop(0)  # Remove oldest
                operation_timings["update_ms"].append(duration_ms)
                
                if duration_ms > 200:  # Log slow operations
                    logger.warning(f"Slow bank update for {bank_type}:{bank_id}: {duration_ms:.2f}ms")
                    
                logger.debug(f"Updated bank {bank_type}:{bank_id} in {duration_ms:.2f}ms")
            
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error updating cache for bank {bank_type}:{bank_id}: {e}")
            
            # Add error to history
            CoreOperations.add_error(
                error_history,
                f"Failed to update bank {bank_type}:{bank_id}: {str(e)}",
                "error",
                None,
                enable_diagnostics
            )
            
            # Error history is returned to client on next operation call
            return {"status": "error", "error": str(e)}
    
    @staticmethod
    def sync_all_pending_banks(
        pending_updates: Dict[str, bool],
        sync_to_disk_func
    ) -> Dict[str, bool]:
        """Synchronize all banks with pending updates to disk.
        
        Args:
            pending_updates: Pending updates dictionary
            sync_to_disk_func: Function to sync to disk
            
        Returns:
            Dict mapping bank keys to sync success status
        """
        results = {}
        
        for key in list(pending_updates.keys()):
            # Parse bank type and ID from key
            parts = key.split(":", 1)
            if len(parts) != 2:
                logger.error(f"Invalid bank key format: {key}")
                results[key] = False
                continue
                
            bank_type, bank_id = parts
            results[key] = sync_to_disk_func(bank_type, bank_id)
            
        return results
    
    @staticmethod
    def bank_get_operation(
        bank_type: str,
        bank_id: str,
        cache: Dict[str, Dict[str, str]],
        load_bank_func,
        operation_timings: Optional[Dict[str, List[float]]] = None,
        operation_counts: Optional[Dict[str, int]] = None,
        enable_diagnostics: bool = False
    ) -> Dict[str, str]:
        """Get a bank from the cache or load it if missing.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            cache: Cache dictionary
            load_bank_func: Function to load bank from disk
            operation_timings: Optional operation timings dictionary to update
            operation_counts: Optional operation counts dictionary to update
            enable_diagnostics: Whether diagnostics are enabled
            
        Returns:
            Dict containing bank content
        """
        start_time = time.time()
        key = f"{bank_type}:{bank_id}"
        
        if key not in cache:
            # Cache miss
            if enable_diagnostics and operation_counts is not None:
                operation_counts["cache_misses"] = operation_counts.get("cache_misses", 0) + 1
                operation_counts["load_operations"] = operation_counts.get("load_operations", 0) + 1
                
            logger.debug(f"Cache miss for bank {bank_type}:{bank_id}, loading from disk")
            
            # Load from disk and build cache
            load_bank_func(bank_type, bank_id)
        else:
            # Cache hit
            if enable_diagnostics and operation_counts is not None:
                operation_counts["cache_hits"] = operation_counts.get("cache_hits", 0) + 1
                
            logger.debug(f"Cache hit for bank {bank_type}:{bank_id}")
        
        # Record timing if diagnostics enabled
        if enable_diagnostics and operation_timings is not None and "load_ms" in operation_timings:
            duration_ms = (time.time() - start_time) * 1000
            if len(operation_timings["load_ms"]) >= 100:
                operation_timings["load_ms"].pop(0)  # Remove oldest
            operation_timings["load_ms"].append(duration_ms)
            
            if duration_ms > 100:  # Log slow operations
                logger.warning(f"Slow bank retrieval for {bank_type}:{bank_id}: {duration_ms:.2f}ms")
        
        return cache.get(key, {})
