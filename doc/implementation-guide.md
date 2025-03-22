# Claude Desktop Memory Bank - MCP Server Implementation Guide

This guide provides practical steps for implementing the Claude Desktop Memory Bank MCP server, following the MCP specification.

## Prerequisites

Before starting the implementation, ensure you have:

1. **Python** (3.8 or newer) installed
2. **Node.js** (for Claude Desktop integration)
3. **Claude Desktop** application
4. Basic knowledge of Python programming

## Project Setup

Let's start by setting up the project structure:

```
claude-desktop-memory-bank/
├── memory_bank_server/
│   ├── __init__.py
│   ├── server.py
│   ├── context_manager.py
│   ├── storage_manager.py
│   └── utils.py
├── storage/
│   ├── templates/
│   └── projects/
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
pip install mcp httpx
```

## Step 2: Implement the Storage Manager

The storage manager will handle file operations for the memory bank:

```python
# memory_bank_server/storage_manager.py
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class StorageManager:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.templates_path = self.root_path / "templates"
        self.projects_path = self.root_path / "projects"
        
        # Ensure directories exist
        self.templates_path.mkdir(parents=True, exist_ok=True)
        self.projects_path.mkdir(parents=True, exist_ok=True)
    
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
    
    async def create_project(self, project_name: str, metadata: Dict[str, Any]) -> None:
        """Create a new project."""
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
    
    async def get_projects(self) -> List[str]:
        """Get a list of all project names."""
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
    
    async def get_context_file(self, project_name: str, file_name: str) -> str:
        """Get the content of a project context file."""
        file_path = self.projects_path / project_name / file_name
        return await self._read_file(file_path)
    
    async def update_context_file(self, project_name: str, file_name: str, content: str) -> None:
        """Update a project context file."""
        file_path = self.projects_path / project_name / file_name
        await self._write_file(file_path, content)
        
        # Update last modified in metadata
        metadata = await self.get_project_metadata(project_name)
        metadata["lastModified"] = self._get_current_timestamp()
        await self.update_project_metadata(project_name, metadata)
    
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

## Step 3: Implement the Context Manager

The context manager will handle the business logic for managing context files:

```python
# memory_bank_server/context_manager.py
from typing import Dict, List, Optional, Any
from .storage_manager import StorageManager

class ContextManager:
    def __init__(self, storage_manager: StorageManager):
        self.storage_manager = storage_manager
        self.current_project = None
    
    async def initialize(self) -> None:
        """Initialize the context manager."""
        await self.storage_manager.initialize_templates()
        
        # Set current project if any exist
        projects = await self.storage_manager.get_projects()
        if projects:
            self.current_project = projects[0]
    
    async def create_project(self, project_name: str, description: str) -> Dict[str, Any]:
        """Create a new project with initial context files."""
        metadata = {
            "name": project_name,
            "description": description,
            "created": self.storage_manager._get_current_timestamp(),
            "lastModified": self.storage_manager._get_current_timestamp()
        }
        
        await self.storage_manager.create_project(project_name, metadata)
        self.current_project = project_name
        
        return metadata
    
    async def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with their metadata."""
        project_names = await self.storage_manager.get_projects()
        projects = []
        
        for name in project_names:
            metadata = await self.storage_manager.get_project_metadata(name)
            projects.append(metadata)
        
        return projects
    
    async def set_current_project(self, project_name: str) -> Dict[str, Any]:
        """Set the current active project."""
        project_names = await self.storage_manager.get_projects()
        if project_name not in project_names:
            raise ValueError(f"Project '{project_name}' does not exist")
        
        self.current_project = project_name
        return await self.storage_manager.get_project_metadata(project_name)
    
    async def get_context(self, context_type: str) -> str:
        """Get the content of a specific context file."""
        if not self.current_project:
            raise ValueError("No active project selected")
        
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
            self.current_project, 
            file_mapping[context_type]
        )
    
    async def update_context(self, context_type: str, content: str) -> Dict[str, Any]:
        """Update a specific context file."""
        if not self.current_project:
            raise ValueError("No active project selected")
        
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
            self.current_project,
            file_mapping[context_type],
            content
        )
        
        return await self.storage_manager.get_project_metadata(self.current_project)
    
    async def search_context(self, query: str) -> Dict[str, List[str]]:
        """Search through context files for the given query."""
        if not self.current_project:
            raise ValueError("No active project selected")
        
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
            content = await self.storage_manager.get_context_file(
                self.current_project, 
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
        
        return results
    
    async def get_all_context(self) -> Dict[str, str]:
        """Get all context files for the current project."""
        if not self.current_project:
            raise ValueError("No active project selected")
        
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
            content = await self.storage_manager.get_context_file(
                self.current_project,
                file_name
            )
            result[context_type] = content
        
        return result
```

## Step 4: Implement the MCP Server

Now let's implement the MCP server itself using the Python SDK:

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

class MemoryBankServer:
    def __init__(self, root_path: str):
        # Initialize managers
        self.storage_manager = StorageManager(root_path)
        self.context_manager = ContextManager(self.storage_manager)
        
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
                combined = "\n\n".join([
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
    
    def _register_tool_handlers(self):
        """Register tool handlers for the MCP server."""
        @self.server.tool("create-project")
        async def create_project(name: str, description: str) -> types.Result:
            """Create a new project in the memory bank.
            
            Args:
                name: The name of the project to create
                description: A brief description of the project
            
            Returns:
                A confirmation message
            """
            try:
                await self.context_manager.create_project(name, description)
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Project '{name}' created successfully."
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
        
        @self.server.tool("set-active-project")
        async def set_active_project(name: str) -> types.Result:
            """Set the active project.
            
            Args:
                name: The name of the project to set as active
            
            Returns:
                A confirmation message
            """
            try:
                await self.context_manager.set_current_project(name)
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Project '{name}' is now the active project."
                        )
                    ]
                )
            except Exception as e:
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Error setting active project: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("list-projects")
        async def list_projects() -> types.Result:
            """List all projects in the memory bank.
            
            Returns:
                A list of projects with their metadata
            """
            try:
                projects = await self.context_manager.get_projects()
                result_text = "Projects:\n\n"
                for project in projects:
                    result_text += f"- {project['name']}: {project.get('description', 'No description')}\n"
                    result_text += f"  Created: {project.get('created', 'Unknown')}\n"
                    result_text += f"  Last Modified: {project.get('lastModified', 'Unknown')}\n\n"
                
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
                            text=f"Error listing projects: {str(e)}"
                        )
                    ]
                )
        
        @self.server.tool("update-context")
        async def update_context(context_type: str, content: str) -> types.Result:
            """Update a context file in the memory bank.
            
            Args:
                context_type: The type of context to update (project_brief, product_context, 
                               system_patterns, tech_context, active_context, progress)
                content: The new content for the context file
            
            Returns:
                A confirmation message
            """
            try:
                await self.context_manager.update_context(context_type, content)
                return types.Result(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Context '{context_type}' updated successfully."
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
            """Search through context files for the given query.
            
            Args:
                query: The search term to look for in context files
            
            Returns:
                Search results with matching lines
            """
            try:
                results = await self.context_manager.search_context(query)
                if not results:
                    return types.Result(
                        content=[
                            types.TextContent(
                                type="text",
                                text=f"No results found for query: {query}"
                            )
                        ]
                    )
                
                result_text = f"Search results for '{query}':\n\n"
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

## Step 5: Create the Entry Point

Create the module's entry point in `__init__.py`:

```python
# memory_bank_server/__init__.py
from . import server

__all__ = ["server"]

def main():
    """Main entry point for the package."""
    import asyncio
    asyncio.run(server.main())
```

## Step 6: Set Up Package Configuration

Create a setup.py file for the package:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="memory_bank_server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp",
        "httpx",
    ],
    entry_points={
        'console_scripts': [
            'memory-bank-server=memory_bank_server:main',
        ],
    },
)
```

## Step 7: Configure Claude Desktop

To integrate with Claude Desktop, you'll need to add an entry to the Claude Desktop configuration file. The location of this file depends on your operating system:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following configuration:

```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "python",
      "args": ["-m", "memory_bank_server"],
      "env": {
        "MEMORY_BANK_ROOT": "/home/pjm/code/claude-desktop-memory-bank/storage"
      }
    }
  }
}
```

## Step 8: Install and Run

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

## Step 9: Using the Memory Bank in Claude Desktop

Once the server is configured and Claude Desktop is restarted, you can interact with the Memory Bank using Claude Desktop:

1. **Create a Project**: Use the `create-project` tool to create a new project
2. **Update Context**: Use the `update-context` tool to update context files
3. **Search Context**: Use the `search-context` tool to search through context
4. **Access Context**: Use resources like `project-brief` or `all-context` to retrieve context information

## Troubleshooting

If you encounter issues:

1. **Check the Claude Desktop logs**:
   - On macOS: `~/Library/Logs/Claude/mcp-server-memory-bank.log`
   - On Windows: Check the Event Viewer or `%APPDATA%\Claude\logs`

2. **Run the server manually** to see any error messages:
   ```bash
   python -m memory_bank_server
   ```

3. **Verify the configuration** in Claude Desktop's config file is correct

4. **Ensure all dependencies** are properly installed

## Conclusion

This implementation guide provides a practical approach to building a Claude Desktop Memory Bank using the Model Context Protocol. The implementation provides the core functionality needed to maintain context across sessions while following the standardized MCP architecture.

Future enhancements could include:
- Advanced search capabilities using embeddings
- User interface improvements
- Integration with other data sources
- Support for remote hosting when MCP adds this capability
