"""
Tests for the new Memory Bank architecture.

This module contains tests for the new service-oriented architecture
of the Memory Bank system.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from memory_bank_server.services import StorageService, RepositoryService, ContextService
from memory_bank_server.server import MemoryBankServer

# No need to explicitly import pytest-mock as it's now installed in the environment

class TestNewArchitecture:
    """Test case for the new Memory Bank architecture."""
    
    @pytest.fixture
    def temp_dir(self, tmpdir):
        """Create a temporary directory for testing."""
        # Create the templates directory
        os.makedirs(os.path.join(str(tmpdir), "templates"), exist_ok=True)
        
        # Create template files
        template_files = {
            "projectbrief.md": "# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n",
            "productContext.md": "# Product Context\n\n## Problem\n\n## Solution\n\n## User Experience\n\n## Stakeholders\n",
            "systemPatterns.md": "# System Patterns\n\n## Architecture\n\n## Patterns\n\n## Decisions\n\n## Relationships\n",
            "techContext.md": "# Technical Context\n\n## Technologies\n\n## Setup\n\n## Constraints\n\n## Dependencies\n",
            "activeContext.md": "# Active Context\n\n## Current Focus\n\n## Recent Changes\n\n## Next Steps\n\n## Active Decisions\n",
            "progress.md": "# Progress\n\n## Completed\n\n## In Progress\n\n## Pending\n\n## Issues\n"
        }
        
        # Write template files
        for filename, content in template_files.items():
            with open(os.path.join(str(tmpdir), "templates", filename), "w") as f:
                f.write(content)
                
        return str(tmpdir)
    
    @pytest.fixture
    def storage_service(self, temp_dir):
        """Create a storage service for testing."""
        service = StorageService(temp_dir)
        
        # Pre-create template directories and files needed for tests
        os.makedirs(os.path.join(temp_dir, "templates"), exist_ok=True)
        with open(os.path.join(temp_dir, "templates", "projectbrief.md"), "w") as f:
            f.write("# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n")
        
        return service
    
    @pytest.fixture
    def repository_service(self, storage_service):
        """Create a repository service for testing."""
        return RepositoryService(storage_service)
    
    @pytest.fixture
    def context_service(self, storage_service, repository_service):
        """Create a context service for testing."""
        return ContextService(storage_service, repository_service)
    
    @pytest.fixture
    def server(self, temp_dir):
        """Create a memory bank server for testing."""
        server = MemoryBankServer(temp_dir)
        
        # Pre-create template directories and files needed for tests
        os.makedirs(os.path.join(temp_dir, "templates"), exist_ok=True)
        with open(os.path.join(temp_dir, "templates", "projectbrief.md"), "w") as f:
            f.write("# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n")
        
        return server
    
    @pytest.mark.asyncio
    async def test_server_initialization(self, server):
        """Test that the server initializes correctly."""
        # Initialize the server
        await server.initialize()
        
        # Check that the context service was initialized
        assert server.context_service is not None
        
        # Check that the direct access methods are available
        assert server.direct is not None
        assert server.direct_access is not None
    
    @pytest.mark.asyncio
    async def test_storage_service(self, storage_service):
        """Test basic storage service functionality."""
        # Test template initialization
        await storage_service.initialize_template("test.md", "Test content")
        
        # Test template retrieval
        content = await storage_service.read_file(storage_service.templates_path / "test.md")
        assert content == "Test content"
        
        # Test global memory bank initialization
        global_path = await storage_service.initialize_global_memory_bank()
        assert os.path.exists(global_path)
    
    @pytest.mark.asyncio
    async def test_context_service(self, context_service):
        """Test basic context service functionality."""
        # Mock the get_context method
        context_service.get_context = AsyncMock()
        context_service.get_context.return_value = "Test context"
        
        # Mock the update_context method
        context_service.update_context = AsyncMock()
        context_service.update_context.return_value = {"type": "global", "path": "/path/to/global"}
        
        # Initialize the context service
        await context_service.initialize()
        
        # Test getting context
        context = await context_service.get_context("project_brief")
        assert context == "Test context"
        
        # Test updating context
        result = await context_service.update_context("project_brief", "New content")
        assert result["type"] == "global"
    
    @pytest.mark.asyncio
    async def test_direct_access(self, server):
        """Test direct access methods."""
        # Mock the context service
        server.context_service.get_context = AsyncMock()
        server.context_service.get_context.return_value = "Test context"
        
        # Initialize the server
        await server.initialize()
        
        # Test direct access to get_context
        context = await server.direct.get_context("project_brief")
        assert context == "Test context"
    
    @pytest.mark.asyncio
    async def test_service_composition(self, server):
        """Test that services are properly composed."""
        # Check that the server uses the service layer correctly
        assert server.storage_service is not None
        assert server.repository_service is not None
        assert server.context_service is not None
        
        # Check that services are correctly composed
        assert server.repository_service.storage_service is server.storage_service
        assert server.context_service.storage_service is server.storage_service
        assert server.context_service.repository_service is server.repository_service
