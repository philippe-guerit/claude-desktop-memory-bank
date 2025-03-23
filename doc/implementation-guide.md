# Claude Desktop Memory Bank - Implementation Guide

This guide provides practical steps for implementing the Claude Desktop Memory Bank MCP server using the layered architecture approach.

## Architecture Overview

The Memory Bank system uses a layered architecture with clear separation of concerns:

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│                 │      │                 │      │                 │
│  Core Business  │◄────►│ Service Layer   │◄────►│ Integration     │
│  Logic Layer    │      │                 │      │ Layer           │
│                 │      │                 │      │                 │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

## Prerequisites

Before starting the implementation, ensure you have:

1. **Python** (3.8 or newer) installed
2. **Node.js** (for Claude Desktop integration)
3. **Claude Desktop** application
4. **Git** (for repository detection and integration)
5. Basic knowledge of Python programming

## Project Structure

Create the project structure following the layered architecture:

```
claude-desktop-memory-bank/
├── memory_bank_server/
│   ├── __init__.py
│   ├── __main__.py
│   ├── core/                   # Core business logic layer
│   │   ├── __init__.py
│   │   ├── context.py          # Context management functions
│   │   └── memory_bank.py      # Memory bank management functions
│   ├── services/               # Service layer
│   │   ├── __init__.py
│   │   ├── context_service.py  # Context orchestration
│   │   ├── repository_service.py # Repository management
│   │   └── storage_service.py  # File I/O operations
│   ├── server/                 # Integration layer
│   │   ├── __init__.py
│   │   ├── direct_access.py    # Direct API access
│   │   ├── fastmcp_integration.py # FastMCP framework integration
│   │   └── memory_bank_server.py # Main server class
│   └── prompt_templates/       # MCP prompt templates
│       └── default_custom_instruction.md
├── storage/                    # Data storage directory
│   ├── global/
│   ├── projects/
│   ├── repositories/
│   └── templates/
├── tests/                      # Unit and integration tests
│   └── ...
├── config.json                 # Configuration file
├── setup.py                    # Package setup
└── README.md                   # Documentation
```

## Step 1: Set up the Project

Create the basic project structure and virtual environment:

```bash
# Create project directory
mkdir -p claude-desktop-memory-bank/memory_bank_server/{core,services,server,prompt_templates}
mkdir -p claude-desktop-memory-bank/storage/{global,projects,repositories,templates}
mkdir -p claude-desktop-memory-bank/tests

# Initialize virtual environment
cd claude-desktop-memory-bank
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install mcp httpx gitpython
```

## Step 2: Implement the Core Business Logic Layer

The core layer contains pure, framework-agnostic functions with no external dependencies.

### memory_bank.py

```python
# memory_bank_server/core/memory_bank.py
"""
Core business logic for Memory Bank management.

This module contains pure, framework-agnostic functions for
managing memory banks, independent of the FastMCP integration.
"""

import os
from typing import Dict, List, Optional, Any

async def start_memory_bank(
    context_service,
    prompt_name: Optional[str] = None,
    auto_detect: bool = True,
    current_path: Optional[str] = None,
    force_type: Optional[str] = None
) -> Dict[str, Any]:
    """Core business logic for starting a memory bank."""
    # Initialize tracking variables
    actions_taken = []
    selected_memory_bank = None
    
    # Use current working directory if path not provided
    if not current_path:
        current_path = os.getcwd()
    
    # Step 1: Auto-detect repository if enabled
    detected_repo = None
    if auto_detect and not force_type:
        detected_repo = await detect_repository(context_service, current_path)
        
        if detected_repo:
            actions_taken.append(f"Detected repository: {detected_repo.get('name', '')}")
    
    # Step 2: Initialize repository memory bank if needed
    if detected_repo and not force_type:
        # Check if memory bank exists for this repository
        memory_bank_path = detected_repo.get('memory_bank_path')
        if not memory_bank_path or not os.path.exists(memory_bank_path):
            repo_memory_bank = await initialize_repository_memory_bank(
                context_service,
                detected_repo.get('path', '')
            )
            actions_taken.append(f"Initialized repository memory bank for: {detected_repo.get('name', '')}")
            selected_memory_bank = repo_memory_bank
        else:
            actions_taken.append(f"Using existing repository memory bank: {detected_repo.get('name', '')}")
    
    # Step 3: Select appropriate memory bank based on detection or force_type
    if force_type:
        if force_type == "global":
            selected_memory_bank = await select_memory_bank(context_service)
            actions_taken.append("Forced selection of global memory bank")
        elif force_type.startswith("project:"):
            project_name = force_type.split(":", 1)[1]
            selected_memory_bank = await select_memory_bank(
                context_service, 
                type="project", 
                project_name=project_name
            )
            actions_taken.append(f"Forced selection of project memory bank: {project_name}")
        elif force_type.startswith("repository:"):
            repo_path = force_type.split(":", 1)[1]
            selected_memory_bank = await select_memory_bank(
                context_service,
                type="repository",
                repository_path=repo_path
            )
            actions_taken.append(f"Forced selection of repository memory bank: {repo_path}")
        else:
            actions_taken.append(f"Warning: Invalid force_type: {force_type}. Using default selection.")
            
    elif detected_repo and not selected_memory_bank:
        # We detected a repo but didn't initialize a memory bank (it already existed)
        selected_memory_bank = await select_memory_bank(
            context_service,
            type="repository",
            repository_path=detected_repo.get('path', '')
        )
        actions_taken.append(f"Selected repository memory bank: {detected_repo.get('name', '')}")
    
    # If no memory bank was selected yet, get the current memory bank
    if not selected_memory_bank:
        selected_memory_bank = await context_service.get_current_memory_bank()
        actions_taken.append(f"Using current memory bank: {selected_memory_bank['type']}")
    
    # Format result
    result = {
        "selected_memory_bank": selected_memory_bank,
        "actions_taken": actions_taken,
        "prompt_name": prompt_name
    }
    
    return result

async def select_memory_bank(
    context_service,
    type: str = "global", 
    project_name: Optional[str] = None, 
    repository_path: Optional[str] = None
) -> Dict[str, Any]:
    """Core logic for selecting a memory bank."""
    return await context_service.set_memory_bank(
        type=type,
        project_name=project_name,
        repository_path=repository_path
    )

# Additional core functions for memory bank operations...
```

### context.py

```python
# memory_bank_server/core/context.py
"""
Core business logic for context management.

This module contains pure, framework-agnostic functions for
managing context content, independent of the FastMCP integration.
"""

from typing import Dict, List, Optional, Any

async def get_context(context_service, context_type: str) -> str:
    """Core logic for getting context content."""
    return await context_service.get_context(context_type)

async def update_context(context_service, context_type: str, content: str) -> Dict[str, Any]:
    """Core logic for updating context content."""
    return await context_service.update_context(context_type, content)

async def search_context(context_service, query: str) -> Dict[str, List[str]]:
    """Core logic for searching context content."""
    return await context_service.search_context(query)

async def bulk_update_context(context_service, updates: Dict[str, str]) -> Dict[str, Any]:
    """Core logic for bulk updating multiple context files."""
    return await context_service.bulk_update_context(updates)

async def get_all_context(context_service) -> Dict[str, str]:
    """Core logic for getting all context files."""
    return await context_service.get_all_context()

# Additional core functions for context operations...
```

## Step 3: Implement the Service Layer

The service layer encapsulates related functionality and orchestrates the core business logic.

### storage_service.py

```python
# memory_bank_server/services/storage_service.py
"""
Storage service for Memory Bank.

This service handles all file I/O operations for the Memory Bank system.
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class StorageService:
    """Service for handling storage operations in the Memory Bank system."""
    
    def __init__(self, root_path: str):
        """Initialize the storage service."""
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
    
    # Implement methods for file operations, template management,
    # and memory bank initialization...
```

### repository_service.py

```python
# memory_bank_server/services/repository_service.py
"""
Repository service for Memory Bank.

This service handles Git repository detection and management.
"""

import os
import subprocess
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

from .storage_service import StorageService

class RepositoryService:
    """Service for handling Git repository operations in the Memory Bank system."""
    
    def __init__(self, storage_service: StorageService):
        """Initialize the repository service."""
        self.storage_service = storage_service
    
    async def detect_repository(self, path: str) -> Optional[Dict[str, Any]]:
        """Detect if a path is within a Git repository."""
        # Implementation...
    
    async def initialize_repository_memory_bank(
        self, 
        repo_path: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initialize a memory bank for a repository."""
        # Implementation...
    
    # Helper methods for Git operations...
```

### context_service.py

```python
# memory_bank_server/services/context_service.py
"""
Context service for Memory Bank.

This service handles context management operations including updating,
searching, and retrieving context.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from .storage_service import StorageService
from .repository_service import RepositoryService

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
        """Initialize the context service."""
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
    
    # Implement methods for memory bank management, context operations,
    # searching, and updating context...
```

## Step 4: Implement the Integration Layer

The integration layer provides adapters to connect the core logic to external frameworks.

### direct_access.py

```python
# memory_bank_server/server/direct_access.py
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
    search_context,
    bulk_update_context,
    auto_summarize_context,
    prune_context,
    get_all_context,
    get_memory_bank_info
)

logger = logging.getLogger(__name__)

class DirectAccess:
    """Direct access methods for Memory Bank functionality."""
    
    def __init__(self, context_service):
        """Initialize the direct access methods."""
        self.context_service = context_service
    
    # Implement methods that map directly to core functions...
```

### fastmcp_integration.py

```python
# memory_bank_server/server/fastmcp_integration.py
"""
FastMCP integration for Memory Bank.

This module contains adapter functions that connect the core business logic
to the FastMCP framework.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Callable

from mcp.server import FastMCP

from ..core import (
    start_memory_bank,
    select_memory_bank,
    list_memory_banks,
    detect_repository,
    initialize_repository_memory_bank,
    create_project,
    get_context,
    update_context,
    search_context,
    bulk_update_context,
    auto_summarize_context,
    prune_context,
    get_all_context,
    get_memory_bank_info
)

logger = logging.getLogger(__name__)

class FastMCPIntegration:
    """Integration layer between Memory Bank core logic and FastMCP."""
    
    def __init__(self, context_service):
        """Initialize the FastMCP integration."""
        self.context_service = context_service
        self.server = None
    
    def initialize(self, custom_instructions: str) -> None:
        """Initialize the FastMCP server."""
        # Implementation...
    
    def is_available(self) -> bool:
        """Check if FastMCP integration is available."""
        return self.server is not None
    
    def register_handlers(self) -> None:
        """Register handlers with the FastMCP server."""
        if not self.is_available():
            logger.warning("Skipping handler registration - FastMCP not available")
            return
        
        self._register_resource_handlers()
        self._register_tool_handlers()
        self._register_prompt_handlers()
    
    # Implement methods for registering resources, tools, and prompts...
```

### memory_bank_server.py

```python
# memory_bank_server/server/memory_bank_server.py
"""
Main server class for Memory Bank.

This module contains the main server class that coordinates all components.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any

from ..services import StorageService, RepositoryService, ContextService
from .fastmcp_integration import FastMCPIntegration
from .direct_access import DirectAccess

logger = logging.getLogger(__name__)

class MemoryBankServer:
    """Main server class for Memory Bank system."""
    
    def __init__(self, root_path: str):
        """Initialize the Memory Bank server."""
        logger.info(f"Initializing Memory Bank Server with root path: {root_path}")
        
        # Initialize service layer
        self.storage_service = StorageService(root_path)
        self.repository_service = RepositoryService(self.storage_service)
        self.context_service = ContextService(self.storage_service, self.repository_service)
        
        # Initialize integration layers
        self._initialize_integrations()
        
        # Expose direct access methods
        self.direct = self.direct_access
    
    def _initialize_integrations(self):
        """Initialize integration layers."""
        # Initialize direct access methods
        self.direct_access = DirectAccess(self.context_service)
        
        # Initialize FastMCP integration
        self.fastmcp_integration = FastMCPIntegration(self.context_service)
        
        # Load custom instructions for FastMCP
        custom_instructions = self._load_custom_instructions()
        
        # Initialize FastMCP server
        self.fastmcp_integration.initialize(custom_instructions)
        
        # Register handlers
        if self.fastmcp_integration.is_available():
            self.fastmcp_integration.register_handlers()
    
    async def initialize(self) -> None:
        """Initialize the server."""
        logger.info("Initializing Memory Bank server")
        await self.context_service.initialize()
    
    async def run(self) -> None:
        """Run the server."""
        logger.info("Starting Memory Bank server")
        
        try:
            # Initialize the server
            await self.initialize()
            
            # Check if FastMCP is available
            if self.fastmcp_integration.is_available():
                # Run the server with FastMCP
                logger.info("Memory Bank server running with FastMCP integration")
                await self.fastmcp_integration.run()
            else:
                # Run in standalone mode
                logger.info("Memory Bank server running in standalone mode")
                await self._run_standalone()
        except Exception as e:
            # Log any unexpected errors to stderr to help with debugging
            import sys
            print(f"Memory Bank server error: {str(e)}", file=sys.stderr)
            logger.error(f"Memory Bank server error: {str(e)}", exc_info=True)
            raise  # Re-raise the exception to properly exit the server
    
    # Additional methods for server operation...
```

## Step 5: Create Entry Points

### __main__.py

```python
# memory_bank_server/__main__.py
import sys
import logging
import asyncio
from .server.memory_bank_server import MemoryBankServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    """Entry point for running the package as a module."""
    try:
        # Print startup message to stderr for debugging
        print("Starting Memory Bank MCP server...", file=sys.stderr)
        
        # Get root path for the memory bank from environment or use default
        import os
        root_path = os.environ.get("MEMORY_BANK_ROOT", os.path.expanduser("~/memory-bank"))
        
        # Create and run the server
        server = MemoryBankServer(root_path)
        asyncio.run(server.run())
    except Exception as e:
        # Log any uncaught exceptions
        print(f"Error in Memory Bank MCP server: {str(e)}", file=sys.stderr)
        logger.error(f"Error in Memory Bank MCP server: {str(e)}", exc_info=True)
        sys.exit(1)
```

### __init__.py

```python
# memory_bank_server/__init__.py
"""
Claude Desktop Memory Bank - Autonomous context management for Claude Desktop.

This package provides a Model Context Protocol (MCP) server that enables Claude Desktop
to maintain context and memory across sessions.
"""

import sys
import asyncio
import logging
from .server.memory_bank_server import MemoryBankServer

__version__ = "0.1.0"
__all__ = ["MemoryBankServer"]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for the package."""
    try:
        # Print startup message to stderr for debugging
        print("Starting Memory Bank MCP server...", file=sys.stderr)
        
        # Get root path for the memory bank from environment or use default
        import os
        root_path = os.environ.get("MEMORY_BANK_ROOT", os.path.expanduser("~/memory-bank"))
        
        # Create and run the server
        server = MemoryBankServer(root_path)
        asyncio.run(server.run())
    except Exception as e:
        # Log any uncaught exceptions
        print(f"Error in Memory Bank MCP server: {str(e)}", file=sys.stderr)
        logger.error(f"Error in Memory Bank MCP server: {str(e)}", exc_info=True)
        sys.exit(1)
```

## Step 6: Package Configuration

### setup.py

```python
from setuptools import setup, find_packages

setup(
    name="claude-desktop-memory-bank",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "mcp",
        "httpx",
        "gitpython",
    ],
    entry_points={
        "console_scripts": [
            "memory-bank-server=memory_bank_server:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Autonomous memory system for Claude Desktop",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/claude-desktop-memory-bank",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
```

## Step 7: Configure Claude Desktop

To integrate with Claude Desktop, create a configuration file:

```json
{
  "mcpServers": {
    "memory-bank": {
      "command": "python",
      "args": ["-m", "memory_bank_server"],
      "env": {
        "MEMORY_BANK_ROOT": "/path/to/your/storage/directory",
        "ENABLE_REPO_DETECTION": "true"
      }
    }
  }
}
```

Place this file in the Claude Desktop configuration directory:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## Step 8: Testing

Create comprehensive tests for each layer to ensure proper functionality:

1. **Core Layer Tests**: Test the pure business logic functions
2. **Service Layer Tests**: Test the service components with mocked dependencies
3. **Integration Layer Tests**: Test the adapters with mocked services
4. **End-to-End Tests**: Test the complete system with real file I/O

## Deployment

For deployment:

1. **Development Installation**:
   ```bash
   # Install in development mode
   pip install -e .
   ```

2. **Production Installation**:
   ```bash
   # Build package
   python setup.py sdist bdist_wheel
   
   # Install package
   pip install dist/claude_desktop_memory_bank-0.1.0-py3-none-any.whl
   ```

## Conclusion

This implementation guide provides a comprehensive approach to building the Claude Desktop Memory Bank using a clean, layered architecture. By following this approach, you'll create a system that is:

1. **Easy to maintain**: Clear separation of concerns allows for isolated changes
2. **Highly testable**: Pure business logic can be tested independently 
3. **Framework agnostic**: Core logic doesn't depend on external frameworks
4. **Flexible**: New integrations can be added without changing the core logic
5. **Robust**: System continues to function even if parts of it fail

The layered architecture approach ensures the system can grow and adapt over time while maintaining a clean, maintainable codebase.
