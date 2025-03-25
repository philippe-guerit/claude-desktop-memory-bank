"""
Unit tests for the direct access integration layer.

This module tests the DirectAccess class which provides a direct API
to the Memory Bank functionality without FastMCP dependency.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from memory_bank_server.server.direct_access import DirectAccess
from memory_bank_server.services.context_service import ContextService


class TestDirectAccess:
    """Test case for the DirectAccess integration layer."""
    
    @pytest.fixture
    def mock_context_service(self):
        """Create a mock context service."""
        context_service = MagicMock()
        
        # Set up AsyncMock for async methods
        context_service.set_memory_bank = AsyncMock()
        context_service.set_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        context_service.get_current_memory_bank = AsyncMock()
        context_service.get_current_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        context_service.get_memory_banks = AsyncMock()
        context_service.get_memory_banks.return_value = {
            'global': [{'path': '/path/to/global'}],
            'projects': [
                {'name': 'test-project', 'metadata': {}}
            ],
            'repositories': [
                {'name': 'test-repo', 'repo_path': '/path/to/repo'}
            ]
        }
        
        # Mock repository service
        context_service.repository_service = MagicMock()
        
        context_service.get_context = AsyncMock()
        context_service.get_context.return_value = "Sample context content"
        
        context_service.get_all_context = AsyncMock()
        context_service.get_all_context.return_value = {
            'project_brief': 'Project brief content',
            'active_context': 'Active context content',
            'progress': 'Progress content'
        }
        
        context_service.bulk_update_context = AsyncMock()
        context_service.bulk_update_context.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        
        return context_service
    
    @pytest.fixture
    def direct_access(self, mock_context_service):
        """Create a DirectAccess instance for testing."""
        return DirectAccess(mock_context_service)
    
    @pytest.mark.asyncio
    async def test_start_memory_bank(self, direct_access):
        """Test the start_memory_bank direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.start_memory_bank', new_callable=AsyncMock) as mock_start:
            mock_start.return_value = {
                'selected_memory_bank': {'type': 'repository'},
                'actions_taken': ['detected repository'],
                'prompt_name': None
            }
            
            # Call the method
            result = await direct_access.start_memory_bank(
                prompt_name=None,
                auto_detect=True,
                current_path='/path/to/repo',
                force_type=None
            )
            
            # Verify that the method was called correctly
            mock_start.assert_called_once()
            
            # Verify the response structure
            assert 'selected_memory_bank' in result
            assert 'actions_taken' in result
            assert 'prompt_name' in result
    
    @pytest.mark.asyncio
    async def test_select_memory_bank(self, direct_access):
        """Test the select_memory_bank direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.select_memory_bank', new_callable=AsyncMock) as mock_select:
            mock_select.return_value = {
                'type': 'repository',
                'path': '/path/to/memory-bank'
            }
            
            # Test with global type
            result = await direct_access.select_memory_bank(type='global')
            
            # Verify that the method was called correctly
            mock_select.assert_called_with(
                direct_access.context_service,
                type='global',
                project_name=None,
                repository_path=None
            )
    
    @pytest.mark.asyncio
    async def test_list_memory_banks(self, direct_access):
        """Test the list_memory_banks direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.list_memory_banks', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = {
                'current': {'type': 'global'},
                'available': {
                    'global': [{'path': '/path/to/global'}],
                    'projects': [],
                    'repositories': []
                }
            }
            
            # Call the method
            result = await direct_access.list_memory_banks()
            
            # Verify that the method was called correctly
            mock_list.assert_called_once_with(direct_access.context_service)
            
            # Verify response structure
            assert 'current' in result
            assert 'available' in result
    
    @pytest.mark.asyncio
    async def test_bulk_update_context(self, direct_access):
        """Test the bulk_update_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.bulk_update_context', new_callable=AsyncMock) as mock_bulk:
            mock_bulk.return_value = {
                'type': 'repository',
                'path': '/path/to/memory-bank'
            }
            
            # Prepare updates
            updates = {
                'project_brief': 'New project brief',
                'active_context': 'New active context'
            }
            
            # Call the method
            result = await direct_access.bulk_update_context(updates=updates)
            
            # Verify that the method was called correctly
            mock_bulk.assert_called_once_with(direct_access.context_service, updates)
            
            # Verify the result
            assert result['type'] == 'repository'
            assert result['path'] == '/path/to/memory-bank'
    
    @pytest.mark.asyncio
    async def test_get_all_context(self, direct_access):
        """Test the get_all_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.get_all_context', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = {
                'project_brief': 'Project brief content',
                'active_context': 'Active context content',
                'progress': 'Progress content'
            }
            
            # Call the method
            result = await direct_access.get_all_context()
            
            # Verify that the method was called correctly
            mock_get_all.assert_called_once_with(direct_access.context_service)
            
            # Verify response structure
            assert 'project_brief' in result
            assert 'active_context' in result
            assert 'progress' in result
    
    @pytest.mark.asyncio
    async def test_get_memory_bank_info(self, direct_access):
        """Test the get_memory_bank_info direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.get_memory_bank_info', new_callable=AsyncMock) as mock_get_info:
            mock_get_info.return_value = {
                'current': {
                    'type': 'repository',
                    'path': '/path/to/memory-bank'
                },
                'all': {
                    'global': [{'path': '/path/to/global'}],
                    'projects': [],
                    'repositories': []
                }
            }
            
            # Call the method
            result = await direct_access.get_memory_bank_info()
            
            # Verify that the method was called correctly
            mock_get_info.assert_called_once_with(direct_access.context_service)
            
            # Verify response structure
            assert 'current' in result
            assert 'all' in result
