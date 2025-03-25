"""
Direct access methods for Memory Bank.

This module contains methods for directly accessing Memory Bank functionality
without going through the FastMCP integration layer.
"""

import logging
from typing import Dict, List, Optional, Any

from ..core import (
    start_memory_bank,
    select_memory_bank,
    list_memory_banks,
    detect_repository,
    initialize_repository_memory_bank,
    create_project,
    get_context,
    update_context,
    bulk_update_context,
    prune_context,
    get_all_context,
    get_memory_bank_info
)

logger = logging.getLogger(__name__)

class DirectAccess:
    """Direct access methods for Memory Bank functionality."""
    
    def __init__(self, context_service):
        """Initialize the direct access methods.
        
        Args:
            context_service: The context service instance
        """
        self.context_service = context_service
    
    # Memory bank management
    
    async def start_memory_bank(
        self,
        prompt_name: Optional[str] = None,
        auto_detect: bool = True,
        current_path: Optional[str] = None,
        force_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start a memory bank.
        
        Args:
            prompt_name: Optional name of the prompt to load
            auto_detect: Whether to automatically detect repositories
            current_path: Path to check for repository
            force_type: Force a specific memory bank type
            
        Returns:
            Dictionary with result data
        """
        return await start_memory_bank(
            self.context_service,
            prompt_name=prompt_name,
            auto_detect=auto_detect,
            current_path=current_path,
            force_type=force_type
        )
    
    async def select_memory_bank(
        self,
        type: str = "global", 
        project_name: Optional[str] = None, 
        repository_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Select a memory bank.
        
        Args:
            type: The type of memory bank to use
            project_name: The name of the project
            repository_path: The path to the repository
            
        Returns:
            Dictionary with memory bank information
        """
        return await select_memory_bank(
            self.context_service,
            type=type,
            project_name=project_name,
            repository_path=repository_path
        )
    
    async def list_memory_banks(self) -> Dict[str, Any]:
        """List all available memory banks.
        
        Returns:
            Dictionary with memory bank information
        """
        return await list_memory_banks(self.context_service)
    
    async def detect_repository(self, path: str) -> Optional[Dict[str, Any]]:
        """Detect if a path is within a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            Repository information if detected, None otherwise
        """
        return await detect_repository(self.context_service, path)
    
    async def initialize_repository_memory_bank(
        self,
        repository_path: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a memory bank for a repository.
        
        Args:
            repository_path: Path to the repository
            project_name: Optional project name to associate
            
        Returns:
            Dictionary with memory bank information
        """
        return await initialize_repository_memory_bank(
            self.context_service,
            repository_path,
            project_name
        )
    
    async def create_project(
        self,
        name: str,
        description: str,
        repository_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new project.
        
        Args:
            name: Project name
            description: Project description
            repository_path: Optional path to a Git repository
            
        Returns:
            Dictionary with project information
        """
        return await create_project(
            self.context_service,
            name,
            description,
            repository_path
        )
    
    # Context operations
    
    async def get_context(self, context_type: str) -> str:
        """Get a context file.
        
        Args:
            context_type: Type of context
            
        Returns:
            Context content
        """
        return await get_context(self.context_service, context_type)
    

    async def bulk_update_context(self, updates: Dict[str, str]) -> Dict[str, Any]:
        """Update multiple context files at once.
        
        Args:
            updates: Dictionary with updates
            
        Returns:
            Dictionary with memory bank information
        """
        return await bulk_update_context(self.context_service, updates)
    

    
    async def prune_context(self, max_age_days: int = 90) -> Dict[str, Any]:
        """Remove outdated context.
        
        Args:
            max_age_days: Maximum age of content to keep
            
        Returns:
            Dictionary with pruning results
        """
        return await prune_context(self.context_service, max_age_days)
    
    async def get_all_context(self) -> Dict[str, str]:
        """Get all context files.
        
        Returns:
            Dictionary with all context
        """
        return await get_all_context(self.context_service)
    
    async def get_memory_bank_info(self) -> Dict[str, Any]:
        """Get memory bank information.
        
        Returns:
            Dictionary with memory bank information
        """
        return await get_memory_bank_info(self.context_service)
