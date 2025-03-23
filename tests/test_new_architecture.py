"""
Tests for the new Memory Bank architecture.

This module contains tests for the new service-oriented architecture
of the Memory Bank system.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from memory_bank_server.services import StorageService, RepositoryService, ContextService
from memory_bank_server.server import MemoryBankServer

class TestNewArchitecture:
    """Test case for the new Memory Bank architecture."""
    
    @pytest.fixture
    def temp_dir(self, tmpdir):
        """Create a temporary directory for testing."""
        return str(tmpdir)
    
    @pytest.fixture
    def storage_service(self, temp_dir):
        """Create a storage service for testing."""
        return StorageService(temp_dir)
    
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
        return MemoryBankServer(temp_dir)
    
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
    async def test_context_service(self, context_service, mocker):
        """Test basic context service functionality."""
        # Mock the get_context method
        mocker.patch.object(
            context_service, 
            'get_context', 
            return_value="Test context"
        )
        
        # Mock the update_context method
        mocker.patch.object(
            context_service, 
            'update_context', 
            return_value={"type": "global", "path": "/path/to/global"}
        )
        
        # Initialize the context service
        await context_service.initialize()
        
        # Test getting context
        context = await context_service.get_context("project_brief")
        assert context == "Test context"
        
        # Test updating context
        result = await context_service.update_context("project_brief", "New content")
        assert result["type"] == "global"
    
    @pytest.mark.asyncio
    async def test_direct_access(self, server, mocker):
        """Test direct access methods."""
        # Mock the context service
        mocker.patch.object(
            server.context_service,
            'get_context',
            return_value="Test context"
        )
        
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
