import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from .storage_manager import StorageManager
from .memory_bank_selector import MemoryBankSelector

class ContextManager:
    def __init__(self, storage_manager: StorageManager, memory_bank_selector: MemoryBankSelector):
        self.storage_manager = storage_manager
        self.memory_bank_selector = memory_bank_selector
    
    async def initialize(self) -> None:
        """Initialize the context manager."""
        await self.storage_manager.initialize_templates()
        await self.memory_bank_selector.initialize()
    
    async def create_project(self, project_name: str, description: str, 
                         repository_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project with initial context files."""
        metadata = {
            "name": project_name,
            "description": description,
            "created": self.storage_manager._get_current_timestamp(),
            "lastModified": self.storage_manager._get_current_timestamp()
        }
        
        # Add repository if specified
        if repository_path:
            metadata["repository"] = repository_path
        
        # Create project memory bank
        await self.storage_manager.create_project_memory_bank(project_name, metadata)
        
        # If repository is specified, register it
        if repository_path:
            await self.storage_manager.register_repository(repository_path, project_name)
        
        # Select this memory bank
        await self.memory_bank_selector.select_memory_bank(claude_project=project_name)
        
        return metadata
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with their metadata."""
        project_names = await self.storage_manager.get_project_memory_banks()
        projects = []
        
        for name in project_names:
            try:
                metadata = await self.storage_manager.get_project_metadata(name)
                projects.append(metadata)
            except Exception:
                # Skip projects with errors
                pass
        
        return projects
    
    async def set_memory_bank(self, 
                          claude_project: Optional[str] = None, 
                          repository_path: Optional[str] = None) -> Dict[str, Any]:
        """Set the active memory bank."""
        return await self.memory_bank_selector.select_memory_bank(
            claude_project=claude_project,
            repo_path=repository_path
        )
    
    async def get_context(self, context_type: str) -> str:
        """Get the content of a specific context file from the current memory bank."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        if context_type not in file_mapping:
            raise ValueError(f"Unknown context type: {context_type}")
        
        return await self.storage_manager.get_context_file(
            memory_bank_path, 
            file_mapping[context_type]
        )
    
    async def update_context(self, context_type: str, content: str) -> Dict[str, Any]:
        """Update a specific context file in the current memory bank."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        if context_type not in file_mapping:
            raise ValueError(f"Unknown context type: {context_type}")
        
        await self.storage_manager.update_context_file(
            memory_bank_path,
            file_mapping[context_type],
            content
        )
        
        return memory_bank_info
    
    async def search_context(self, query: str) -> Dict[str, List[str]]:
        """Search through context files in the current memory bank for the given query."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "projectbrief.md": "project_brief",
            "productContext.md": "product_context",
            "systemPatterns.md": "system_patterns",
            "techContext.md": "tech_context",
            "activeContext.md": "active_context",
            "progress.md": "progress"
        }
        
        results = {}
        
        for file_name, context_type in file_mapping.items():
            try:
                content = await self.storage_manager.get_context_file(
                    memory_bank_path, 
                    file_name
                )
                
                # Simple search implementation - can be improved
                if query.lower() in content.lower():
                    lines = content.split('\n')
                    matching_lines = [
                        line.strip() for line in lines 
                        if query.lower() in line.lower()
                    ]
                    if matching_lines:
                        results[context_type] = matching_lines
            except Exception:
                # Skip files with errors
                pass
        
        return results
    
    async def get_all_context(self) -> Dict[str, str]:
        """Get all context files from the current memory bank."""
        memory_bank_info = await self.memory_bank_selector.get_current_memory_bank()
        memory_bank_path = memory_bank_info["path"]
        
        file_mapping = {
            "project_brief": "projectbrief.md",
            "product_context": "productContext.md",
            "system_patterns": "systemPatterns.md",
            "tech_context": "techContext.md",
            "active_context": "activeContext.md",
            "progress": "progress.md"
        }
        
        result = {}
        
        for context_type, file_name in file_mapping.items():
            try:
                content = await self.storage_manager.get_context_file(
                    memory_bank_path,
                    file_name
                )
                result[context_type] = content
            except Exception:
                # Skip files with errors
                result[context_type] = f"Error retrieving {context_type}"
        
        return result
    
    async def detect_repository(self, path: str) -> Optional[Dict[str, Any]]:
        """Detect if a path is within a Git repository."""
        return await self.memory_bank_selector.detect_repository(path)
    
    async def initialize_repository_memory_bank(self, repo_path: str, 
                                           claude_project: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a repository memory bank."""
        return await self.memory_bank_selector.initialize_repository_memory_bank(
            repo_path, 
            claude_project
        )
    
    async def get_memory_banks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available memory banks."""
        return await self.memory_bank_selector.get_all_memory_banks()
    
    async def get_current_memory_bank(self) -> Dict[str, Any]:
        """Get information about the current memory bank."""
        return await self.memory_bank_selector.get_current_memory_bank()
