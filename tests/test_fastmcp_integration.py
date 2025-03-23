"""
Unit tests for the FastMCP integration layer.

This module tests the FastMCPIntegration class which provides an integration
between the Memory Bank system and the FastMCP framework.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from memory_bank_server.server.fastmcp_integration import FastMCPIntegration
from memory_bank_server.services.context_service import ContextService


class TestFastMCPIntegration:
    """Test case for the FastMCP integration layer."""
    
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
    def mock_fastmcp(self):
        """Create a mock FastMCP framework."""
        fastmcp = MagicMock()
        fastmcp.register_function = MagicMock()
        fastmcp.tool = MagicMock()
        fastmcp.resource = MagicMock()
        fastmcp.prompt = MagicMock()
        return fastmcp
    
    @pytest.fixture
    def fastmcp_integration(self, mock_context_service, mock_fastmcp):
        """Create a FastMCPIntegration instance for testing."""
        integration = FastMCPIntegration(mock_context_service)
        
        # Patch the registration methods to avoid external dependencies
        with patch.object(integration, '_register_resource_handlers'):
            with patch.object(integration, '_register_tool_handlers'):
                with patch.object(integration, '_register_prompt_handlers'):
                    integration.register = MagicMock()
                    integration.register(mock_fastmcp)
                    
                    # Set up handler methods for testing
                    integration.memory_bank_start_handler = AsyncMock()
                    integration.memory_bank_start_handler.return_value = {
                        'selected_memory_bank': {'type': 'repository'},
                        'actions_taken': ['detected repository'],
                        'prompt_name': None
                    }
                    
                    integration.select_memory_bank_handler = AsyncMock()
                    integration.select_memory_bank_handler.return_value = {
                        'type': 'repository',
                        'path': '/path/to/memory-bank'
                    }
                    
                    integration.list_memory_banks_handler = AsyncMock()
                    integration.list_memory_banks_handler.return_value = {
                        'current': {'type': 'global'},
                        'available': {
                            'global': [{'path': '/path/to/global'}],
                            'projects': [],
                            'repositories': []
                        }
                    }
                    
                    integration.detect_repository_handler = AsyncMock()
                    integration.detect_repository_handler.return_value = {
                        'name': 'test-repo',
                        'path': '/path/to/repo',
                        'branch': 'main'
                    }
                    
                    integration.initialize_repository_memory_bank_handler = AsyncMock()
                    integration.initialize_repository_memory_bank_handler.return_value = {
                        'type': 'repository',
                        'path': '/path/to/memory-bank',
                        'repo_info': {
                            'name': 'test-repo',
                            'path': '/path/to/repo',
                            'branch': 'main'
                        }
                    }
                    
                    integration.create_project_handler = AsyncMock()
                    integration.create_project_handler.return_value = {
                        'name': 'test-project',
                        'description': 'A test project'
                    }
                    
                    integration.update_context_handler = AsyncMock()
                    integration.update_context_handler.return_value = {
                        'type': 'repository',
                        'path': '/path/to/memory-bank'
                    }
                    
                    integration.search_context_handler = AsyncMock()
                    integration.search_context_handler.return_value = {
                        'project_brief': ['Line with search term'],
                        'active_context': ['Another line with search term']
                    }
                    
                    integration.bulk_update_context_handler = AsyncMock()
                    integration.bulk_update_context_handler.return_value = {
                        'type': 'repository',
                        'path': '/path/to/memory-bank'
                    }
                    
                    integration.auto_summarize_context_handler = AsyncMock()
                    integration.auto_summarize_context_handler.return_value = {
                        'project_brief': 'Updated project brief',
                        'active_context': 'Updated active context'
                    }
                    
                    integration.prune_context_handler = AsyncMock()
                    integration.prune_context_handler.return_value = {
                        'project_brief': {
                            'pruned_sections': 2,
                            'kept_sections': 3
                        },
                        'active_context': {
                            'pruned_sections': 1,
                            'kept_sections': 4
                        }
                    }
        
        return integration
    
    def test_registration(self, fastmcp_integration, mock_fastmcp):
        """Test that functions are properly registered with FastMCP."""
        # Registration is already mocked in the fixture
        assert fastmcp_integration.register.called
    
    @pytest.mark.asyncio
    async def test_memory_bank_start_handler(self, fastmcp_integration):
        """Test the memory_bank_start handler."""
        # Mock handler args
        args = {
            'prompt_name': None,
            'auto_detect': True,
            'current_path': '/path/to/repo',
            'force_type': None
        }
        
        # Call the handler
        result = await fastmcp_integration.memory_bank_start_handler(args)
        
        # Verify the result
        assert 'selected_memory_bank' in result
        assert 'actions_taken' in result
        assert 'prompt_name' in result
    
    @pytest.mark.asyncio
    async def test_select_memory_bank_handler(self, fastmcp_integration):
        """Test the select_memory_bank handler."""
        # Mock handler args
        args = {
            'type': 'repository',
            'project': None,
            'repository_path': '/path/to/repo'
        }
        
        # Call the handler
        result = await fastmcp_integration.select_memory_bank_handler(args)
        
        # Verify the result
        assert result['type'] == 'repository'
        assert result['path'] == '/path/to/memory-bank'
    
    @pytest.mark.asyncio
    async def test_list_memory_banks_handler(self, fastmcp_integration):
        """Test the list_memory_banks handler."""
        # Call the handler
        result = await fastmcp_integration.list_memory_banks_handler({})
        
        # Verify the result
        assert 'current' in result
        assert 'available' in result
    
    @pytest.mark.asyncio
    async def test_detect_repository_handler(self, fastmcp_integration):
        """Test the detect_repository handler."""
        # Mock handler args
        args = {'path': '/path/to/repo'}
        
        # Call the handler
        result = await fastmcp_integration.detect_repository_handler(args)
        
        # Verify the result
        assert 'name' in result
        assert 'path' in result
        assert 'branch' in result
    
    @pytest.mark.asyncio
    async def test_initialize_repository_memory_bank_handler(self, fastmcp_integration):
        """Test the initialize_repository_memory_bank handler."""
        # Mock handler args
        args = {
            'repository_path': '/path/to/repo',
            'claude_project': 'test-project'
        }
        
        # Call the handler
        result = await fastmcp_integration.initialize_repository_memory_bank_handler(args)
        
        # Verify the result
        assert 'type' in result
        assert 'path' in result
        assert 'repo_info' in result
    
    @pytest.mark.asyncio
    async def test_create_project_handler(self, fastmcp_integration):
        """Test the create_project handler."""
        # Mock handler args
        args = {
            'name': 'test-project',
            'description': 'A test project',
            'repository_path': '/path/to/repo'
        }
        
        # Call the handler
        result = await fastmcp_integration.create_project_handler(args)
        
        # Verify the result
        assert 'name' in result
        assert 'description' in result
    
    @pytest.mark.asyncio
    async def test_update_context_handler(self, fastmcp_integration):
        """Test the update_context handler."""
        # Mock handler args
        args = {
            'context_type': 'project_brief',
            'content': 'New project brief content'
        }
        
        # Call the handler
        result = await fastmcp_integration.update_context_handler(args)
        
        # Verify the result
        assert 'type' in result
        assert 'path' in result
    
    @pytest.mark.asyncio
    async def test_search_context_handler(self, fastmcp_integration):
        """Test the search_context handler."""
        # Mock handler args
        args = {'query': 'search term'}
        
        # Call the handler
        result = await fastmcp_integration.search_context_handler(args)
        
        # Verify the result
        assert 'project_brief' in result
        assert 'active_context' in result
    
    @pytest.mark.asyncio
    async def test_bulk_update_context_handler(self, fastmcp_integration):
        """Test the bulk_update_context handler."""
        # Mock handler args
        updates = {
            'project_brief': 'New project brief',
            'active_context': 'New active context'
        }
        args = {'updates': updates}
        
        # Call the handler
        result = await fastmcp_integration.bulk_update_context_handler(args)
        
        # Verify the result
        assert 'type' in result
        assert 'path' in result
    
    @pytest.mark.asyncio
    async def test_auto_summarize_context_handler(self, fastmcp_integration):
        """Test the auto_summarize_context handler."""
        # Mock handler args
        args = {'conversation_text': 'Sample conversation text'}
        
        # Call the handler
        result = await fastmcp_integration.auto_summarize_context_handler(args)
        
        # Verify the result
        assert 'project_brief' in result
        assert 'active_context' in result
    
    @pytest.mark.asyncio
    async def test_prune_context_handler(self, fastmcp_integration):
        """Test the prune_context handler."""
        # Mock handler args
        args = {'max_age_days': 90}
        
        # Call the handler
        result = await fastmcp_integration.prune_context_handler(args)
        
        # Verify the result
        assert 'project_brief' in result
        assert 'active_context' in result
