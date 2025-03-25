"""
Repository service for Memory Bank.

This service handles Git repository detection and management.
"""

import os
import subprocess
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from .storage_service import StorageService

logger = logging.getLogger(__name__)

class RepositoryService:
    """Service for handling Git repository operations in the Memory Bank system."""
    
    def __init__(self, storage_service: StorageService):
        """Initialize the repository service.
        
        Args:
            storage_service: Storage service instance
        """
        self.storage_service = storage_service
    
    async def detect_repository(self, path: str) -> Optional[Dict[str, Any]]:
        """Detect if a path is within a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            Repository information if detected, None otherwise
        """
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        repo_root = await loop.run_in_executor(None, self.find_repository_root, path)
        
        if not repo_root:
            return None
        
        # Get repository information
        repo_info = await loop.run_in_executor(None, self.get_repository_info, repo_root)
        
        # Check if there's a memory bank for this repository
        repo_name = os.path.basename(repo_root)
        memory_bank_path = await self.storage_service.get_repository_memory_bank_path(repo_name)
        if memory_bank_path:
            repo_info["memory_bank_path"] = memory_bank_path
        
        return repo_info
    
    async def initialize_repository_memory_bank(
        self, 
        repo_path: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a memory bank for a repository.
        
        Args:
            repo_path: Path to the repository
            project_name: Name of the associated project (optional)
            
        Returns:
            Memory bank information
        """
        # Verify this is a Git repository
        if not await asyncio.get_event_loop().run_in_executor(None, self.is_git_repository, repo_path):
            raise ValueError(f"The path {repo_path} is not a valid Git repository.")
        
        # Get repository info
        repo_info = await asyncio.get_event_loop().run_in_executor(None, self.get_repository_info, repo_path)
        repo_name = repo_info["name"]
        
        # Register repository with branch and remote URL
        await self.storage_service.register_repository(
            repo_path, 
            repo_name, 
            project_name,
            repo_info.get("remote_url"),
            repo_info.get("branch")
        )
        
        # Create memory bank for repository - this will create .claude-memory in the repo
        memory_bank_path = await self.storage_service.create_repository_memory_bank(repo_name)
        
        # Return memory bank info
        return {
            "type": "repository",
            "path": memory_bank_path,
            "repo_info": repo_info,
            "project": project_name
        }
    
    # Helper methods
    
    def is_git_repository(self, path: str) -> bool:
        """Check if the given path is a git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a git repository, False otherwise
        """
        git_dir = os.path.join(path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    def find_repository_root(self, path: str) -> Optional[str]:
        """Find the nearest git repository root from a path.
        
        Args:
            path: Path to start search from
            
        Returns:
            Repository root path or None if not found
        """
        current = os.path.abspath(path)
        while current != os.path.dirname(current):  # Stop at filesystem root
            if self.is_git_repository(current):
                return current
            current = os.path.dirname(current)
        return None
    
    def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """Get information about a Git repository.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Repository information
        """
        try:
            # Get repository name
            name = os.path.basename(repo_path)
            
            # Get remote URL if available
            remote_url = None
            try:
                result = subprocess.run(
                    ["git", "config", "--get", "remote.origin.url"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    remote_url = result.stdout.strip()
                    logger.info(f"Detected remote URL: {remote_url}")
            except Exception as e:
                logger.warning(f"Error getting remote URL: {str(e)}")
            
            # Get current branch
            branch = None
            try:
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    branch = result.stdout.strip()
                    if not branch:  # Try fallback method
                        result = subprocess.run(
                            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            cwd=repo_path,
                            capture_output=True,
                            text=True,
                            check=False
                        )
                        if result.returncode == 0:
                            branch = result.stdout.strip()
                    logger.info(f"Detected branch: {branch}")
            except Exception as e:
                logger.warning(f"Error getting branch: {str(e)}")
            
            return {
                "name": name,
                "path": repo_path,
                "remote_url": remote_url,
                "branch": branch
            }
        except Exception as e:
            logger.error(f"Error getting repository info: {str(e)}")
            return {
                "name": os.path.basename(repo_path),
                "path": repo_path,
                "error": str(e)
            }
