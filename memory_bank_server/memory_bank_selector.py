import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from .repository_utils import RepositoryUtils
from .storage_manager import StorageManager

class MemoryBankSelector:
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.current_memory_bank = None
        self.current_memory_bank_type = None
    
    async def initialize(self) -> None:
        """Initialize the memory bank selector."""
        # Ensure global memory bank exists
        await self.storage_manager.initialize_global_memory_bank()
        
        # Set global as default
        self.current_memory_bank = str(self.storage_manager.global_path)
        self.current_memory_bank_type = "global"
    
    async def select_memory_bank(self, 
                              claude_project: Optional[str] = None, 
                              repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Select an appropriate memory bank based on context."""
        # Priority 1: Explicitly provided repository path
        if repo_path:
            if RepositoryUtils.is_git_repository(repo_path):
                # Initialize memory bank if it doesn't exist
                memory_bank_path = os.path.join(repo_path, '.claude-memory')
                if not os.path.exists(memory_bank_path):
                    os.makedirs(memory_bank_path)
                    RepositoryUtils.initialize_memory_bank(
                        repo_path, 
                        str(self.storage_manager.templates_path)
                    )
                
                # Register repository if not already registered
                repo_name = RepositoryUtils.get_repository_name(repo_path)
                repo_record = await self.storage_manager.get_repository_record(repo_name)
                if not repo_record:
                    await self.storage_manager.register_repository(repo_path, claude_project)
                
                self.current_memory_bank = memory_bank_path
                self.current_memory_bank_type = "repository"
                
                return {
                    "type": "repository",
                    "path": memory_bank_path,
                    "repo_info": RepositoryUtils.get_repository_info(repo_path)
                }
        
        # Priority 2: Claude project with associated repository
        if claude_project:
            # Get list of project memory banks
            project_memory_banks = await self.storage_manager.get_project_memory_banks()
            
            if claude_project in project_memory_banks:
                # Check if project has an associated repository
                project_metadata = await self.storage_manager.get_project_metadata(claude_project)
                if "repository" in project_metadata and project_metadata["repository"]:
                    repo_path = project_metadata["repository"]
                    
                    if RepositoryUtils.is_git_repository(repo_path):
                        # Use repository memory bank
                        memory_bank_path = os.path.join(repo_path, '.claude-memory')
                        if not os.path.exists(memory_bank_path):
                            os.makedirs(memory_bank_path)
                            RepositoryUtils.initialize_memory_bank(
                                repo_path, 
                                str(self.storage_manager.templates_path)
                            )
                        
                        self.current_memory_bank = memory_bank_path
                        self.current_memory_bank_type = "repository"
                        
                        return {
                            "type": "repository",
                            "path": memory_bank_path,
                            "repo_info": RepositoryUtils.get_repository_info(repo_path),
                            "project": claude_project
                        }
                
                # No repository or invalid repository, use project memory bank
                project_path = self.storage_manager.projects_path / claude_project
                self.current_memory_bank = str(project_path)
                self.current_memory_bank_type = "project"
                
                return {
                    "type": "project",
                    "path": str(project_path),
                    "project": claude_project
                }
        
        # Priority 3: Default to global memory bank
        global_path = str(self.storage_manager.global_path)
        self.current_memory_bank = global_path
        self.current_memory_bank_type = "global"
        
        return {
            "type": "global",
            "path": global_path
        }
    
    async def get_current_memory_bank(self) -> Dict[str, Any]:
        """Get information about the currently selected memory bank."""
        if not self.current_memory_bank:
            # Initialize with global if not set
            await self.initialize()
        
        result = {
            "type": self.current_memory_bank_type,
            "path": self.current_memory_bank
        }
        
        # Add additional info based on type
        if self.current_memory_bank_type == "repository":
            repo_path = os.path.dirname(self.current_memory_bank)
            result["repo_info"] = RepositoryUtils.get_repository_info(repo_path)
        elif self.current_memory_bank_type == "project":
            project_name = os.path.basename(self.current_memory_bank)
            result["project"] = project_name
        
        return result
    
    async def detect_repository(self, path: str) -> Optional[Dict[str, Any]]:
        """Detect if a path is within a Git repository."""
        repo_root = RepositoryUtils.find_repository_root(path)
        if repo_root:
            return RepositoryUtils.get_repository_info(repo_root)
        return None
    
    async def initialize_repository_memory_bank(self, repo_path: str, 
                                            claude_project: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a repository memory bank."""
        if not RepositoryUtils.is_git_repository(repo_path):
            raise ValueError(f"Path is not a Git repository: {repo_path}")
        
        # Create .claude-memory directory if it doesn't exist
        memory_bank_path = os.path.join(repo_path, '.claude-memory')
        if not os.path.exists(memory_bank_path):
            os.makedirs(memory_bank_path)
        
        # Initialize with template files
        RepositoryUtils.initialize_memory_bank(
            repo_path, 
            str(self.storage_manager.templates_path)
        )
        
        # Register repository 
        await self.storage_manager.register_repository(repo_path, claude_project)
        
        # Set as current memory bank
        self.current_memory_bank = memory_bank_path
        self.current_memory_bank_type = "repository"
        
        return {
            "type": "repository",
            "path": memory_bank_path,
            "repo_info": RepositoryUtils.get_repository_info(repo_path),
            "project": claude_project
        }
    
    async def get_all_memory_banks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get information about all available memory banks."""
        result = {
            "global": [{"path": str(self.storage_manager.global_path)}],
            "projects": [],
            "repositories": []
        }
        
        # Get project memory banks
        project_names = await self.storage_manager.get_project_memory_banks()
        for name in project_names:
            try:
                metadata = await self.storage_manager.get_project_metadata(name)
                result["projects"].append({
                    "name": name,
                    "path": str(self.storage_manager.projects_path / name),
                    "metadata": metadata
                })
            except Exception:
                # Skip projects with errors
                pass
        
        # Get repository memory banks
        repositories = await self.storage_manager.get_repositories()
        for repo in repositories:
            try:
                repo_path = repo.get("path", "")
                if repo_path and RepositoryUtils.is_git_repository(repo_path):
                    memory_bank_path = os.path.join(repo_path, '.claude-memory')
                    if os.path.exists(memory_bank_path):
                        result["repositories"].append({
                            "name": repo.get("name", ""),
                            "path": memory_bank_path,
                            "repo_path": repo_path,
                            "project": repo.get("project")
                        })
            except Exception:
                # Skip repositories with errors
                pass
        
        return result
