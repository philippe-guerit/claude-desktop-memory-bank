"""
Storage manager implementation.

This module provides the StorageManager class for managing memory banks.
"""

from pathlib import Path
import os
import logging
from typing import Dict, Any, List, Optional, Union

from .global_bank import GlobalMemoryBank
from .project_bank import ProjectMemoryBank
from .code_bank import CodeMemoryBank
from .bank import MemoryBank

logger = logging.getLogger(__name__)


class StorageManager:
    """Manages all memory banks for the system."""
    
    def __init__(self, storage_root: Path):
        """Initialize the storage manager.
        
        Args:
            storage_root: Root path for all memory banks
        """
        self.storage_root = storage_root
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each bank type
        (self.storage_root / "global").mkdir(exist_ok=True)
        (self.storage_root / "projects").mkdir(exist_ok=True)
        (self.storage_root / "code").mkdir(exist_ok=True)
        
        # Active banks
        self.active_banks: Dict[str, Dict[str, MemoryBank]] = {
            "global": {},
            "project": {},
            "code": {}
        }
        
        logger.info(f"Storage manager initialized with root at {storage_root}")
    
    def list_banks(self, bank_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List available memory banks.
        
        Args:
            bank_type: Optional type filter (global, project, code)
            
        Returns:
            Dict mapping bank types to lists of bank info
        """
        result = {}
        
        # List global banks
        if bank_type is None or bank_type == "global":
            result["global"] = []
            for bank_dir in (self.storage_root / "global").iterdir():
                if bank_dir.is_dir():
                    try:
                        bank = self.get_bank("global", bank_dir.name)
                        if bank:
                            result["global"].append({
                                "id": bank_dir.name,
                                "last_used": bank.last_updated().isoformat(),
                                "description": "Global conversation memory"
                            })
                    except Exception as e:
                        logger.error(f"Error listing global bank {bank_dir.name}: {e}")
        
        # List project banks
        if bank_type is None or bank_type == "project":
            result["projects"] = []
            for bank_dir in (self.storage_root / "projects").iterdir():
                if bank_dir.is_dir():
                    try:
                        bank = self.get_bank("project", bank_dir.name)
                        if bank:
                            result["projects"].append({
                                "id": bank_dir.name,
                                "last_used": bank.last_updated().isoformat(),
                                "description": f"Project {bank_dir.name.replace('_', ' ').title()}"
                            })
                    except Exception as e:
                        logger.error(f"Error listing project bank {bank_dir.name}: {e}")
        
        # List code banks
        if bank_type is None or bank_type == "code":
            result["code"] = []
            for bank_dir in (self.storage_root / "code").iterdir():
                if bank_dir.is_dir():
                    try:
                        bank = self.get_bank("code", bank_dir.name)
                        if bank:
                            result["code"].append({
                                "id": bank_dir.name,
                                "last_used": bank.last_updated().isoformat(),
                                "description": f"Code for {bank_dir.name.replace('_', ' ').title()}"
                            })
                    except Exception as e:
                        logger.error(f"Error listing code bank {bank_dir.name}: {e}")
        
        return result
    
    def get_bank(self, bank_type: str, bank_id: str, repo_path: Optional[Path] = None) -> Optional[MemoryBank]:
        """Get a memory bank instance.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: Identifier for the specific memory bank
            repo_path: Path to the Git repository (for code banks)
            
        Returns:
            MemoryBank instance if found, None otherwise
        """
        # Check if already active
        if bank_id in self.active_banks.get(bank_type, {}):
            return self.active_banks[bank_type][bank_id]
        
        try:
            # Create a new bank instance
            if bank_type == "global":
                bank = GlobalMemoryBank(self.storage_root, bank_id)
            elif bank_type == "project":
                bank = ProjectMemoryBank(self.storage_root, bank_id)
            elif bank_type == "code":
                bank = CodeMemoryBank(self.storage_root, bank_id, repo_path)
            else:
                logger.error(f"Unknown bank type: {bank_type}")
                return None
            
            # Cache the bank instance
            if bank_type not in self.active_banks:
                self.active_banks[bank_type] = {}
            self.active_banks[bank_type][bank_id] = bank
            
            return bank
        
        except Exception as e:
            logger.error(f"Error getting bank {bank_type}/{bank_id}: {e}")
            return None
    
    def create_bank(self, bank_type: str, bank_id: str, repo_path: Optional[Path] = None) -> Optional[MemoryBank]:
        """Create a new memory bank.
        
        Args:
            bank_type: Type of memory bank (global, project, code)
            bank_id: Identifier for the specific memory bank
            repo_path: Path to the Git repository (for code banks)
            
        Returns:
            Newly created MemoryBank instance
        """
        # Get or create the bank
        bank = self.get_bank(bank_type, bank_id, repo_path)
        
        # Initialize default content if it's a new bank
        if bank:
            # This is handled in the bank constructors
            pass
        
        return bank
    
    def detect_repo(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Detect if a path is inside a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            Dict with repo info if found, None otherwise
        """
        try:
            # Only import if needed
            import git
            
            # Convert to Path if needed
            if isinstance(path, str):
                path = Path(path)
            
            # Try to find the Git repo
            try:
                repo = git.Repo(path, search_parent_directories=True)
                repo_path = Path(repo.working_dir)
                
                # Get basic Git info
                return {
                    "is_git_repo": True,
                    "repo_path": str(repo_path),
                    "repo_name": os.path.basename(repo_path),
                    "current_branch": repo.active_branch.name,
                    "remote_url": next(repo.remotes.origin.urls) if repo.remotes else None
                }
            except git.exc.InvalidGitRepositoryError:
                return None
            
        except Exception as e:
            logger.error(f"Error detecting Git repository at {path}: {e}")
            return None
    
    def close(self) -> None:
        """Close all active banks and release resources."""
        # Currently no resources to release
        self.active_banks = {
            "global": {},
            "project": {},
            "code": {}
        }
