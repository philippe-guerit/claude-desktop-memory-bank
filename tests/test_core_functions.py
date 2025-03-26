"""
Unit tests for core business logic functions.

These tests verify that the core functions work correctly
independent of the FastMCP integration.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from memory_bank_server.core.memory_bank import (
    activate,
    select,
    list
)

from memory_bank_server.core.context import (
    update,
    get_context,
    get_all_context,
    get_memory_bank_info
)

class TestMemoryBankCoreFunctions:
    """Test case for Memory Bank core functions."""
    
    @pytest.fixture
    def mock_context_manager(self):
        """Create a mock context manager for testing."""
        context_manager = MagicMock()
        
        # Mock repository service
        repository_service = MagicMock()
        repository_service.detect_repository = AsyncMock()
        repository_service.detect_repository.return_value = {
            'name': 'test-repo',
            'path': '/path/to/repo',
            'branch': 'main',
            'memory_bank_path': '/path/to/memory-bank'
        }
        repository_service.initialize_repository_memory_bank = AsyncMock()
        repository_service.initialize_repository_memory_bank.return_value = {
            'type': 'repository',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        context_manager.repository_service = repository_service
        
        # Mock memory bank selection
        context_manager.set_memory_bank = AsyncMock()
        context_manager.set_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock current memory bank
        context_manager.get_current_memory_bank = AsyncMock()
        context_manager.get_current_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock context operations
        context_manager.bulk_update_context = AsyncMock()
        context_manager.bulk_update_context.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        
        # Mock context getters
        context_manager.get_context = AsyncMock()
        context_manager.get_context.return_value = "Sample context content"
        
        context_manager.get_all_context = AsyncMock()
        context_manager.get_all_context.return_value = {
            'project_brief': 'Project brief content',
            'active_context': 'Active context content',
            'progress': 'Progress content'
        }
        
        context_manager.get_memory_banks = AsyncMock()
        context_manager.get_memory_banks.return_value = {
            'global': [{'path': '/path/to/global'}],
            'projects': [
                {'name': 'test-project', 'metadata': {}}
            ],
            'repositories': [
                {'name': 'test-repo', 'repo_path': '/path/to/repo'}
            ]
        }
        
        return context_manager
    
    @pytest.mark.asyncio
    async def test_activate(self, mock_context_manager):
        """Test activate core function."""
        with patch('memory_bank_server.core.memory_bank.activate', new_callable=AsyncMock) as mock_activate:
            mock_activate.return_value = {
                'selected_memory_bank': {'type': 'repository'},
                'actions_taken': ['detected repository'],
                'prompt_name': None
            }
            
            # Call the function
            result = await mock_activate(
                mock_context_manager,
                prompt_name=None,
                auto_detect=True,
                current_path='/path/to/repo',
                force_type=None
            )
            
            # Verify that the function was called correctly
            mock_activate.assert_called_once()
            
            # Verify the response structure
            assert 'selected_memory_bank' in result
            assert 'actions_taken' in result
            assert 'prompt_name' in result
    
    @pytest.mark.asyncio
    async def test_select(self, mock_context_manager):
        """Test select core function."""
        # Test with global type
        result = await select(
            mock_context_manager,
            type='global'
        )
        
        mock_context_manager.set_memory_bank.assert_called_with(
            type='global',
            project_name=None,
            repository_path=None
        )
        
        # Test with project type
        result = await select(
            mock_context_manager,
            type='project',
            project_name='test-project'
        )
        
        mock_context_manager.set_memory_bank.assert_called_with(
            type='project',
            project_name='test-project',
            repository_path=None
        )
        
        # Test with repository type
        result = await select(
            mock_context_manager,
            type='repository',
            repository_path='/path/to/repo'
        )
        
        mock_context_manager.set_memory_bank.assert_called_with(
            type='repository',
            project_name=None,
            repository_path='/path/to/repo'
        )
    
    @pytest.mark.asyncio
    async def test_update(self, mock_context_manager):
        """Test update core function."""
        updates = {
            'project_brief': 'New project brief content',
            'active_context': 'New active context content'
        }
        
        result = await update(
            mock_context_manager,
            updates
        )
        
        mock_context_manager.bulk_update_context.assert_called_once_with(updates)
    
    @pytest.mark.asyncio
    async def test_get_context_functions(self, mock_context_manager):
        """Test context getter core functions."""
        # Test get_context for project_brief
        brief = await get_context(mock_context_manager, 'project_brief')
        mock_context_manager.get_context.assert_called_with('project_brief')
        assert brief == "Sample context content"
        
        # Test get_context for active_context
        active = await get_context(mock_context_manager, 'active_context')
        mock_context_manager.get_context.assert_called_with('active_context')
        assert active == "Sample context content"
        
        # Test get_context for progress
        progress = await get_context(mock_context_manager, 'progress')
        mock_context_manager.get_context.assert_called_with('progress')
        assert progress == "Sample context content"
        
        # Test get_all_context
        all_context = await get_all_context(mock_context_manager)
        mock_context_manager.get_all_context.assert_called_once()
        assert 'project_brief' in all_context
        assert 'active_context' in all_context
        assert 'progress' in all_context
        
        # Test get_memory_bank_info
        info = await get_memory_bank_info(mock_context_manager)
        mock_context_manager.get_current_memory_bank.assert_called_once()
        mock_context_manager.get_memory_banks.assert_called_once()
        assert 'current' in info
        assert 'all' in info
