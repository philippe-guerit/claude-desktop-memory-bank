"""
Bank operations for cache manager.

This module provides functionality for bank loading and updating operations.
"""

import logging
import time
import traceback
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class BankOperations:
    """Handles bank loading and updating operations."""
    
    @staticmethod
    def load_bank_from_disk(bank_type: str, bank_id: str, storage_root: Path, 
                           cache: Dict[str, Dict[str, str]], 
                           file_sync_last_sync_time: Dict[str, datetime],
                           error_history: List[Dict[str, Any]],
                           enable_diagnostics: bool,
                           operation_counts: Optional[Dict[str, int]] = None) -> None:
        """Load bank content from disk files into memory cache.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            storage_root: Root path of storage
            cache: Cache dictionary to update
            file_sync_last_sync_time: Last sync time dictionary to update
            error_history: Error history list to update
            enable_diagnostics: Whether diagnostics are enabled
            operation_counts: Optional operation counts dictionary to update
        """
        logger.info(f"Loading bank {bank_type}:{bank_id} from disk")
        
        try:
            # Import here to avoid circular imports
            from memory_bank.storage.manager import StorageManager
            
            # Get the storage manager
            storage = StorageManager(storage_root)
            
            # Get the bank
            bank = storage.get_bank(bank_type, bank_id)
            if not bank:
                # Create the bank if it doesn't exist
                bank = storage.create_bank(bank_type, bank_id)
            
            # Load content
            content = bank.load_all_content()
            
            # Store in cache
            key = f"{bank_type}:{bank_id}"
            cache[key] = content
            
            # Record the load time
            file_sync_last_sync_time[key] = datetime.now(UTC)
            
            # Update operation counts if provided
            if enable_diagnostics and operation_counts is not None:
                operation_counts["load_operations"] = operation_counts.get("load_operations", 0) + 1
            
            logger.info(f"Successfully loaded bank {bank_type}:{bank_id} from disk")
            
        except Exception as e:
            logger.error(f"Error loading bank {bank_type}:{bank_id} from disk: {e}")
            
            # Create an empty cache entry to prevent repeated load attempts
            key = f"{bank_type}:{bank_id}"
            cache[key] = {}
            
            # Add to error history
            error = {
                "timestamp": datetime.now(UTC).isoformat(),
                "description": f"Failed to load bank {bank_type}:{bank_id} from disk: {str(e)}",
                "severity": "error"
            }
            error_history.append(error)
            
            # Keep error history at a reasonable size
            if len(error_history) > 100:
                error_history = error_history[-100:]
    
    @staticmethod
    def sync_to_disk(bank_type: str, bank_id: str, cache: Dict[str, Dict[str, str]],
                    file_sync, pending_updates: Dict[str, bool],
                    error_history: List[Dict[str, Any]],
                    enable_diagnostics: bool,
                    operation_counts: Optional[Dict[str, int]] = None,
                    operation_timings: Optional[Dict[str, List[float]]] = None,
                    consistency_checker=None) -> bool:
        """Synchronize a bank to disk.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            cache: Cache dictionary
            file_sync: File synchronizer instance
            pending_updates: Pending updates dictionary to update
            error_history: Error history list to update
            enable_diagnostics: Whether diagnostics are enabled
            operation_counts: Optional operation counts dictionary to update
            operation_timings: Optional operation timings dictionary to update
            consistency_checker: Optional consistency checker instance
            
        Returns:
            True if sync was successful, False otherwise
        """
        start_time = time.time()
        
        if enable_diagnostics and operation_counts is not None:
            operation_counts["sync_operations"] = operation_counts.get("sync_operations", 0) + 1
        
        key = f"{bank_type}:{bank_id}"
        if key not in cache:
            logger.warning(f"Cannot sync bank {key} to disk: not in cache")
            return False
        
        try:
            # Determine bank root path
            bank_root = BankOperations.get_bank_root_path(bank_type, bank_id, file_sync.storage_root)
            
            # Sync to disk using the file synchronizer
            success = file_sync.sync_to_disk(
                bank_type, bank_id, cache[key], bank_root
            )
            
            if success:
                # Clear pending update flag
                pending_updates.pop(key, None)
                logger.info(f"Successfully synced bank {key} to disk")
                
                # Check consistency if diagnostics enabled
                if enable_diagnostics and consistency_checker:
                    consistent, issues = consistency_checker.check_bank_consistency(
                        bank_type, bank_id, cache[key]
                    )
                    if not consistent:
                        logger.warning(f"Consistency check after sync failed for {key}: {issues}")
                        # Log detailed diagnostics
                        consistency_checker.log_diagnostic_info(
                            bank_type, bank_id, "Post-sync consistency check failed"
                        )
            else:
                logger.error(f"Failed to sync bank {key} to disk")
                if enable_diagnostics and operation_counts is not None:
                    operation_counts["sync_failures"] = operation_counts.get("sync_failures", 0) + 1
            
            # Record timing if diagnostics enabled
            if enable_diagnostics and operation_timings is not None:
                duration_ms = (time.time() - start_time) * 1000
                if "sync_ms" in operation_timings:
                    if len(operation_timings["sync_ms"]) >= 100:
                        operation_timings["sync_ms"].pop(0)  # Remove oldest
                    operation_timings["sync_ms"].append(duration_ms)
                
                if duration_ms > 300:  # Log slow sync operations
                    logger.warning(f"Slow disk sync for {bank_type}:{bank_id}: {duration_ms:.2f}ms")
                    
                logger.debug(f"Synced bank {bank_type}:{bank_id} to disk in {duration_ms:.2f}ms")
                
            return success
            
        except Exception as e:
            logger.error(f"Error syncing bank {key} to disk: {e}")
            
            if enable_diagnostics and operation_counts is not None:
                operation_counts["sync_failures"] = operation_counts.get("sync_failures", 0) + 1
            
            # Add to error history
            error = {
                "timestamp": datetime.now(UTC).isoformat(),
                "description": f"Failed to sync bank {key} to disk: {str(e)}",
                "severity": "error",
                "traceback": traceback.format_exc() if enable_diagnostics else None
            }
            error_history.append(error)
            
            # Keep error history at a reasonable size
            if len(error_history) > 100:
                error_history = error_history[-100:]
            
            # Log diagnostic information if enabled
            if enable_diagnostics and consistency_checker:
                try:
                    consistency_checker.log_diagnostic_info(
                        bank_type, bank_id, f"Sync failed: {str(e)}"
                    )
                except Exception as diag_e:
                    logger.error(f"Error logging diagnostic information: {diag_e}")
                
            return False
    
    @staticmethod
    def get_bank_root_path(bank_type: str, bank_id: str, storage_root: Path) -> Path:
        """Get the root path for a bank on disk.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            storage_root: Root path of storage
            
        Returns:
            Path to the bank's root directory
        """
        if bank_type == "global":
            return storage_root / "global" / bank_id
        elif bank_type == "project":
            return storage_root / "projects" / bank_id
        elif bank_type == "code":
            return storage_root / "code" / bank_id
        else:
            raise ValueError(f"Unknown bank type: {bank_type}")
    
    @staticmethod
    def is_large_update(content: Dict[str, str]) -> bool:
        """Determine if this is a large update that should trigger immediate sync.
        
        Args:
            content: New content being added
            
        Returns:
            True if this is a large update, False otherwise
        """
        # Calculate the total size of the update
        total_size = sum(len(c) for c in content.values())
        
        # Consider updates over 2KB as large
        return total_size > 2048
