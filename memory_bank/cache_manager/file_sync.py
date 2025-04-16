"""
File synchronization module for cache manager.

This module provides file synchronization functionality between memory cache and disk.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, UTC
from pathlib import Path
from queue import Queue, Empty
from typing import Dict, Any, Tuple, Optional, Union

logger = logging.getLogger(__name__)


class FileSynchronizer:
    """Handles synchronization between in-memory cache and disk files."""
    
    def __init__(self, sync_interval: int = 60, storage_root: Optional[Path] = None):
        """Initialize the file synchronizer.
        
        Args:
            sync_interval: Interval in seconds between sync operations
            storage_root: Root path for file storage, defaults to ~/.claude-desktop/memory
        """
        self.sync_interval = sync_interval
        self.sync_queue = Queue()
        self.running = False
        self.sync_thread = None
        self.last_sync_time = {}
        
        # Set storage root (default to ~/.claude-desktop/memory if not provided)
        self.storage_root = storage_root or Path.home() / ".claude-desktop" / "memory"
        self.storage_root.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """Start the synchronization thread."""
        if self.running:
            return
            
        self.running = True
        self.sync_thread = threading.Thread(
            target=self._sync_worker, 
            daemon=True,
            name="CacheFileSyncThread"
        )
        self.sync_thread.start()
        logger.info(f"File synchronizer started with interval of {self.sync_interval} seconds")
    
    def stop(self):
        """Stop the synchronization thread."""
        if not self.running:
            return
            
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5.0)
            logger.info("File synchronizer stopped")
    
    def schedule_sync(self, bank_type: str, bank_id: str, priority: bool = False):
        """Schedule a bank for synchronization.
        
        Args:
            bank_type: Type of memory bank
            bank_id: ID of the memory bank
            priority: Whether this is a high-priority sync
        """
        # Put in queue with priority marker
        self.sync_queue.put((bank_type, bank_id, priority))
        logger.debug(f"Scheduled sync for {bank_type}:{bank_id} with priority={priority}")
    
    def sync_to_disk(self, bank_type: str, bank_id: str, content: Dict[str, str], 
                     bank_root: Path) -> bool:
        """Synchronize in-memory content to disk.
        
        Args:
            bank_type: Type of memory bank
            bank_id: ID of the memory bank
            content: Memory bank content
            bank_root: Root path of the memory bank
            
        Returns:
            True if sync was successful, False otherwise
        """
        key = f"{bank_type}:{bank_id}"
        try:
            logger.info(f"Syncing {bank_type}:{bank_id} to disk")
            
            # Create the bank directory if it doesn't exist
            bank_root.mkdir(parents=True, exist_ok=True)
            
            # Write each file
            for file_path, file_content in content.items():
                full_path = bank_root / file_path
                
                # Create subdirectories if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file content
                full_path.write_text(file_content)
                logger.debug(f"Wrote file {file_path} for {bank_type}:{bank_id}")
            
            # Update last sync time
            self.last_sync_time[key] = datetime.now(UTC)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync {bank_type}:{bank_id} to disk: {e}")
            return False
    
    def write_debug_dump(self, cache: Dict[str, Dict[str, str]], dump_path: Path) -> bool:
        """Write a debug dump of the in-memory cache.
        
        Args:
            cache: The in-memory cache
            dump_path: Path to write the debug dump
            
        Returns:
            True if dump was successful, False otherwise
        """
        try:
            # Calculate approximate token count for monitoring purposes
            token_metrics = {}
            total_tokens = 0
            
            for bank_key, content in cache.items():
                # Estimate 4 characters per token as a simple approximation
                bank_size = sum(len(str(item)) for item in content.values()) // 4
                total_tokens += bank_size
                token_metrics[bank_key] = bank_size
                logger.debug(f"Bank {bank_key}: ~{bank_size} tokens")
            
            # Create dump object with metrics
            dump_obj = {
                "cache": cache,
                "metrics": {
                    "total_tokens": total_tokens,
                    "bank_tokens": token_metrics,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            }
            
            # Ensure the directory exists
            dump_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the dump file
            with open(dump_path, 'w') as f:
                json.dump(dump_obj, f, indent=2)
                
            logger.info(f"Debug memory dump written to {dump_path} ({total_tokens} tokens)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write debug memory dump: {e}")
            return False
    
    def _sync_worker(self):
        """Worker thread for background synchronization."""
        next_periodic_sync = time.time() + self.sync_interval
        
        while self.running:
            try:
                # Check for periodic sync
                current_time = time.time()
                if current_time >= next_periodic_sync:
                    logger.debug("Triggering periodic sync check")
                    self._trigger_periodic_sync()
                    next_periodic_sync = current_time + self.sync_interval
                
                # Process any pending sync requests
                try:
                    bank_type, bank_id, priority = self.sync_queue.get(timeout=1.0)
                    logger.debug(f"Processing sync request for {bank_type}:{bank_id}")
                    
                    # Signal the cache manager to perform the sync
                    # This is handled externally as we don't have direct access to 
                    # the cache manager from here
                    
                    # Mark as done
                    self.sync_queue.task_done()
                    
                except Empty:
                    # No sync requests, just continue
                    pass
                    
            except Exception as e:
                logger.error(f"Error in sync worker thread: {e}")
                time.sleep(5)  # Avoid tight loop on persistent errors
    
    def _trigger_periodic_sync(self):
        """Trigger periodic sync for all banks with pending changes."""
        # This is a placeholder - the actual implementation is in the cache manager
        # as it has access to the pending_updates dict
        pass
    
    def get_last_sync_time(self, bank_type: str, bank_id: str) -> Optional[datetime]:
        """Get the last synchronization time for a bank.
        
        Args:
            bank_type: Type of memory bank
            bank_id: ID of the memory bank
            
        Returns:
            Last sync time or None if never synced
        """
        key = f"{bank_type}:{bank_id}"
        return self.last_sync_time.get(key)
