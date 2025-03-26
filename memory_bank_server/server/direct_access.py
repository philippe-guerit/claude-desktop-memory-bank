"""
Direct access methods for Memory Bank.

This module contains methods for directly accessing Memory Bank functionality
without going through the FastMCP integration layer.
"""

import logging
from typing import Dict, List, Optional, Any

from ..core import (
    # Fluent API-style functions
    activate,
    select,
    list,
    update,
    
    # Context functions
    get_context,
    get_all_context,
    get_memory_bank_info
)

# Import internal helper functions for internal use
from ..core.context import _prune_context_internal

logger = logging.getLogger(__name__)

class DirectAccess:
    """Direct access methods for Memory Bank functionality."""
    
    def __init__(self, context_service):
        """Initialize the direct access methods.
        
        Args:
            context_service: The context service instance
        """
        self.context_service = context_service
    
    # New fluent API-style methods
    
    async def activate(
        self,
        prompt_name: Optional[str] = None,
        auto_detect: bool = True,
        current_path: Optional[str] = None,
        force_type: Optional[str] = None,
        project_name: Optional[str] = None,
        project_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Activate a memory bank with unified approach (fluent API style).
        
        Args:
            prompt_name: Optional name of the prompt to load
            auto_detect: Whether to automatically detect repositories
            current_path: Path to check for repository
            force_type: Force a specific memory bank type
            project_name: Optional name for creating a new project
            project_description: Optional description for creating a new project
            
        Returns:
            Dictionary with result data
        """
        return await activate(
            self.context_service,
            prompt_name=prompt_name,
            auto_detect=auto_detect,
            current_path=current_path,
            force_type=force_type,
            project_name=project_name,
            project_description=project_description
        )
    
    async def select(
        self,
        type: str = "global", 
        project_name: Optional[str] = None, 
        repository_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Select a memory bank (fluent API style).
        
        Args:
            type: The type of memory bank to use
            project_name: The name of the project
            repository_path: The path to the repository
            
        Returns:
            Dictionary with memory bank information
        """
        return await select(
            self.context_service,
            type=type,
            project_name=project_name,
            repository_path=repository_path
        )
    
    async def list(self) -> Dict[str, Any]:
        """List all available memory banks (fluent API style).
        
        Returns:
            Dictionary with memory bank information
        """
        return await list(self.context_service)
    
    async def update(self, updates: Dict[str, str]) -> Dict[str, Any]:
        """Update multiple context files at once (fluent API style).
        
        Args:
            updates: Dictionary with updates
            
        Returns:
            Dictionary with memory bank information
        """
        return await update(self.context_service, updates)
    
    # Removed deprecated methods
    
    # Context operations
    
    async def get_context(self, context_type: str) -> str:
        """Get a context file.
        
        Args:
            context_type: Type of context
            
        Returns:
            Context content
        """
        return await get_context(self.context_service, context_type)
    

    # Removed deprecated methods
    

    
    # Internal method for pruning - not exposed as a tool
    async def _prune_context(self, max_age_days: int = 90) -> Dict[str, Any]:
        """Internal method for pruning context.
        
        Args:
            max_age_days: Maximum age of content to keep
            
        Returns:
            Dictionary with pruning results
        """
        return await _prune_context_internal(self.context_service, max_age_days)
    
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
