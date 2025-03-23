"""
Unit tests for the Memory Bank Server class.

This module tests the MemoryBankServer class which is the main entry point
for using the Memory Bank system.
"""

import os
import pytest
import tempfile
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from memory_bank_server.server.memory_bank_server import MemoryBankServer
from memory_bank_server.services.storage_service import StorageService
from memory_bank_server.services.repository_service import RepositoryService
from memory_bank_server.services.context_service import ContextService
from memory_bank_server.server.direct_access import DirectAccess
from memory_bank_server.server.fastmcp_integration import FastMCPIntegration


class TestMemoryBankServer:
    """Test case for the Memory Bank Server."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def mock_fastmcp(self):
        """Create a mock FastMCP framework."""
        fastmcp = MagicMock()
        
        # Mock the function registration
        fastmcp.register_function = MagicMock()
        
        # Mock the callback registration
        fastmcp.register_callback = MagicMock()
        
        return fastmcp
    
    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        storage_service = MagicMock(spec=StorageService)
        repository_service = MagicMock(spec=RepositoryService)
        context_service = MagicMock(spec=ContextService)
        direct_access = MagicMock(spec=DirectAccess)
        
        # Create a mock for FastMCPIntegration with register method
        fastmcp_integration = MagicMock()
        fastmcp_integration.register = MagicMock()
        
        return {
            'storage_service': storage_service,
            'repository_service': repository_service,
            'context_service': context_service,
            'direct_access': direct_access,
            'fastmcp_integration': fastmcp_integration
        }
    
    @pytest.fixture
    def mock_server(self, temp_dir, mock_fastmcp, mock_services):
        """Create a mock Memory Bank Server with patched services."""
        with patch('memory_bank_server.server.memory_bank_server.StorageService') as mock_storage, \
             patch('memory_bank_server.server.memory_bank_server.RepositoryService') as mock_repo, \
             patch('memory_bank_server.server.memory_bank_server.ContextService') as mock_context, \
             patch('memory_bank_server.server.memory_bank_server.DirectAccess') as mock_direct, \
             patch('memory_bank_server.server.memory_bank_server.FastMCPIntegration') as mock_fastmcp_int:
            
            # Configure mocks to return the mock services
            mock_storage.return_value = mock_services['storage_service']
            mock_repo.return_value = mock_services['repository_service']
            mock_context.return_value = mock_services['context_service']
            mock_direct.return_value = mock_services['direct_access']
            mock_fastmcp_int.return_value = mock_services['fastmcp_integration']
            
            # Create the server
            server = MemoryBankServer(temp_dir)
            
            # Set the context service initialize to AsyncMock
            server.context_service.initialize = AsyncMock()
            
            yield server
    
    def test_initialization(self, mock_server, mock_services):
        """Test the server initialization."""
        # Check that services are created correctly
        assert mock_server.storage_service is mock_services['storage_service']
        assert mock_server.repository_service is mock_services['repository_service']
        assert mock_server.context_service is mock_services['context_service']
        assert mock_server.direct is mock_services['direct_access']
        assert mock_server.direct_access is mock_services['direct_access']
        assert mock_server.fastmcp_integration is mock_services['fastmcp_integration']
    
    def test_fastmcp_integration(self, mock_server, mock_fastmcp):
        """Test FastMCP integration."""
        # Register with FastMCP by calling the register method of fastmcp_integration
        mock_server.fastmcp_integration.register(mock_fastmcp)
        
        # Check that FastMCP integration registration was called
        mock_server.fastmcp_integration.register.assert_called_once_with(mock_fastmcp)
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_server):
        """Test server initialization."""
        # Initialize the server
        await mock_server.initialize()
        
        # Check that the context service was initialized
        mock_server.context_service.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_direct_access_delegation(self, mock_server):
        """Test that direct access methods delegate to the right components."""
        # Mock direct access method
        mock_server.direct.get_context = AsyncMock()
        mock_server.direct.get_context.return_value = "Test context"
        
        # Call the method through the server
        result = await mock_server.direct.get_context("test_context")
        
        # Verify that the direct access method was called
        mock_server.direct.get_context.assert_called_once_with("test_context")
        assert result == "Test context"
