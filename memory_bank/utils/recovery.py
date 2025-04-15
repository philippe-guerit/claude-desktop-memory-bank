"""
Basic recovery and consistency checking for the memory bank system.

Provides lightweight tools to detect inconsistent states and log information
to assist with manual recovery when needed.
"""

import logging
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set

logger = logging.getLogger(__name__)


class ConsistencyChecker:
    """Simple checker for memory bank consistency between cache and disk."""
    
    def __init__(self, storage_root: Path):
        """Initialize the consistency checker.
        
        Args:
            storage_root: Root path of the memory bank storage
        """
        self.storage_root = storage_root
        logger.info(f"ConsistencyChecker initialized with storage root: {storage_root}")
    
    def check_bank_consistency(self, bank_type: str, bank_id: str, 
                              cache_content: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Check if a memory bank is consistent between cache and disk.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
            cache_content: Current cache content for the bank
            
        Returns:
            Tuple of (is_consistent, list of inconsistencies)
        """
        # Get bank path
        bank_path = self._get_bank_path(bank_type, bank_id)
        
        # Check if bank exists on disk
        if not bank_path.exists():
            logger.warning(f"Bank {bank_type}:{bank_id} doesn't exist on disk")
            return False, [f"Bank {bank_type}:{bank_id} doesn't exist on disk"]
        
        inconsistencies = []
        
        # Check if all files in cache exist on disk with same content
        for file_path, content in cache_content.items():
            disk_path = bank_path / file_path
            
            if not disk_path.exists():
                inconsistencies.append(f"File {file_path} exists in cache but not on disk")
                logger.warning(f"File {file_path} exists in cache but not on disk for bank {bank_type}:{bank_id}")
                continue
            
            # Check file content (optional - can be expensive for large files)
            # We could add a parameter to skip content checks for performance
            try:
                disk_content = disk_path.read_text(encoding='utf-8')
                if disk_content != content:
                    inconsistencies.append(f"File {file_path} has different content in cache vs disk")
                    logger.warning(f"File {file_path} has different content in cache vs disk for bank {bank_type}:{bank_id}")
            except Exception as e:
                inconsistencies.append(f"Error reading file {file_path} from disk: {str(e)}")
                logger.error(f"Error reading file {file_path} from disk for bank {bank_type}:{bank_id}: {e}")
        
        # Return result
        is_consistent = len(inconsistencies) == 0
        if is_consistent:
            logger.info(f"Bank {bank_type}:{bank_id} is consistent between cache and disk")
        else:
            logger.warning(f"Found {len(inconsistencies)} inconsistencies in bank {bank_type}:{bank_id}")
            
        return is_consistent, inconsistencies
    
    def _get_bank_path(self, bank_type: str, bank_id: str) -> Path:
        """Get the path to a bank on disk.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
            
        Returns:
            Path to the bank
        """
        if bank_type == "global":
            return self.storage_root / "global" / bank_id
        elif bank_type == "project":
            return self.storage_root / "projects" / bank_id
        elif bank_type == "code":
            return self.storage_root / "code" / bank_id
        else:
            raise ValueError(f"Unknown bank type: {bank_type}")
    
    def log_diagnostic_info(self, bank_type: str, bank_id: str, issue: str) -> None:
        """Log detailed diagnostic information about a bank.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: ID of the memory bank
            issue: Description of the issue
        """
        try:
            bank_path = self._get_bank_path(bank_type, bank_id)
            
            # Collect basic information
            info = {
                "timestamp": datetime.now(UTC).isoformat(),
                "bank_type": bank_type,
                "bank_id": bank_id,
                "issue": issue,
                "bank_path": str(bank_path),
                "bank_exists": bank_path.exists(),
                "files": []
            }
            
            # List files if bank exists
            if bank_path.exists():
                for path in bank_path.glob('**/*'):
                    if path.is_file():
                        rel_path = path.relative_to(bank_path)
                        file_info = {
                            "path": str(rel_path),
                            "size": path.stat().st_size,
                            "mtime": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
                        }
                        info["files"].append(file_info)
            
            # Log the diagnostic information
            logger.info(f"Diagnostic information for bank {bank_type}:{bank_id}: {json.dumps(info)}")
            
            # Write to diagnostic file
            diag_dir = self.storage_root / "diagnostics"
            diag_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            diag_file = diag_dir / f"{bank_type}_{bank_id}_{timestamp}_diag.json"
            
            with open(diag_file, 'w') as f:
                json.dump(info, f, indent=2)
                
            logger.info(f"Wrote diagnostic information to {diag_file}")
            
        except Exception as e:
            logger.error(f"Error logging diagnostic information for bank {bank_type}:{bank_id}: {e}")
