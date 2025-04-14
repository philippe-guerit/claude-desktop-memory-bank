"""
Cache manager implementation.

This module provides the CacheManager class for managing in-memory cache of memory banks.
"""

import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import threading
import time

from .file_sync import FileSynchronizer

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
    
    def __init__(self, debug_memory_dump=True, sync_interval=60):
        """Initialize the cache manager with optional debug dump support.
        
        Args:
            debug_memory_dump: Whether to enable memory dump for debugging
            sync_interval: Interval in seconds between automatic synchronizations
        """
        # If singleton already exists, return that instance
        if CacheManager._instance is not None:
            return
            
        self.cache = {}  # Dictionary mapping bank keys to content
        self.debug_memory_dump = debug_memory_dump
        self.pending_updates = {}  # Track updates pending disk synchronization
        self.error_history = []  # Store recent processing errors (max 100)
        
        # Initialize file synchronizer
        self.file_sync = FileSynchronizer(sync_interval=sync_interval)
        self.file_sync.start()
        
        # Storage root path
        self.storage_root = Path.home() / ".claude-desktop" / "memory"
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Debug dump path
        self.debug_dump_path = self.storage_root / "cache_memory_dump.json"
        
        logger.info(f"Cache Manager initialized with debug_memory_dump={debug_memory_dump}, " +
                    f"sync_interval={sync_interval}s")
    
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
        return self.get_bank_key(bank_type, bank_id) in self.cache
    
    def get_bank(self, bank_type: str, bank_id: str) -> Dict[str, str]:
        """Get a bank from the cache or load it if missing.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            Dict containing bank content
        """
        key = self.get_bank_key(bank_type, bank_id)
        if key not in self.cache:
            # Load from disk and build cache
            self._load_bank_from_disk(bank_type, bank_id)
        
        return self.cache.get(key, {})
    
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
        key = self.get_bank_key(bank_type, bank_id)
        if key not in self.cache:
            self._load_bank_from_disk(bank_type, bank_id)
        
        # Process the content and update in-memory cache
        try:
            updated_content = self._process_content(content, self.cache.get(key, {}))
            self.cache[key] = self._merge_content(self.cache.get(key, {}), updated_content)
            self.pending_updates[key] = True
            
            # Schedule disk synchronization
            priority = immediate_sync or self._is_large_update(updated_content)
            self.file_sync.schedule_sync(bank_type, bank_id, priority=priority)
            
            # If it's a high-priority update, sync now
            if priority:
                self._sync_to_disk(bank_type, bank_id)
            
            # Write debug memory dump
            self.dump_debug_memory()
            
            return {"status": "success"}
            
        except Exception as e:
            error = {
                "timestamp": datetime.now(UTC).isoformat(),
                "description": str(e),
                "severity": "error"
            }
            self.error_history.append(error)
            
            # Keep error history at a reasonable size
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
            
            logger.error(f"Error updating cache for bank {bank_type}:{bank_id}: {e}")
            
            # Error history is returned to client on next operation call
            return {"status": "error", "error": str(e)}
    
    def _is_large_update(self, content: Dict[str, str]) -> bool:
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
    
    def _load_bank_from_disk(self, bank_type: str, bank_id: str) -> None:
        """Load bank content from disk files into memory cache.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
        """
        logger.info(f"Loading bank {bank_type}:{bank_id} from disk")
        
        try:
            # Import here to avoid circular imports
            from memory_bank.storage.manager import StorageManager
            
            # Get the storage manager
            storage = StorageManager(self.storage_root)
            
            # Get the bank
            bank = storage.get_bank(bank_type, bank_id)
            if not bank:
                # Create the bank if it doesn't exist
                bank = storage.create_bank(bank_type, bank_id)
            
            # Load content
            content = bank.load_all_content()
            
            # Store in cache
            key = self.get_bank_key(bank_type, bank_id)
            self.cache[key] = content
            
            # Record the load time in the synchronizer
            self.file_sync.last_sync_time[key] = datetime.now(UTC)
            
            # Write debug memory dump
            self.dump_debug_memory()
            
            logger.info(f"Successfully loaded bank {bank_type}:{bank_id} from disk")
            
        except Exception as e:
            logger.error(f"Error loading bank {bank_type}:{bank_id} from disk: {e}")
            
            # Create an empty cache entry to prevent repeated load attempts
            key = self.get_bank_key(bank_type, bank_id)
            self.cache[key] = {}
            
            # Add to error history
            error = {
                "timestamp": datetime.now(UTC).isoformat(),
                "description": f"Failed to load bank {bank_type}:{bank_id} from disk: {str(e)}",
                "severity": "error"
            }
            self.error_history.append(error)
            
            # Keep error history at a reasonable size
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
    
    def _process_content(self, content: str, existing_cache: Dict[str, str]) -> Dict[str, str]:
        """Process content using LLM-based or rule-based approach.
        
        Args:
            content: New content to process
            existing_cache: Existing cache content
            
        Returns:
            Processed content as a dict mapping file paths to content
        """
        try:
            # For Phase 1, just use rule-based processing
            # LLM-based processing will be implemented in a later phase
            return self._process_with_rules(content, existing_cache)
            
        except Exception as e:
            logger.error(f"Error processing content: {e}")
            raise
    
    def _process_with_rules(self, content: str, existing_cache: Dict[str, str]) -> Dict[str, str]:
        """Process content with rule-based approach.
        
        Args:
            content: New content to process
            existing_cache: Existing cache content
            
        Returns:
            Processed content as a dict mapping file paths to content
        """
        # In Phase 1, return a simple structure with context.md as the target
        # This will be enhanced in Phase 5 with proper content processing
        return {"context.md": content}
    
    def _merge_content(self, existing_content: Dict[str, str], new_content: Dict[str, str]) -> Dict[str, str]:
        """Merge new content with existing content.
        
        Args:
            existing_content: Existing content in the cache
            new_content: New content to merge
            
        Returns:
            Merged content
        """
        result = existing_content.copy()
        
        # For each file in new content
        for file_path, content in new_content.items():
            if file_path in result:
                # Append to existing file
                result[file_path] = result[file_path] + "\n\n" + content
            else:
                # Create new file
                result[file_path] = content
        
        return result
    
    def _sync_to_disk(self, bank_type: str, bank_id: str) -> bool:
        """Synchronize a bank to disk.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            True if sync was successful, False otherwise
        """
        key = self.get_bank_key(bank_type, bank_id)
        if key not in self.cache:
            logger.warning(f"Cannot sync bank {key} to disk: not in cache")
            return False
        
        try:
            # Determine bank root path
            bank_root = self._get_bank_root_path(bank_type, bank_id)
            
            # Sync to disk using the file synchronizer
            success = self.file_sync.sync_to_disk(
                bank_type, bank_id, self.cache[key], bank_root
            )
            
            if success:
                # Clear pending update flag
                self.pending_updates.pop(key, None)
                logger.info(f"Successfully synced bank {key} to disk")
            else:
                logger.error(f"Failed to sync bank {key} to disk")
                
            return success
            
        except Exception as e:
            logger.error(f"Error syncing bank {key} to disk: {e}")
            
            # Add to error history
            error = {
                "timestamp": datetime.now(UTC).isoformat(),
                "description": f"Failed to sync bank {key} to disk: {str(e)}",
                "severity": "error"
            }
            self.error_history.append(error)
            
            # Keep error history at a reasonable size
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
                
            return False
    
    def sync_all_pending(self) -> Dict[str, bool]:
        """Synchronize all banks with pending updates to disk.
        
        Returns:
            Dict mapping bank keys to sync success status
        """
        results = {}
        
        for key in list(self.pending_updates.keys()):
            # Parse bank type and ID from key
            parts = key.split(":", 1)
            if len(parts) != 2:
                logger.error(f"Invalid bank key format: {key}")
                results[key] = False
                continue
                
            bank_type, bank_id = parts
            results[key] = self._sync_to_disk(bank_type, bank_id)
            
        return results
    
    def _get_bank_root_path(self, bank_type: str, bank_id: str) -> Path:
        """Get the root path for a bank on disk.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            
        Returns:
            Path to the bank's root directory
        """
        if bank_type == "global":
            return self.storage_root / "global" / bank_id
        elif bank_type == "project":
            return self.storage_root / "projects" / bank_id
        elif bank_type == "code":
            return self.storage_root / "code" / bank_id
        else:
            raise ValueError(f"Unknown bank type: {bank_type}")
    
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
        if not self.debug_memory_dump:
            return False
        
        # Write debug memory dump
        return self.file_sync.write_debug_dump(self.cache, self.debug_dump_path)
