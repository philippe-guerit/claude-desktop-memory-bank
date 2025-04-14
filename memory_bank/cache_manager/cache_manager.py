"""
Cache manager implementation.

This module provides the CacheManager class for managing in-memory cache of memory banks.
"""

import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, Optional
from queue import Queue
import threading

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
    
    def __init__(self, debug_memory_dump=True):
        """Initialize the cache manager with optional debug dump support.
        
        Args:
            debug_memory_dump: Whether to enable memory dump for debugging
        """
        # If singleton already exists, return that instance
        if CacheManager._instance is not None:
            return
            
        self.cache = {}  # Dictionary mapping bank keys to content
        self.debug_memory_dump = debug_memory_dump
        self.last_sync_time = {}  # Track last disk synchronization by bank
        self.pending_updates = {}  # Track updates pending disk synchronization
        self.error_history = []  # Store recent processing errors
        self.sync_queue = Queue()  # FIFO queue for synchronization operations
        self._sync_thread = None  # Background thread for disk synchronization
        
        logger.info(f"Cache Manager initialized with debug_memory_dump={debug_memory_dump}")
    
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
    
    def update_bank(self, bank_type: str, bank_id: str, content: str) -> Dict[str, Any]:
        """Update a bank's content in memory.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
            content: New content to add
            
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
            self._schedule_disk_sync(bank_type, bank_id)
            
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
            
            logger.error(f"Error updating cache for bank {bank_type}:{bank_id}: {e}")
            
            # Error history is returned to client on next operation call
            return {"status": "error", "error": str(e)}
    
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
            storage_root = Path.home() / ".claude-desktop" / "memory"
            storage = StorageManager(storage_root)
            
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
            self.last_sync_time[key] = datetime.now(UTC)
            
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
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "description": f"Failed to load bank {bank_type}:{bank_id} from disk: {str(e)}",
                "severity": "error"
            }
            self.error_history.append(error)
    
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
    
    def _schedule_disk_sync(self, bank_type: str, bank_id: str) -> None:
        """Schedule an asynchronous disk synchronization.
        
        Args:
            bank_type: Type of bank (global, project, code)
            bank_id: Bank identifier
        """
        # For Phase 1, we're not implementing the actual synchronization
        # This will be implemented in Phase 2
        logger.info(f"Disk sync scheduled for bank {bank_type}:{bank_id}")
        
        # Add to sync queue for future implementation
        self.sync_queue.put((bank_type, bank_id))
    
    def get_error_history(self) -> list:
        """Return recent processing errors.
        
        Returns:
            List of recent error entries
        """
        return self.error_history[-10:] if self.error_history else []
    
    def dump_debug_memory(self) -> None:
        """Write current cache state to cache_memory_dump.json if debug enabled."""
        if not self.debug_memory_dump:
            return
        
        try:
            # Calculate approximate token count for monitoring purposes
            total_tokens = 0
            for bank_key, content in self.cache.items():
                # Estimate 4 characters per token as a simple approximation
                bank_size = sum(len(str(item)) for item in content.values()) // 4
                total_tokens += bank_size
                logger.info(f"Bank {bank_key}: ~{bank_size} tokens")
            
            logger.info(f"Total cache size: ~{total_tokens} tokens")
            
            # Determine the path for the dump file
            dump_path = Path.home() / ".claude-desktop" / "memory" / "cache_memory_dump.json"
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dump_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
                
            logger.info(f"Debug memory dump written to {dump_path}")
            
        except Exception as e:
            logger.error(f"Failed to write debug memory dump: {e}")
