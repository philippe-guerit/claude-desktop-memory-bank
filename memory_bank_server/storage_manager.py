import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

class StorageManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.global_path = self.root_path / "global"
        self.projects_path = self.root_path / "projects"
        self.repositories_path = self.root_path / "repositories"
        self.templates_path = self.root_path / "templates"
        
        # Ensure directories exist
        self.global_path.mkdir(parents=True, exist_ok=True)
        self.projects_path.mkdir(parents=True, exist_ok=True)
        self.repositories_path.mkdir(parents=True, exist_ok=True)
        self.templates_path.mkdir(parents=True, exist_ok=True)
    
    async def initialize_template(self, template_name: str, content: str) -> None:
        """Initialize a template file if it doesn't exist."""
        template_path = self.templates_path / template_name
        if not template_path.exists():
            await self._write_file(template_path, content)
    
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
        """Get the content of a template file."""
        template_path = self.templates_path / template_name
        return await self._read_file(template_path)
    
    async def initialize_global_memory_bank(self) -> None:
        """Initialize the global memory bank if it doesn't exist."""
        # Check if global memory bank exists
        if not any(self.global_path.iterdir()):
            # Initialize files from templates
            for template_name in ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                                "techContext.md", "activeContext.md", "progress.md"]:
                template_content = await self.get_template(template_name)
                file_path = self.global_path / template_name
                await self._write_file(file_path, template_content)
    
    async def create_project_memory_bank(self, project_name: str, metadata: Dict[str, Any]) -> None:
        """Create a new project memory bank."""
        project_path = self.projects_path / project_name
        project_path.mkdir(exist_ok=True)
        
        # Create project metadata file
        metadata_path = project_path / "project.json"
        await self._write_file(metadata_path, json.dumps(metadata, indent=2))
        
        # Initialize project files from templates
        for template_name in ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                            "techContext.md", "activeContext.md", "progress.md"]:
            template_content = await self.get_template(template_name)
            file_path = project_path / template_name
            await self._write_file(file_path, template_content)
    
    async def register_repository(self, repo_path: str, project_name: Optional[str] = None) -> None:
        """Register a repository in the memory bank system."""
        repo_name = os.path.basename(repo_path)
        repo_record = {
            "path": repo_path,
            "name": repo_name,
            "project": project_name
        }
        
        # Save repository record
        record_path = self.repositories_path / f"{repo_name}.json"
        await self._write_file(record_path, json.dumps(repo_record, indent=2))
        
        # If project is specified, update project metadata
        if project_name:
            project_metadata_path = self.projects_path / project_name / "project.json"
            if project_metadata_path.exists():
                metadata = json.loads(await self._read_file(project_metadata_path))
                metadata["repository"] = repo_path
                await self._write_file(project_metadata_path, json.dumps(metadata, indent=2))
    
    async def get_repository_record(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get repository record by name."""
        record_path = self.repositories_path / f"{repo_name}.json"
        if record_path.exists():
            content = await self._read_file(record_path)
            return json.loads(content)
        return None
    
    async def get_repositories(self) -> List[Dict[str, Any]]:
        """Get all registered repositories."""
        repositories = []
        for file in self.repositories_path.glob("*.json"):
            content = await self._read_file(file)
            repositories.append(json.loads(content))
        return repositories
    
    async def get_project_memory_banks(self) -> List[str]:
        """Get a list of all project memory bank names."""
        return [p.name for p in self.projects_path.iterdir() if p.is_dir()]
    
    async def get_project_metadata(self, project_name: str) -> Dict[str, Any]:
        """Get project metadata."""
        metadata_path = self.projects_path / project_name / "project.json"
        content = await self._read_file(metadata_path)
        return json.loads(content)
    
    async def update_project_metadata(self, project_name: str, metadata: Dict[str, Any]) -> None:
        """Update project metadata."""
        metadata_path = self.projects_path / project_name / "project.json"
        await self._write_file(metadata_path, json.dumps(metadata, indent=2))
    
    async def get_context_file(self, memory_bank_path: str, file_name: str) -> str:
        """Get the content of a context file from a memory bank."""
        file_path = Path(memory_bank_path) / file_name
        return await self._read_file(file_path)
    
    async def update_context_file(self, memory_bank_path: str, file_name: str, content: str) -> None:
        """Update a context file in a memory bank."""
        file_path = Path(memory_bank_path) / file_name
        await self._write_file(file_path, content)
        
        # If this is a project memory bank, update the last modified timestamp
        if str(self.projects_path) in str(file_path):
            project_name = file_path.parent.name
            try:
                metadata = await self.get_project_metadata(project_name)
                metadata["lastModified"] = self._get_current_timestamp()
                await self.update_project_metadata(project_name, metadata)
            except Exception:
                pass
    
    async def _read_file(self, path: Path) -> str:
        """Read a file asynchronously."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def _write_file(self, path: Path, content: str) -> None:
        """Write to a file asynchronously."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
