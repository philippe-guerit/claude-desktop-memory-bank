"""
Context service for Memory Bank.

This service handles context management operations including updating,
searching, and retrieving context.
"""

import os
import re
import logging
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, Tuple

from .storage_service import StorageService
from .repository_service import RepositoryService

logger = logging.getLogger(__name__)

class ContextService:
    """Service for handling context operations in the Memory Bank system."""
    
    # Context file mapping
    CONTEXT_FILES = {
        "project_brief": "projectbrief.md",
        "product_context": "productContext.md",
        "system_patterns": "systemPatterns.md",
        "tech_context": "techContext.md",
        "active_context": "activeContext.md",
        "progress": "progress.md"
    }
    
    # Inverse mapping for convenience
    FILE_TO_CONTEXT = {v: k for k, v in CONTEXT_FILES.items()}
    
    def __init__(self, storage_service: StorageService, repository_service: RepositoryService):
        """Initialize the context service.
        
        Args:
            storage_service: Storage service instance
            repository_service: Repository service instance
        """
        self.storage_service = storage_service
        self.repository_service = repository_service
        self.current_memory_bank = None
    
    async def initialize(self) -> None:
        """Initialize the context service."""
        # Initialize global memory bank
        await self.storage_service.initialize_global_memory_bank()
        
        # Set global memory bank as default
        global_path = await self.storage_service.initialize_global_memory_bank()
        self.current_memory_bank = {
            "type": "global",
            "path": global_path
        }
    
    # Memory bank management
    
    async def get_memory_banks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available memory banks.
        
        Returns:
            Dictionary with global, projects, and repositories memory banks
        """
        # Get global memory bank
        global_memory_bank = [{
            "type": "global",
            "path": str(self.storage_service.global_path)
        }]
        
        # Get project memory banks
        project_names = await self.storage_service.get_project_memory_banks()
        projects = []
        for name in project_names:
            try:
                metadata = await self.storage_service.get_project_metadata(name)
                projects.append({
                    "name": name,
                    "metadata": metadata,
                    "path": await self.storage_service.get_project_path(name)
                })
            except Exception as e:
                # Skip projects with errors
                logger.error(f"Error getting project memory bank {name}: {str(e)}")
        
        # Get repository memory banks
        repositories = []
        repo_records = await self.storage_service.get_repositories()
        for record in repo_records:
            repo_name = record["name"]
            repo_mb_path = await self.storage_service.get_repository_memory_bank_path(repo_name)
            if repo_mb_path:
                repositories.append({
                    "name": repo_name,
                    "repo_path": record["path"],
                    "project": record.get("project"),
                    "remote_url": record.get("remote_url"),
                    "branch": record.get("branch"),
                    "last_accessed": record.get("last_accessed"),
                    "path": repo_mb_path
                })
        
        return {
            "global": global_memory_bank,
            "projects": projects,
            "repositories": repositories
        }
    
    async def get_current_memory_bank(self) -> Dict[str, Any]:
        """Get information about the current memory bank.
        
        Returns:
            Information about the current memory bank
        """
        if not self.current_memory_bank:
            # Initialize with global memory bank
            global_path = await self.storage_service.initialize_global_memory_bank()
            self.current_memory_bank = {
                "type": "global",
                "path": global_path
            }
        
        return self.current_memory_bank
    
    async def set_memory_bank(
        self, 
        type: str = "global",
        project_name: Optional[str] = None,
        repository_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Set the active memory bank.
        
        Args:
            type: Memory bank type ('global', 'project', or 'repository')
            project_name: Project name (for 'project' type)
            repository_path: Repository path (for 'repository' type)
            
        Returns:
            Information about the selected memory bank
        """
        if type == "global":
            # Set global memory bank
            global_path = await self.storage_service.initialize_global_memory_bank()
            self.current_memory_bank = {
                "type": "global",
                "path": global_path
            }
        
        elif type == "project":
            # Set project memory bank
            if not project_name:
                raise ValueError("Project name is required for project memory bank selection.")
            
            # Get project path
            project_path = await self.storage_service.get_project_path(project_name)
            
            # Get project metadata
            try:
                metadata = await self.storage_service.get_project_metadata(project_name)
                
                # Set as current memory bank
                self.current_memory_bank = {
                    "type": "project",
                    "path": project_path,
                    "project": project_name,
                    "metadata": metadata
                }
            except Exception as e:
                logger.error(f"Error setting project memory bank for {project_name}: {str(e)}")
                raise ValueError(f"Error setting project memory bank: {str(e)}")
        
        elif type == "repository":
            # Set repository memory bank
            if not repository_path:
                raise ValueError("Repository path is required for repository memory bank selection.")
            
            # Detect repository
            repo_info = await self.repository_service.detect_repository(repository_path)
            if not repo_info:
                logger.error(f"No Git repository found at or above {repository_path}")
                raise ValueError(f"No Git repository found at or above {repository_path}.")
            
            repo_name = repo_info["name"]
            logger.info(f"Detected repository: {repo_name} at {repo_info['path']}")
            
            # Get repository memory bank path
            repo_mb_path = await self.storage_service.get_repository_memory_bank_path(repo_name)
            if not repo_mb_path:
                # Initialize repository memory bank
                logger.info(f"Initializing memory bank for repository {repo_name}")
                await self.repository_service.initialize_repository_memory_bank(repo_info["path"])
                repo_mb_path = await self.storage_service.get_repository_memory_bank_path(repo_name)
                if not repo_mb_path:
                    logger.error(f"Failed to initialize memory bank for repository {repo_name}")
                    raise ValueError(f"Failed to initialize memory bank for repository {repo_name}.")
            
            # Get associated project
            repo_record = await self.storage_service.get_repository_record(repo_name)
            project_name = repo_record.get("project") if repo_record else None
            
            # Set as current memory bank
            self.current_memory_bank = {
                "type": "repository",
                "path": repo_mb_path,
                "repo_info": repo_info,
                "project": project_name
            }
            
            logger.info(f"Set current memory bank to repository: {repo_name}, path: {repo_mb_path}")
        
        else:
            raise ValueError(f"Unknown memory bank type: {type}. Use 'global', 'project', or 'repository'.")
        
        return self.current_memory_bank
    
    async def create_project(
        self, 
        name: str, 
        description: str, 
        repository_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new project with initial context files.
        
        Args:
            name: Project name
            description: Project description
            repository_path: Repository path (optional)
            
        Returns:
            Project information
        """
        # Validate repository path if provided
        if repository_path:
            if not await self.repository_service.is_git_repository(repository_path):
                raise ValueError(f"The path {repository_path} is not a valid Git repository.")
        
        # Create metadata
        metadata = {
            "name": name,
            "description": description,
            "created": datetime.now(UTC).isoformat(),
            "lastModified": datetime.now(UTC).isoformat()
        }
        
        # Add repository if specified
        if repository_path:
            metadata["repository"] = repository_path
        
        # Create project memory bank
        project_path = await self.storage_service.create_project_memory_bank(name, metadata)
        
        # If repository is specified, register it
        if repository_path:
            repo_info = await self.repository_service.detect_repository(repository_path)
            repo_name = repo_info["name"]
            await self.storage_service.register_repository(
                repository_path, 
                repo_name, 
                name,
                repo_info.get("remote_url"),
                repo_info.get("branch")
            )
        
        # Set this as current memory bank
        self.current_memory_bank = {
            "type": "project",
            "path": project_path,
            "project": name,
            "metadata": metadata
        }
        
        return metadata
    
    # Context operations
    
    async def get_context(self, context_type: str) -> str:
        """Get the content of a specific context file from the current memory bank.
        
        Args:
            context_type: Type of context to get
            
        Returns:
            Content of the context file
        """
        self._validate_context_type(context_type)
        
        # Get current memory bank path
        memory_bank = await self.get_current_memory_bank()
        memory_bank_path = memory_bank["path"]
        
        # Get context file
        file_name = self.CONTEXT_FILES[context_type]
        try:
            content = await self.storage_service.get_context_file(memory_bank_path, file_name)
            logger.info(f"Successfully retrieved context file {file_name} from {memory_bank_path}")
            return content
        except Exception as e:
            logger.error(f"Error retrieving context {context_type}: {str(e)}")
            raise
    
    async def update_context(self, context_type: str, content: str) -> Dict[str, Any]:
        """Update a specific context file in the current memory bank.
        
        Args:
            context_type: Type of context to update
            content: New content for the context file
            
        Returns:
            Information about the current memory bank
        """
        self._validate_context_type(context_type)
        
        # Get current memory bank
        memory_bank = await self.get_current_memory_bank()
        memory_bank_path = memory_bank["path"]
        
        # Update context file
        file_name = self.CONTEXT_FILES[context_type]
        try:
            await self.storage_service.update_context_file(memory_bank_path, file_name, content)
            logger.info(f"Successfully updated context file {file_name} in {memory_bank_path}")
            
            # Wait briefly to ensure file operations complete
            await asyncio.sleep(0.1)
            
            # Verify the update
            read_content = await self.storage_service.get_context_file(memory_bank_path, file_name)
            if read_content != content:
                logger.error(f"File verification failed for {context_type} - content mismatch")
                raise IOError(f"File verification failed for {context_type} - content mismatch")
        except Exception as e:
            logger.error(f"Error updating context {context_type}: {str(e)}")
            raise
        
        return memory_bank
    

    
    async def bulk_update_context(self, updates: Dict[str, str]) -> Dict[str, Any]:
        """Update multiple context files in the current memory bank in one operation.
        
        Args:
            updates: Dictionary mapping context types to content
            
        Returns:
            Information about the current memory bank
        """
        # Validate all context types before updating
        for context_type in updates.keys():
            self._validate_context_type(context_type)
        
        # Get current memory bank
        memory_bank = await self.get_current_memory_bank()
        memory_bank_path = memory_bank["path"]
        
        # Update all specified context files
        success = True
        for context_type, content in updates.items():
            try:
                file_name = self.CONTEXT_FILES[context_type]
                await self.storage_service.update_context_file(memory_bank_path, file_name, content)
                logger.info(f"Successfully updated context file {file_name} in {memory_bank_path}")
            except Exception as e:
                logger.error(f"Error updating context {context_type}: {str(e)}")
                success = False
        
        # Wait briefly to ensure file operations complete
        await asyncio.sleep(0.1)
        
        # Verify the updates
        for context_type, content in updates.items():
            try:
                file_name = self.CONTEXT_FILES[context_type]
                read_content = await self.storage_service.get_context_file(memory_bank_path, file_name)
                if read_content != content:
                    logger.error(f"File verification failed for {context_type} - content mismatch")
                    success = False
            except Exception as e:
                logger.error(f"Error verifying context {context_type}: {str(e)}")
                success = False
        
        if not success:
            raise IOError("Failed to update all context files. Check logs for details.")
        
        return memory_bank
    

    
    async def prune_context(self, max_age_days: int = 90) -> Dict[str, Any]:
        """Remove outdated information from context files.
        
        Args:
            max_age_days: Maximum age of content to retain (in days)
            
        Returns:
            Information about what was pruned
        """
        # Get current memory bank
        memory_bank = await self.get_current_memory_bank()
        memory_bank_path = memory_bank["path"]
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        result = {}
        
        # Process each context file
        for context_type, file_name in self.CONTEXT_FILES.items():
            try:
                # Get current content
                content = await self.storage_service.get_context_file(memory_bank_path, file_name)
                
                # Look for date headers in the format "## Update YYYY-MM-DD"
                sections = re.split(r'(## Update \d{4}-\d{2}-\d{2})', content)
                
                # First section is the main content without a date
                pruned_content = sections[0]
                
                # Track what we keep and remove
                kept_sections = 0
                pruned_sections = 0
                
                # Process dated sections
                for i in range(1, len(sections), 2):
                    if i+1 < len(sections):
                        date_header = sections[i]
                        section_content = sections[i+1]
                        
                        # Extract date from header
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_header)
                        if date_match:
                            date_str = date_match.group(1)
                            try:
                                section_date = datetime.strptime(date_str, "%Y-%m-%d")
                                
                                # Keep section if it's newer than the cutoff date
                                if section_date >= cutoff_date:
                                    pruned_content += date_header + section_content
                                    kept_sections += 1
                                else:
                                    pruned_sections += 1
                            except ValueError:
                                # If date parsing fails, keep the section
                                pruned_content += date_header + section_content
                                kept_sections += 1
                        else:
                            # If no date found, keep the section
                            pruned_content += date_header + section_content
                            kept_sections += 1
                
                # Only update if something was pruned
                if pruned_sections > 0:
                    await self.storage_service.update_context_file(
                        memory_bank_path,
                        file_name,
                        pruned_content
                    )
                    
                    result[context_type] = {
                        "pruned_sections": pruned_sections,
                        "kept_sections": kept_sections
                    }
            except Exception as e:
                # Skip files with errors
                logger.error(f"Error pruning context {context_type}: {str(e)}")
                result[context_type] = {"error": str(e)}
        
        return result
    
    async def get_all_context(self) -> Dict[str, str]:
        """Get all context files from the current memory bank.
        
        Returns:
            Dictionary mapping context types to content
        """
        memory_bank = await self.get_current_memory_bank()
        memory_bank_path = memory_bank["path"]
        
        result = {}
        
        for context_type, file_name in self.CONTEXT_FILES.items():
            try:
                content = await self.storage_service.get_context_file(
                    memory_bank_path,
                    file_name
                )
                result[context_type] = content
            except Exception as e:
                # Skip files with errors
                logger.error(f"Error retrieving context {context_type}: {str(e)}")
                result[context_type] = f"Error retrieving {context_type}"
        
        return result
    
    # Helper methods
    
    def _validate_context_type(self, context_type: str) -> None:
        """Validate that a context type is supported.
        
        Args:
            context_type: Context type to validate
            
        Raises:
            ValueError: If context type is not supported
        """
        if context_type not in self.CONTEXT_FILES:
            raise ValueError(
                f"Unknown context type: {context_type}. " +
                f"Valid types are: {', '.join(self.CONTEXT_FILES.keys())}"
            )
