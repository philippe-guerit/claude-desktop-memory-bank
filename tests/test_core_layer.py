"""
Unit tests for the core layer.

This module contains tests for the pure business logic functions in the core layer.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from memory_bank_server.core import (
    start_memory_bank,
    select_memory_bank,
    list_memory_banks,
    get_context,
    bulk_update_context,
    get_all_context,
    get_memory_bank_info
)

class TestCoreLayer:
    """Test case for core layer functions."""
    
    @pytest.fixture
    def mock_context_service(self):
        """Create a mock context service."""
        context_service = MagicMock()
        
        # Mock repository service
        context_service.repository_service = MagicMock()
        
        # Mock context service methods
        context_service.set_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        context_service.get_current_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        context_service.get_memory_banks.return_value = {
            'global': [{'path': '/path/to/global'}],
            'projects': [{'name': 'test-project'}],
            'repositories': [{'name': 'test-repo', 'repo_path': '/path/to/repo'}]
        }
        context_service.get_context.return_value = 'Context content'
        context_service.bulk_update_context.return_value = {'type': 'global', 'path': '/path/to/global'}
        context_service.get_all_context.return_value = {
            'project_brief': 'Project brief content',
            'active_context': 'Active context content'
        }
        
        return context_service
    
    @pytest.mark.asyncio
    async def test_start_memory_bank(self, mock_context_service):
        """Test start_memory_bank function."""
        # Call the function
        result = await start_memory_bank(
            mock_context_service,
            prompt_name='test-prompt',
            auto_detect=True,
            current_path='/path/to/repo',
            force_type=None
        )
        
        # Verify the result
        assert 'selected_memory_bank' in result
        assert 'actions_taken' in result
        assert 'prompt_name' in result
        assert result['prompt_name'] == 'test-prompt'
    
    @pytest.mark.asyncio
    async def test_select_memory_bank(self, mock_context_service):
        """Test select_memory_bank function."""
        # Call the function
        result = await select_memory_bank(
            mock_context_service,
            type='repository',
            project_name=None,
            repository_path='/path/to/repo'
        )
        
        # Verify the result
        assert result['type'] == 'repository'
        assert result['path'] == '/path/to/memory-bank'
        
        # Verify the correct methods were called
        mock_context_service.set_memory_bank.assert_called_once_with(
            type='repository',
            project_name=None,
            repository_path='/path/to/repo'
        )
    
    @pytest.mark.asyncio
    async def test_list_memory_banks(self, mock_context_service):
        """Test list_memory_banks function."""
        # Call the function
        result = await list_memory_banks(mock_context_service)
        
        # Verify the result
        assert 'current' in result
        assert 'available' in result
        assert result['current']['type'] == 'repository'
        assert 'global' in result['available']
        assert 'projects' in result['available']
        assert 'repositories' in result['available']
        
        # Verify the correct methods were called
        mock_context_service.get_current_memory_bank.assert_called_once()
        mock_context_service.get_memory_banks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_context(self, mock_context_service):
        """Test get_context function."""
        # Call the function
        result = await get_context(mock_context_service, 'project_brief')
        
        # Verify the result
        assert result == 'Context content'
        
        # Verify the correct methods were called
        mock_context_service.get_context.assert_called_once_with('project_brief')
    
    @pytest.mark.asyncio
    async def test_bulk_update_context(self, mock_context_service):
        """Test bulk_update_context function."""
        # Call the function
        updates = {
            'project_brief': 'New project brief',
            'active_context': 'New active context'
        }
        result = await bulk_update_context(mock_context_service, updates)
        
        # Verify the result
        assert result['type'] == 'global'
        assert result['path'] == '/path/to/global'
        
        # Verify the correct methods were called
        mock_context_service.bulk_update_context.assert_called_once_with(updates)
    
    @pytest.mark.asyncio
    async def test_get_all_context(self, mock_context_service):
        """Test get_all_context function."""
        # Call the function
        result = await get_all_context(mock_context_service)
        
        # Verify the result
        assert 'project_brief' in result
        assert 'active_context' in result
        assert result['project_brief'] == 'Project brief content'
        assert result['active_context'] == 'Active context content'
        
        # Verify the correct methods were called
        mock_context_service.get_all_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_memory_bank_info(self, mock_context_service):
        """Test get_memory_bank_info function."""
        # Call the function
        result = await get_memory_bank_info(mock_context_service)
        
        # Verify the result
        assert 'current' in result
        assert 'all' in result
        assert result['current']['type'] == 'repository'
        
        # Verify the correct methods were called
        mock_context_service.get_current_memory_bank.assert_called_once()
        mock_context_service.get_memory_banks.assert_called_once()
