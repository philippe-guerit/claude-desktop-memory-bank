# Claude Desktop Memory Bank - MCP Server Implementation Guide

This guide provides practical steps for implementing the Claude Desktop Memory Bank MCP server, following the MCP specification with support for multiple memory bank types.

## Prerequisites

Before starting the implementation, ensure you have:

1. **Python** (3.8 or newer) installed
2. **Node.js** (for Claude Desktop integration)
3. **Claude Desktop** application
4. **Git** (for repository detection and integration)
5. Basic knowledge of Python programming

## Project Setup

Let's start by setting up the project structure:

```
claude-desktop-memory-bank/
├── memory_bank_server/
│   ├── __init__.py
│   ├── server.py
│   ├── context_manager.py
│   ├── memory_bank_selector.py
│   ├── storage_manager.py
│   ├── repository_utils.py
│   └── utils.py
├── storage/
│   ├── global/
│   ├── projects/
│   ├── repositories/
│   └── templates/
├── tests/
│   └── test_server.py
├── config.json
├── setup.py
└── README.md
```

## Step 1: Install Dependencies

Create a virtual environment and install the required dependencies:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install mcp httpx gitpython
```

## Step 2: Implement the Repository Utilities

Let's start by implementing utilities for Git repository detection and management:

```python
# memory_bank_server/repository_utils.py
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

class RepositoryUtils:
    @staticmethod
    def is_git_repository(path: str) -> bool:
        """Check if the given path is a git repository."""
        git_dir = os.path.join(path, '.git')
        return os.path.exists(git_dir) and os.path.isdir(git_dir)
    
    @staticmethod
    def find_repository_root(path: str) -> Optional[str]:
        """Find the nearest git repository root from a path."""
        current = os.path.abspath(path)
        while current != os.path.dirname(current):  # Stop at filesystem root
            if RepositoryUtils.is_git_repository(current):
                return current
            current = os.path.dirname(current)
        return None
    
    @staticmethod
    def get_repository_name(repo_path: str) -> str:
        """Get the name of a repository from its path."""
        return os.path.basename(repo_path)
    
    @staticmethod
    def initialize_memory_bank(repo_path: str, templates_dir: str) -> bool:
        """Initialize a .claude-memory directory in the repository."""
        memory_dir = os.path.join(repo_path, '.claude-memory')
        
        # Create directory if it doesn't exist
        if not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
        
        # Copy template files
        template_files = [f for f in os.listdir(templates_dir) if f.endswith('.md')]
        for template_file in template_files:
            source = os.path.join(templates_dir, template_file)
            destination = os.path.join(memory_dir, template_file)
            
            # Only copy if destination doesn't exist
            if not os.path.exists(destination):
                with open(source, 'r', encoding='utf-8') as src_file:
                    with open(destination, 'w', encoding='utf-8') as dest_file:
                        dest_file.write(src_file.read())
        
        return True
    
    @staticmethod
    def get_repository_info(repo_path: str) -> Dict[str, Any]:
        """Get information about a Git repository."""
        try:
            # Get repository name
            name = RepositoryUtils.get_repository_name(repo_path)
            
            # Get remote URL if available
            remote_url = ""
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
            except Exception:
                pass
            
            # Get current branch
            branch = ""
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
            except Exception:
                pass
            
            return {
                "name": name,
                "path": repo_path,
                "remote_url": remote_url,
                "branch": branch,
                "memory_bank_path": os.path.join(repo_path, '.claude-memory')
            }
        except Exception as e:
            return {
                "name": os.path.basename(repo_path),
                "path": repo_path,
                "error": str(e)
            }
```

## Step 3: Implement the Storage Manager

The storage manager will handle file operations for the memory bank:

```python
# memory_bank_server/storage_manager.py
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
```

## Step 4: Implement the Memory Bank Selector

Now let's create the memory bank selector to manage multiple memory banks:

```python
# memory_bank_server/memory_bank_selector.py
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
```

## Step 5: Implement the Context Manager

The context manager will handle the business logic for managing context files:

```python
# memory_bank_server/context_manager.py
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
```

## Step 6: Implement the MCP Server

Now let's implement the MCP server with support for multiple memory banks:

```python
# memory_bank_server/server.py
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .context_manager import ContextManager
from .storage_manager import StorageManager
from .memory_bank_selector import MemoryBankSelector
from .repository_utils import RepositoryUtils

class MemoryBankServer:
    def __init__(self, root_path: str):
        # Initialize managers
        self.storage_manager = StorageManager(root_path)
        self.memory_bank_selector = MemoryBankSelector(self.storage_manager)
        self.context_manager = ContextManager(self.storage_manager, self.memory_bank_selector)
        
        # Initialize MCP server
        self.server = Server(
            name="memory-bank",
            description="Memory Bank for Claude Desktop"
        )
        
        # Register handlers
        self._register_resource_handlers()
        self._register_tool_handlers()
        self._register_prompt_handlers()
    
    def _register_resource_handlers(self):
        """Register resource handlers for the MCP server."""
        @self.server.resource("project-brief")
        async def get_project_brief(uri: str) -> types.GetResourceResult:
            try:
                context = await self.context_manager.get_context("project_brief")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=context
                        )
                    ]
                )
            except Exception as e:
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving project brief: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("active-context")
        async def get_active_context(uri: str) -> types.GetResourceResult:
            try:
                context = await self.context_manager.get_context("active_context")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=context
                        )
                    ]
                )
            except Exception as e:
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving active context: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("progress")
        async def get_progress(uri: str) -> types.GetResourceResult:
            try:
                context = await self.context_manager.get_context("progress")
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=context
                        )
                    ]
                )
            except Exception as e:
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving progress: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("all-context")
        async def get_all_context(uri: str) -> types.GetResourceResult:
            try:
                contexts = await self.context_manager.get_all_context()
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
                memory_bank_info = f"""# Memory Bank Information
Type: {current_memory_bank['type']}
"""
                
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    memory_bank_info += f"""Repository: {repo_info.get('name', '')}
Path: {repo_info.get('path', '')}
Branch: {repo_info.get('branch', '')}
"""
                elif current_memory_bank['type'] == 'project':
                    memory_bank_info += f"""Project: {current_memory_bank.get('project', '')}
"""
                
                # Add memory bank info at the beginning
                combined = memory_bank_info + "\n\n" + "\n\n".join([
                    f"# {key.replace('_', ' ').title()}\n\n{value}" 
                    for key, value in contexts.items()
                ])
                
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=combined
                        )
                    ]
                )
            except Exception as e:
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving all context: {str(e)}"
                        )
                    ]
                )
        
        @self.server.resource("memory-bank-info")
        async def get_memory_bank_info(uri: str) -> types.GetResourceResult:
            try:
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                all_memory_banks = await self.context_manager.get_memory_banks()
                
                output = f"""# Memory Bank Information

## Current Memory Bank
Type: {current_memory_bank['type']}
"""
                
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    output += f"""Repository: {repo_info.get('name', '')}
Path: {repo_info.get('path', '')}
Branch: {repo_info.get('branch', '')}
"""
                    if 'project' in current_memory_bank:
                        output += f"Associated Project: {current_memory_bank['project']}\n"
                
                elif current_memory_bank['type'] == 'project':
                    output += f"Project: {current_memory_bank.get('project', '')}\n"
                
                output += "\n## Available Memory Banks\n"
                
                # Add global memory bank
                output += "\n### Global Memory Bank\n"
                output += f"Path: {all_memory_banks['global'][0]['path']}\n"
                
                # Add project memory banks
                if all_memory_banks['projects']:
                    output += "\n### Project Memory Banks\n"
                    for project in all_memory_banks['projects']:
                        output += f"- {project['name']}\n"
                        if 'repository' in project.get('metadata', {}):
                            output += f"  Repository: {project['metadata']['repository']}\n"
                
                # Add repository memory banks
                if all_memory_banks['repositories']:
                    output += "\n### Repository Memory Banks\n"
                    for repo in all_memory_banks['repositories']:
                        output += f"- {repo['name']} ({repo['repo_path']})\n"
                        if repo.get('project'):
                            output += f"  Associated Project: {repo['project']}\n"
                
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=output
                        )
                    ]
                )
            except Exception as e:
                return types.GetResourceResult(
                    contents=[
                        types.ResourceContent(
                            uri=uri,
                            text=f"Error retrieving memory bank information: {str(e)}"
                        )
                    ]
                )
    
    def _register_tool_handlers(self):
        """Register tool handlers for the MCP server."""
        @self.server.tool("select-memory-bank")
        async def select_memory_bank(
            type: str = "global", 
            project: Optional[str] = None, 
            repository_path: Optional[str] = None
        ) -> types.Result:
            """Select which memory bank to use for the conversation.
            
            Args:
                type: The type of memory bank to use ('global', 'project', or 'repository')
                project: The name of the project (for 'project' type)
                repository_path: The path to the repository (for 'repository' type)
            
            Returns:
                Information about the selected memory bank
            """
            try:
                if type == "global":
                    memory_bank = await self.context_manager.set_memory_bank()
                elif type == "project":
                    if not project:
                        return types.Result(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text="Project name is required for project memory bank selection."
                                )
                            ]
                        )
                    memory_bank = await self.context_manager.set_memory_bank(claude_project=project)
                elif type == "repository":
                    if not repository_path:
                        return types.Result(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text="Repository path is required for repository memory bank selection."
                                )
                            ]
                        )
                    memory_bank = await self.context_manager.set_memory_bank(repository_path=repository_path)
                else:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"Unknown memory bank type: {type}. Use 'global', 'project', or 'repository'."
                            )
                        ]
                    )
                
                # Format result based on memory bank type
                result_text = f"Selected memory bank: {memory_bank['type']}\n"
                
                if memory_bank['type'] == 'repository':
                    repo_info = memory_bank.get('repo_info', {})
                    result_text += f"Repository: {repo_info.get('name', '')}\n"
                    result_text += f"Path: {repo_info.get('path', '')}\n"
                    if repo_info.get('branch'):
                        result_text += f"Branch: {repo_info.get('branch', '')}\n"
                    if memory_bank.get('project'):
                        result_text += f"Associated Project: {memory_bank['project']}\n"
                
                elif memory_bank['type'] == 'project':
                    result_text += f"Project: {memory_bank.get('project', '')}\n"
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error selecting memory bank: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("create-project")
        async def create_project(
            name: str, 
            description: str, 
            repository_path: Optional[str] = None
        ) -> types.Result:
            """Create a new project in the memory bank.
            
            Args:
                name: The name of the project to create
                description: A brief description of the project
                repository_path: Optional path to a Git repository to associate with the project
            
            Returns:
                A confirmation message
            """
            try:
                # Validate repository path if provided
                if repository_path:
                    if not RepositoryUtils.is_git_repository(repository_path):
                        return types.Result(
                            content=[
                                types.TextContent(
                                    type="text",
                                    text=f"The path {repository_path} is not a valid Git repository."
                                )
                            ]
                        )
                
                # Create project
                project = await self.context_manager.create_project(name, description, repository_path)
                
                result_text = f"Project '{name}' created successfully.\n"
                if repository_path:
                    result_text += f"Associated with repository: {repository_path}\n"
                result_text += "This memory bank is now selected for the current conversation."
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error creating project: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("list-memory-banks")
        async def list_memory_banks() -> types.Result:
            """List all available memory banks.
            
            Returns:
                A list of available memory banks
            """
            try:
                memory_banks = await self.context_manager.get_memory_banks()
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
                result_text = "# Available Memory Banks\n\n"
                
                # Add current memory bank info
                result_text += "## Current Memory Bank\n"
                result_text += f"Type: {current_memory_bank['type']}\n"
                
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    result_text += f"Repository: {repo_info.get('name', '')}\n"
                    result_text += f"Path: {repo_info.get('path', '')}\n"
                    if repo_info.get('branch'):
                        result_text += f"Branch: {repo_info.get('branch', '')}\n"
                    if current_memory_bank.get('project'):
                        result_text += f"Associated Project: {current_memory_bank['project']}\n"
                
                elif current_memory_bank['type'] == 'project':
                    result_text += f"Project: {current_memory_bank.get('project', '')}\n"
                
                # Add global memory bank
                result_text += "\n## Global Memory Bank\n"
                result_text += f"Path: {memory_banks['global'][0]['path']}\n"
                
                # Add project memory banks
                if memory_banks['projects']:
                    result_text += "\n## Project Memory Banks\n"
                    for project in memory_banks['projects']:
                        result_text += f"- {project['name']}\n"
                        if 'repository' in project.get('metadata', {}):
                            result_text += f"  Repository: {project['metadata']['repository']}\n"
                
                # Add repository memory banks
                if memory_banks['repositories']:
                    result_text += "\n## Repository Memory Banks\n"
                    for repo in memory_banks['repositories']:
                        result_text += f"- {repo['name']} ({repo['repo_path']})\n"
                        if repo.get('project'):
                            result_text += f"  Associated Project: {repo['project']}\n"
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error listing memory banks: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("detect-repository")
        async def detect_repository(path: str) -> types.Result:
            """Detect if a path is within a Git repository.
            
            Args:
                path: The path to check
            
            Returns:
                Information about the detected repository, if any
            """
            try:
                repo_info = await self.context_manager.detect_repository(path)
                
                if not repo_info:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"No Git repository found at or above {path}."
                            )
                        ]
                    )
                
                result_text = f"Git repository detected:\n"
                result_text += f"Name: {repo_info.get('name', '')}\n"
                result_text += f"Path: {repo_info.get('path', '')}\n"
                
                if repo_info.get('branch'):
                    result_text += f"Branch: {repo_info.get('branch', '')}\n"
                
                if repo_info.get('remote_url'):
                    result_text += f"Remote URL: {repo_info.get('remote_url', '')}\n"
                
                # Check if repository has a memory bank
                memory_bank_path = repo_info.get('memory_bank_path', '')
                if memory_bank_path and os.path.exists(memory_bank_path):
                    result_text += f"Memory bank exists: Yes\n"
                else:
                    result_text += f"Memory bank exists: No\n"
                    result_text += "Use the initialize-repository-memory-bank tool to create one."
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error detecting repository: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("initialize-repository-memory-bank")
        async def initialize_repository_memory_bank(
            repository_path: str, 
            claude_project: Optional[str] = None
        ) -> types.Result:
            """Initialize a memory bank within a Git repository.
            
            Args:
                repository_path: Path to the Git repository
                claude_project: Optional Claude Desktop project to associate with this repository
            
            Returns:
                Information about the initialized memory bank
            """
            try:
                memory_bank = await self.context_manager.initialize_repository_memory_bank(
                    repository_path, 
                    claude_project
                )
                
                result_text = f"Repository memory bank initialized:\n"
                result_text += f"Path: {memory_bank['path']}\n"
                
                repo_info = memory_bank.get('repo_info', {})
                result_text += f"Repository: {repo_info.get('name', '')}\n"
                result_text += f"Repository path: {repo_info.get('path', '')}\n"
                
                if claude_project:
                    result_text += f"Associated Claude project: {claude_project}\n"
                
                result_text += "This memory bank is now selected for the current conversation."
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error initializing repository memory bank: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("update-context")
        async def update_context(context_type: str, content: str) -> types.Result:
            """Update a context file in the current memory bank.
            
            Args:
                context_type: The type of context to update (project_brief, product_context, 
                               system_patterns, tech_context, active_context, progress)
                content: The new content for the context file
            
            Returns:
                A confirmation message
            """
            try:
                memory_bank = await self.context_manager.update_context(context_type, content)
                
                result_text = f"Context '{context_type}' updated successfully in "
                result_text += f"{memory_bank['type']} memory bank."
                
                if memory_bank['type'] == 'repository':
                    repo_info = memory_bank.get('repo_info', {})
                    result_text += f"\nRepository: {repo_info.get('name', '')}"
                    if memory_bank.get('project'):
                        result_text += f"\nAssociated Project: {memory_bank['project']}"
                
                elif memory_bank['type'] == 'project':
                    result_text += f"\nProject: {memory_bank.get('project', '')}"
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error updating context: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("search-context")
        async def search_context(query: str) -> types.Result:
            """Search through context files in the current memory bank.
            
            Args:
                query: The search term to look for in context files
            
            Returns:
                Search results with matching lines
            """
            try:
                results = await self.context_manager.search_context(query)
                current_memory_bank = await self.context_manager.get_current_memory_bank()
                
                if not results:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"No results found for query: {query} in {current_memory_bank['type']} memory bank."
                            )
                        ]
                    )
                
                result_text = f"Search results for '{query}' in {current_memory_bank['type']} memory bank:\n\n"
                
                # Add memory bank info
                if current_memory_bank['type'] == 'repository':
                    repo_info = current_memory_bank.get('repo_info', {})
                    result_text += f"Repository: {repo_info.get('name', '')}\n"
                    if current_memory_bank.get('project'):
                        result_text += f"Associated Project: {current_memory_bank['project']}\n"
                
                elif current_memory_bank['type'] == 'project':
                    result_text += f"Project: {current_memory_bank.get('project', '')}\n"
                
                result_text += "\n"
                
                # Add search results
                for context_type, lines in results.items():
                    result_text += f"## {context_type.replace('_', ' ').title()}\n\n"
                    for line in lines:
                        result_text += f"- {line}\n"
                    result_text += "\n"
                
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=result_text
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error searching context: {str(e)}"
                        )
                    ]
                )
    
    def _register_prompt_handlers(self):
        """Register prompt handlers for the MCP server."""
        @self.server.prompt("create-project-brief")
        def create_project_brief() -> types.Prompt:
            return types.Prompt(
                name="Create Project Brief",
                description="Template for creating a project brief",
                content=[
                    types.TextContent(
                        type="text",
                        text="""# Project Brief Template

## Project Name
[Enter the project name here]

## Purpose
[Describe the primary purpose of this project]

## Goals
[List the main goals of the project]

## Requirements
[List key requirements]

## Scope
[Define what is in and out of scope]

## Timeline
[Provide a high-level timeline]

## Stakeholders
[List key stakeholders]

## Repository
[If applicable, specify the path to the Git repository]
"""
                    )
                ]
            )
        
        @self.server.prompt("create-update")
        def create_update() -> types.Prompt:
            return types.Prompt(
                name="Create Progress Update",
                description="Template for updating project progress",
                content=[
                    types.TextContent(
                        type="text",
                        text="""# Progress Update Template

## Completed
[List recently completed items]

## In Progress
[List items currently being worked on]

## Pending
[List upcoming items]

## Issues
[List any issues or blockers]

## Notes
[Any additional notes]
"""
                    )
                ]
            )
        
        @self.server.prompt("associate-repository")
        def associate_repository() -> types.Prompt:
            return types.Prompt(
                name="Associate Repository",
                description="Template for associating a repository with a project",
                content=[
                    types.TextContent(
                        type="text",
                        text="""# Associate Repository with Project

## Project Name
[Enter the Claude Desktop project name]

## Repository Path
[Enter the absolute path to the Git repository]

## Description
[Briefly describe the repository and its relation to the project]
"""
                    )
                ]
            )
    
    async def initialize(self) -> None:
        """Initialize the server."""
        await self.context_manager.initialize()
    
    async def run(self) -> None:
        """Run the server."""
        # Import here to avoid circular imports
        import mcp.server.stdio
        
        # Initialize the server
        await self.initialize()
        
        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, 
                write_stream,
                InitializationOptions(
                    server_name="memory-bank",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

# Main entry point
async def main():
    # Get root path for the memory bank from environment or use default
    root_path = os.environ.get("MEMORY_BANK_ROOT", os.path.expanduser("~/memory-bank"))
    
    # Create and run the server
    server = MemoryBankServer(root_path)
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 7: Update the Entry Point

Update the module's entry point in `__init__.py`:

```python
# memory_bank_server/__init__.py
from . import server

__all__ = ["server"]

def main():
    """Main entry point for the package."""
    import asyncio
    asyncio.run(server.main())
```

## Step 8: Configure Claude Desktop

To integrate with Claude Desktop, update the configuration in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "python",
      "args": ["-m", "memory_bank_server"],
      "env": {
        "MEMORY_BANK_ROOT": "/home/pjm/code/claude-desktop-memory-bank/storage",
        "ENABLE_REPO_DETECTION": "true"
      }
    }
  }
}
```

## Step 9: Install and Run

Install the package in development mode:

```bash
# From the project root directory
pip install -e .
```

After installation, you can run the server directly or let Claude Desktop start it:

```bash
# Run manually for testing
memory-bank-server
```

## Using the Memory Bank with Multiple Sources

The server now supports three types of memory banks:

1. **Global Memory Bank**: For general conversations
   - Used when no specific project or repository is selected
   - Stored in the main memory bank directory

2. **Project Memory Banks**: For Claude Desktop projects
   - Created for each Claude Desktop project
   - Can be linked to Git repositories

3. **Repository Memory Banks**: For code repositories
   - Stored directly within Git repositories (`.claude-memory` directory)
   - Can be associated with Claude Desktop projects

## Memory Bank Selection Workflow

The memory bank selection follows this workflow:

1. When starting a conversation, the server checks:
   - Is this conversation part of a Claude Desktop project?
   - Does the project have an associated repository?
   - If yes, use the repository's memory bank
   - If no, ask if the user wants to use the global memory bank

2. Users can explicitly select a memory bank using:
   - `select-memory-bank` tool with parameters for type and path
   - `detect-repository` tool to find a repository from a path
   - `initialize-repository-memory-bank` tool to create a new repository memory bank

## Conclusion

This implementation guide provides a comprehensive approach to building a multi-source Claude Desktop Memory Bank using the Model Context Protocol. The implementation supports global, project-specific, and repository-embedded memory banks to meet various use cases.

The system allows for seamless transitions between different memory bank types and provides tools for managing, searching, and updating context across all sources.
