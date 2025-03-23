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
        context_service.repository_service.detect_repository = AsyncMock()
        context_service.repository_service.detect_repository.return_value = {
            'name': 'test-repo',
            'path': '/path/to/repo',
            'branch': 'main',
            'memory_bank_path': None
        }
        
        context_service.repository_service.initialize_repository_memory_bank = AsyncMock()
        context_service.repository_service.initialize_repository_memory_bank.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank',
            'repo_info': {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
        }
        
        # Mock other async methods
        context_service.create_project = AsyncMock()
        context_service.create_project.return_value = {
            'name': 'test-project',
            'description': 'A test project',
            'created': '2023-01-01T00:00:00Z',
            'lastModified': '2023-01-01T00:00:00Z'
        }
        
        context_service.get_context = AsyncMock()
        context_service.get_context.return_value = "Sample context content"
        
        context_service.get_all_context = AsyncMock()
        context_service.get_all_context.return_value = {
            'project_brief': 'Project brief content',
            'active_context': 'Active context content',
            'progress': 'Progress content'
        }
        
        context_service.update_context = AsyncMock()
        context_service.update_context.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        
        context_service.search_context = AsyncMock()
        context_service.search_context.return_value = {
            'project_brief': ['Line with search term'],
            'active_context': ['Another line with search term']
        }
        
        context_service.bulk_update_context = AsyncMock()
        context_service.bulk_update_context.return_value = {
            'type': 'repository',
            'path': '/path/to/memory-bank'
        }
        
        context_service.auto_summarize_context = AsyncMock()
        context_service.auto_summarize_context.return_value = {
            'project_brief': 'Updated project brief',
            'active_context': 'Updated active context'
        }
        
        context_service.prune_context = AsyncMock()
        context_service.prune_context.return_value = {
            'project_brief': {
                'pruned_sections': 2,
                'kept_sections': 3
            },
            'active_context': {
                'pruned_sections': 1,
                'kept_sections': 4
            }
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
    async def test_detect_repository(self, direct_access):
        """Test the detect_repository direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.detect_repository', new_callable=AsyncMock) as mock_detect:
            mock_detect.return_value = {
                'name': 'test-repo',
                'path': '/path/to/repo',
                'branch': 'main'
            }
            
            # Call the method
            result = await direct_access.detect_repository(path='/path/to/repo')
            
            # Verify that the method was called correctly
            mock_detect.assert_called_once_with(direct_access.context_service, '/path/to/repo')
            
            # Verify response structure
            assert 'name' in result
            assert 'path' in result
            assert 'branch' in result
    
    @pytest.mark.asyncio
    async def test_initialize_repository_memory_bank(self, direct_access):
        """Test the initialize_repository_memory_bank direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.initialize_repository_memory_bank', new_callable=AsyncMock) as mock_init:
            mock_init.return_value = {
                'type': 'repository',
                'path': '/path/to/memory-bank',
                'repo_info': {
                    'name': 'test-repo',
                    'path': '/path/to/repo',
                    'branch': 'main'
                }
            }
            
            # Call the method
            result = await direct_access.initialize_repository_memory_bank(
                repository_path='/path/to/repo',
                project_name='test-project'
            )
            
            # Verify that the method was called correctly
            mock_init.assert_called_once_with(
                direct_access.context_service,
                '/path/to/repo',
                'test-project'
            )
            
            # Verify response structure
            assert 'type' in result
            assert 'path' in result
            assert 'repo_info' in result
    
    @pytest.mark.asyncio
    async def test_create_project(self, direct_access):
        """Test the create_project direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.create_project', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = {
                'name': 'test-project',
                'description': 'A test project'
            }
            
            # Call the method
            result = await direct_access.create_project(
                name='test-project',
                description='A test project',
                repository_path='/path/to/repo'
            )
            
            # Verify that the method was called correctly
            mock_create.assert_called_once_with(
                direct_access.context_service,
                'test-project',
                'A test project',
                '/path/to/repo'
            )
            
            # Verify response structure
            assert 'name' in result
            assert 'description' in result
    
    @pytest.mark.asyncio
    async def test_get_context(self, direct_access):
        """Test the get_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.get_context', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = "Test context content"
            
            # Call the method
            result = await direct_access.get_context(context_type='project_brief')
            
            # Verify that the method was called correctly
            mock_get.assert_called_once_with(direct_access.context_service, 'project_brief')
            
            # Verify the result
            assert result == "Test context content"
    
    @pytest.mark.asyncio
    async def test_update_context(self, direct_access):
        """Test the update_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.update_context', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = {
                'type': 'repository',
                'path': '/path/to/memory-bank'
            }
            
            # Call the method
            result = await direct_access.update_context(
                context_type='project_brief',
                content='New project brief content'
            )
            
            # Verify that the method was called correctly
            mock_update.assert_called_once_with(
                direct_access.context_service,
                'project_brief',
                'New project brief content'
            )
            
            # Verify the result
            assert result['type'] == 'repository'
            assert result['path'] == '/path/to/memory-bank'
    
    @pytest.mark.asyncio
    async def test_search_context(self, direct_access):
        """Test the search_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.search_context', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = {
                'project_brief': ['Line with search term'],
                'active_context': ['Another line with search term']
            }
            
            # Call the method
            result = await direct_access.search_context(query='search term')
            
            # Verify that the method was called correctly
            mock_search.assert_called_once_with(direct_access.context_service, 'search term')
            
            # Verify response structure
            assert 'project_brief' in result
            assert 'active_context' in result
    
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
    async def test_auto_summarize_context(self, direct_access):
        """Test the auto_summarize_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.auto_summarize_context', new_callable=AsyncMock) as mock_auto:
            mock_auto.return_value = {
                'project_brief': 'Updated project brief',
                'active_context': 'Updated active context'
            }
            
            # Call the method
            result = await direct_access.auto_summarize_context(
                conversation_text="Sample conversation text"
            )
            
            # Verify that the method was called correctly
            mock_auto.assert_called_once_with(
                direct_access.context_service,
                "Sample conversation text"
            )
            
            # Verify response structure
            assert 'project_brief' in result
            assert 'active_context' in result
    
    @pytest.mark.asyncio
    async def test_prune_context(self, direct_access):
        """Test the prune_context direct access method."""
        # Create patch for core function
        with patch('memory_bank_server.server.direct_access.prune_context', new_callable=AsyncMock) as mock_prune:
            mock_prune.return_value = {
                'project_brief': {
                    'pruned_sections': 2,
                    'kept_sections': 3
                },
                'active_context': {
                    'pruned_sections': 1,
                    'kept_sections': 4
                }
            }
            
            # Call the method
            result = await direct_access.prune_context(max_age_days=90)
            
            # Verify that the method was called correctly
            mock_prune.assert_called_once_with(direct_access.context_service, 90)
            
            # Verify response structure
            assert 'project_brief' in result
            assert 'active_context' in result
    
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
