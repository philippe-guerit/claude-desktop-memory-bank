"""
Storage service for Memory Bank.

This service handles all file I/O operations for the Memory Bank system.
"""

import os
import json
import shutil
import asyncio
import logging
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class StorageService:
    """Service for handling storage operations in the Memory Bank system."""
    
    def __init__(self, root_path: str):
        """Initialize the storage service.
        
        Args:
            root_path: Root path for storing all memory bank data
        """
        self.root_path = Path(root_path)
        self.global_path = self.root_path / "global"
        self.projects_path = self.root_path / "projects"
        self.repositories_path = self.root_path / "repositories"
        self.templates_path = self.root_path / "templates"
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.global_path.mkdir(parents=True, exist_ok=True)
        self.projects_path.mkdir(parents=True, exist_ok=True)
        self.repositories_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)
    
    # Template operations
    
    async def initialize_template(self, template_name: str, content: str) -> None:
        """Initialize a template file if it doesn't exist.
        
        Args:
            template_name: Name of the template file
            content: Content to write to the template file
        """
        template_path = self.templates_path / template_name
        if not template_path.exists():
            await self.write_file(template_path, content)
    
    async def initialize_templates(self) -> None:
        """Initialize all default templates."""
        templates = {
            "projectbrief.md": "# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n",
            "productContext.md": "# Product Context\n\n## Problem\n\n## Solution\n\n## User Experience\n\n## Stakeholders\n",
            "systemPatterns.md": "# System Patterns\n\n## Architecture\n\n## Patterns\n\n## Decisions\n\n## Relationships\n",
            "techContext.md": "# Technical Context\n\n## Technologies\n\n## Setup\n\n## Constraints\n\n## Dependencies\n",
            "activeContext.md": "# Active Context\n\n## Current Focus\n\n## Recent Changes\n\n## Next Steps\n\n## Active Decisions\n",
            "progress.md": "# Progress\n\n## Completed\n\n## In Progress\n\n## Pending\n\n## Issues\n"
        }
        
        for name, content in templates.items():
            await self.initialize_template(name, content)
    
    async def get_template(self, template_name: str) -> str:
        """Get the content of a template file.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            Content of the template file
        """
        template_path = self.templates_path / template_name
        return await self.read_file(template_path)
    
    # Memory bank operations
    
    async def initialize_global_memory_bank(self) -> str:
        """Initialize the global memory bank if it doesn't exist.
        
        Returns:
            Path to the global memory bank
        """
        # Check if global memory bank exists
        if not any(self.global_path.iterdir()):
            # Initialize files from templates
            for template_name in ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                                "techContext.md", "activeContext.md", "progress.md"]:
                template_content = await self.get_template(template_name)
                file_path = self.global_path / template_name
                await self.write_file(file_path, template_content)
        
        return str(self.global_path)
    
    async def create_project_memory_bank(self, project_name: str, metadata: Dict[str, Any]) -> str:
        """Create a new project memory bank.
        
        Args:
            project_name: Name of the project
            metadata: Metadata for the project
            
        Returns:
            Path to the project memory bank
        """
        project_path = self.projects_path / project_name
        project_path.mkdir(exist_ok=True)
        
        # Create project metadata file
        metadata_path = project_path / "project.json"
        await self.write_file(metadata_path, json.dumps(metadata, indent=2))
        
        # Initialize project files from templates
        for template_name in ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                            "techContext.md", "activeContext.md", "progress.md"]:
            template_content = await self.get_template(template_name)
            file_path = project_path / template_name
            await self.write_file(file_path, template_content)
        
        return str(project_path)
    
    async def create_repository_memory_bank(self, repo_name: str) -> str:
        """Create a new repository memory bank.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Path to the repository memory bank
        """
        # Get repository record
        repo_record = await self.get_repository_record(repo_name)
        if not repo_record:
            logger.error(f"Repository {repo_name} not found in registry")
            raise ValueError(f"Repository {repo_name} not found in registry")
        
        repo_path = Path(repo_record["path"])
        memory_bank_path = repo_path / ".claude-memory"
        memory_bank_path.mkdir(exist_ok=True)
        
        # Initialize repository files from templates
        for template_name in ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                            "techContext.md", "activeContext.md", "progress.md"]:
            template_content = await self.get_template(template_name)
            file_path = memory_bank_path / template_name
            await self.write_file(file_path, template_content)
        
        # Update the last accessed timestamp
        repo_record["last_accessed"] = self.get_current_timestamp()
        record_path = self.repositories_path / f"{repo_name}.json"
        await self.write_file(record_path, json.dumps(repo_record, indent=2))
        
        return str(memory_bank_path)
    
    # Project operations
    
    async def get_project_memory_banks(self) -> List[str]:
        """Get a list of all project memory bank names.
        
        Returns:
            List of project names
        """
        return [p.name for p in self.projects_path.iterdir() if p.is_dir()]
    
    async def get_project_path(self, project_name: str) -> str:
        """Get the path to a project memory bank.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the project memory bank
        """
        return str(self.projects_path / project_name)
    
    async def get_project_metadata(self, project_name: str) -> Dict[str, Any]:
        """Get project metadata.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project metadata
        """
        metadata_path = self.projects_path / project_name / "project.json"
        content = await self.read_file(metadata_path)
        return json.loads(content)
    
    async def update_project_metadata(self, project_name: str, metadata: Dict[str, Any]) -> None:
        """Update project metadata.
        
        Args:
            project_name: Name of the project
            metadata: Updated metadata
        """
        metadata_path = self.projects_path / project_name / "project.json"
        await self.write_file(metadata_path, json.dumps(metadata, indent=2))
    
    # Repository operations
    
    async def register_repository(self, repo_path: str, repo_name: str, project_name: Optional[str] = None, remote_url: Optional[str] = None, branch: Optional[str] = None) -> None:
        """Register a repository in the memory bank system.
        
        Args:
            repo_path: Path to the repository
            repo_name: Name of the repository
            project_name: Name of the associated project (optional)
            remote_url: Remote URL of the repository (optional)
            branch: Current branch of the repository (optional)
        """
        repo_record = {
            "path": repo_path,
            "name": repo_name,
            "project": project_name,
            "remote_url": remote_url,
            "branch": branch,
            "last_accessed": self.get_current_timestamp()
        }
        
        # Save repository record
        record_path = self.repositories_path / f"{repo_name}.json"
        await self.write_file(record_path, json.dumps(repo_record, indent=2))
        
        # If project is specified, update project metadata
        if project_name:
            try:
                project_metadata_path = self.projects_path / project_name / "project.json"
                if project_metadata_path.exists():
                    metadata = json.loads(await self.read_file(project_metadata_path))
                    metadata["repository"] = repo_path
                    await self.write_file(project_metadata_path, json.dumps(metadata, indent=2))
            except Exception as e:
                # Log error but don't fail the registration
                logger.error(f"Error updating project metadata: {str(e)}")
    
    async def get_repository_record(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository record by name.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Repository record or None if not found
        """
        record_path = self.repositories_path / f"{repo_name}.json"
        if record_path.exists():
            content = await self.read_file(record_path)
            return json.loads(content)
        return None
    
    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all registered repositories.
        
        Returns:
            List of repository records
        """
        repositories = []
        for file in self.repositories_path.glob("*.json"):
            content = await self.read_file(file)
            repositories.append(json.loads(content))
        return repositories
    
    async def get_repository_memory_bank_path(self, repo_name: str) -> Optional[str]:
        """Get the path to a repository memory bank.
        
        Args:
            repo_name: Name of the repository
            
        Returns:
            Path to the repository memory bank or None if not found
        """
        # Get repository record
        repo_record = await self.get_repository_record(repo_name)
        if not repo_record:
            logger.error(f"Repository {repo_name} not found in registry")
            return None
        
        # Build path to the .claude-memory directory in the repository
        repo_path = Path(repo_record["path"])
        memory_bank_path = repo_path / ".claude-memory"
        
        # Check if the directory exists
        if memory_bank_path.exists() and memory_bank_path.is_dir():
            # Update last accessed timestamp
            repo_record["last_accessed"] = self.get_current_timestamp()
            record_path = self.repositories_path / f"{repo_name}.json"
            await self.write_file(record_path, json.dumps(repo_record, indent=2))
            
            return str(memory_bank_path)
        
        # Attempt to migrate from legacy location if it exists
        legacy_path = self.repositories_path / repo_name
        if legacy_path.exists() and legacy_path.is_dir():
            # Create the .claude-memory directory if it doesn't exist
            if not memory_bank_path.exists():
                memory_bank_path.mkdir(parents=True, exist_ok=True)
            
            # Copy files from legacy path to new path
            for file_name in os.listdir(legacy_path):
                legacy_file = legacy_path / file_name
                new_file = memory_bank_path / file_name
                
                if legacy_file.is_file() and not new_file.exists():
                    try:
                        content = await self.read_file(legacy_file)
                        await self.write_file(new_file, content)
                        logger.info(f"Migrated {file_name} from legacy location to repository memory bank")
                    except Exception as e:
                        logger.error(f"Error migrating file {file_name}: {str(e)}")
            
            return str(memory_bank_path)
        
        return None
    
    # Context file operations
    
    async def get_context_file(self, memory_bank_path: str, file_name: str) -> str:
        """Get the content of a context file from a memory bank.
        
        Args:
            memory_bank_path: Path to the memory bank
            file_name: Name of the context file
            
        Returns:
            Content of the context file
        """
        file_path = Path(memory_bank_path) / file_name
        return await self.read_file(file_path)
    
    async def update_context_file(self, memory_bank_path: str, file_name: str, content: str) -> None:
        """Update a context file in a memory bank.
        
        Args:
            memory_bank_path: Path to the memory bank
            file_name: Name of the context file
            content: New content for the file
        """
        file_path = Path(memory_bank_path) / file_name
        await self.write_file(file_path, content)
        
        # Wait briefly to ensure file operations complete
        await asyncio.sleep(0.1)
        
        # Verify the file was written correctly
        try:
            read_content = await self.read_file(file_path)
            if read_content != content:
                logger.error(f"File verification failed for {file_path}")
                raise IOError(f"File verification failed for {file_path}")
        except Exception as e:
            logger.error(f"Error verifying file write: {str(e)}")
            raise
        
        # If this is a project memory bank, update the last modified timestamp
        if str(self.projects_path) in str(file_path):
            project_name = file_path.parent.name
            try:
                metadata = await self.get_project_metadata(project_name)
                metadata["lastModified"] = self.get_current_timestamp()
                await self.update_project_metadata(project_name, metadata)
            except Exception as e:
                logger.error(f"Error updating project metadata: {str(e)}")
    
    # File I/O operations
    
    async def read_file(self, path: Path) -> str:
        """Read a file asynchronously.
        
        Args:
            path: Path to the file
            
        Returns:
            Content of the file
        """
        # Use asyncio.to_thread for true async I/O (Python 3.9+)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._read_file, path)
    
    def _read_file(self, path: Path) -> str:
        """Synchronous file read for executor."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def write_file(self, path: Path, content: str) -> None:
        """Write to a file asynchronously.
        
        Args:
            path: Path to the file
            content: Content to write
        """
        # Use asyncio.to_thread for true async I/O (Python 3.9+)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._write_file, path, content)
    
    def _write_file(self, path: Path, content: str) -> None:
        """Synchronous file write for executor."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    # Utility methods
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp in ISO format
        """
        return datetime.now(UTC).isoformat()
