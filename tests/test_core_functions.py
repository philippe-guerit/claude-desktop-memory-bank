"""
Unit tests for core business logic functions.

These tests verify that the core functions work correctly
independent of the FastMCP integration.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from memory_bank_server.core.memory_bank import (
    start_memory_bank,
    select_memory_bank,
    list_memory_banks,
    detect_repository,
    initialize_repository_memory_bank,
    create_project
)

from memory_bank_server.core.context import (
    update_context,
    search_context,
    bulk_update_context,
    auto_summarize_context,
    prune_context,
    get_project_brief,
    get_active_context,
    get_progress,
    get_all_context,
    get_memory_bank_info
)

class TestMemoryBankCoreFunctions:
    """Test case for Memory Bank core functions."""
    
    @pytest.fixture
    async def mock_context_manager(self):
        """Create a mock context manager for testing."""
        context_manager = MagicMock()
        
        # Mock repository detection
        context_manager.detect_repository.return_value = {
            'name': 'test-repo',
            'path': '/path/to/repo',
            'branch': 'main',
            'memory_bank_path': None
        }
        
        # Mock memory bank initialization
        context_manager.initialize_repository_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock memory bank selection
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
        context_manager.get_current_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock project creation
        context_manager.create_project.return_value = {
            'name': 'test-project',
            'description': 'A test project',
            'created': '2023-01-01T00:00:00Z',
            'lastModified': '2023-01-01T00:00:00Z'
        }
        
        # Mock context operations
        context_manager.update_context.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        
        context_manager.search_context.return_value = {
            'project_brief': ['Line with search term'],
            'active_context': ['Another line with search term']
        }
        
        context_manager.bulk_update_context.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        
        context_manager.auto_summarize_context.return_value = {
            'project_brief': 'Updated project brief',
            'active_context': 'Updated active context'
        }
        
        context_manager.prune_context.return_value = {
            'project_brief': {
                'pruned_sections': 2,
                'kept_sections': 3
            },
            'active_context': {
                'pruned_sections': 1,
                'kept_sections': 4
            }
        }
        
        # Mock context getters
        context_manager.get_context.return_value = "Sample context content"
        
        context_manager.get_all_context.return_value = {
            'project_brief': 'Project brief content',
            'active_context': 'Active context content',
            'progress': 'Progress content'
        }
        
        context_manager.get_memory_banks.return_value = {
            'global': [{'path': '/path/to/global'}],
            'projects': [
                {'name': 'test-project', 'metadata': {}}
            ],
            'repositories': [
                {'name': 'test-repo', 'repo_path': '/path/to/repo'}
            ]
        }
        
        yield context_manager
    
    @pytest.mark.asyncio
    async def test_start_memory_bank(self, mock_context_manager):
        """Test start_memory_bank core function."""
        result = await start_memory_bank(
            mock_context_manager,
            prompt_name=None,
            auto_detect=True,
            current_path='/path/to/repo',
            force_type=None
        )
        
        # Verify the function called the expected methods
        mock_context_manager.detect_repository.assert_called_once_with('/path/to/repo')
        
        # Verify we get the expected result structure
        assert 'selected_memory_bank' in result
        assert 'actions_taken' in result
        assert 'prompt_name' in result
        
        # Verify actions taken is a list
        assert isinstance(result['actions_taken'], list)
    
    @pytest.mark.asyncio
    async def test_select_memory_bank(self, mock_context_manager):
        """Test select_memory_bank core function."""
        # Test with global type
        result = await select_memory_bank(
            mock_context_manager,
            type='global'
        )
        
        mock_context_manager.set_memory_bank.assert_called_with()
        
        # Test with project type
        result = await select_memory_bank(
            mock_context_manager,
            type='project',
            project='test-project'
        )
        
        mock_context_manager.set_memory_bank.assert_called_with(claude_project='test-project')
        
        # Test with repository type
        result = await select_memory_bank(
            mock_context_manager,
            type='repository',
            repository_path='/path/to/repo'
        )
        
        mock_context_manager.set_memory_bank.assert_called_with(repository_path='/path/to/repo')
        
        # Test with invalid type
        with pytest.raises(ValueError):
            await select_memory_bank(
                mock_context_manager,
                type='invalid'
            )
    
    @pytest.mark.asyncio
    async def test_update_context(self, mock_context_manager):
        """Test update_context core function."""
        result = await update_context(
            mock_context_manager,
            context_type='project_brief',
            content='New project brief content'
        )
        
        mock_context_manager.update_context.assert_called_once_with('project_brief', 'New project brief content')
        
        # Test with invalid context type
        with pytest.raises(ValueError):
            await update_context(
                mock_context_manager,
                context_type='invalid',
                content='Content'
            )
    
    @pytest.mark.asyncio
    async def test_search_context(self, mock_context_manager):
        """Test search_context core function."""
        result = await search_context(
            mock_context_manager,
            query='search term'
        )
        
        mock_context_manager.search_context.assert_called_once_with('search term')
        
        # Verify result structure
        assert 'project_brief' in result
        assert 'active_context' in result
        assert isinstance(result['project_brief'], list)
        assert 'Line with search term' in result['project_brief']
    
    @pytest.mark.asyncio
    async def test_get_context_functions(self, mock_context_manager):
        """Test context getter core functions."""
        # Test get_project_brief
        brief = await get_project_brief(mock_context_manager)
        mock_context_manager.get_context.assert_called_with('project_brief')
        assert brief == "Sample context content"
        
        # Test get_active_context
        active = await get_active_context(mock_context_manager)
        mock_context_manager.get_context.assert_called_with('active_context')
        assert active == "Sample context content"
        
        # Test get_progress
        progress = await get_progress(mock_context_manager)
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
