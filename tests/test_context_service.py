"""
Unit tests for the context service.
"""

import os
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from memory_bank_server.services.storage_service import StorageService
from memory_bank_server.services.repository_service import RepositoryService
from memory_bank_server.services.context_service import ContextService

class TestContextService:
    """Test case for the context service."""
    
    @pytest.fixture
    def mock_storage_service(self):
        """Create a mock storage service."""
        storage = MagicMock(spec=StorageService)
        
        # Mock methods that will be called
        storage.initialize_global_memory_bank = AsyncMock(return_value="/path/to/global")
        storage.get_context_file = AsyncMock(return_value="# Test Context\n\nThis is test context content.")
        storage.update_context_file = AsyncMock(return_value=None)
        storage.get_project_memory_banks = AsyncMock(return_value=["project1", "project2"])
        storage.get_project_metadata = AsyncMock(return_value={
            "name": "project1",
            "description": "Test project",
            "created": "2023-01-01T00:00:00Z",
            "lastModified": "2023-01-01T00:00:00Z"
        })
        storage.get_project_path = AsyncMock(return_value="/path/to/project")
        storage.create_project_memory_bank = AsyncMock(return_value="/path/to/project")
        storage.get_repositories = AsyncMock(return_value=[
            {"name": "repo1", "path": "/path/to/repo1"},
            {"name": "repo2", "path": "/path/to/repo2"}
        ])
        storage.get_repository_memory_bank_path = AsyncMock(return_value="/path/to/repo-mb")
        
        # Add global_path property for the get_memory_banks test
        storage.global_path = "/path/to/global"
        
        return storage
    
    @pytest.fixture
    def mock_repository_service(self):
        """Create a mock repository service."""
        repo_service = MagicMock(spec=RepositoryService)
        
        # Mock methods that will be called
        repo_service.detect_repository = AsyncMock(return_value={
            "name": "test-repo",
            "path": "/path/to/repo",
            "branch": "main"
        })
        repo_service.initialize_repository_memory_bank = AsyncMock(return_value={
            "type": "repository",
            "path": "/path/to/repo-mb",
            "repo_info": {
                "name": "test-repo",
                "path": "/path/to/repo",
                "branch": "main"
            }
        })
        repo_service.is_git_repository = AsyncMock(return_value=True)
        
        return repo_service
    
    @pytest.fixture
    def context_service(self, mock_storage_service, mock_repository_service):
        """Create a context service with mock dependencies."""
        # Create a real context service but patch the initialize method
        service = ContextService(mock_storage_service, mock_repository_service)
        
        # We need to create an already-initialized service to prevent double-init issues
        service._initialized = True
        service._current_memory_bank = {"type": "global", "path": "/path/to/global"}
        
        return service
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_storage_service, mock_repository_service):
        """Test initializing the context service."""
        # Create a fresh service that hasn't been initialized yet
        context_service = ContextService(mock_storage_service, mock_repository_service)
        context_service._initialized = False
        
        # Set global memory bank path
        mock_storage_service.initialize_global_memory_bank.return_value = "/path/to/global"
        
        # Reset the mock to clear any previous calls
        mock_storage_service.initialize_global_memory_bank.reset_mock()
        
        # Call initialize
        await context_service.initialize()
        
        # Verify that the global memory bank was initialized - allow for multiple calls
        # The implementation calls initialize_global_memory_bank twice
        assert mock_storage_service.initialize_global_memory_bank.await_count == 2
        
        # Verify that the current memory bank is set to global
        assert context_service.current_memory_bank["type"] == "global"
        assert context_service.current_memory_bank["path"] == "/path/to/global"
    
    @pytest.mark.asyncio
    async def test_get_memory_banks(self, context_service):
        """Test getting all available memory banks."""
        # Call the method
        memory_banks = await context_service.get_memory_banks()
        
        # Verify that the method returns the expected structure
        assert "global" in memory_banks
        assert "projects" in memory_banks
        assert "repositories" in memory_banks
        
        # Verify that the storage service methods were called
        context_service.storage_service.get_project_memory_banks.assert_awaited_once()
        context_service.storage_service.get_project_metadata.assert_awaited()
        context_service.storage_service.get_repositories.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_set_memory_bank_global(self, context_service):
        """Test setting the global memory bank."""
        # Call the method
        result = await context_service.set_memory_bank()
        
        # Verify the result
        assert result["type"] == "global"
        
        # Verify that the current memory bank was updated
        current_mb = await context_service.get_current_memory_bank()
        assert current_mb["type"] == "global"
    
    @pytest.mark.asyncio
    async def test_set_memory_bank_project(self, context_service):
        """Test setting a project memory bank."""
        # Call the method
        result = await context_service.set_memory_bank(type="project", project_name="project1")
        
        # Verify the result
        assert result["type"] == "project"
        assert result["project"] == "project1"
        
        # Verify that the current memory bank was updated
        current_mb = await context_service.get_current_memory_bank()
        assert current_mb["type"] == "project"
        assert current_mb["project"] == "project1"
        
        # Verify that the storage service methods were called
        context_service.storage_service.get_project_path.assert_awaited_with("project1")
        context_service.storage_service.get_project_metadata.assert_awaited_with("project1")
    
    @pytest.mark.asyncio
    async def test_set_memory_bank_repository(self, context_service):
        """Test setting a repository memory bank."""
        # Call the method
        with patch.object(context_service.repository_service, 'detect_repository') as mock_detect:
            mock_detect.return_value = {
                "name": "test-repo",
                "path": "/path/to/repo",
                "branch": "main"
            }
            
            result = await context_service.set_memory_bank(
                type="repository", 
                repository_path="/path/to/repo"
            )
            
            # Verify the result
            assert result["type"] == "repository"
            assert result["repo_info"]["name"] == "test-repo"
            
            # Verify that the current memory bank was updated
            current_mb = await context_service.get_current_memory_bank()
            assert current_mb["type"] == "repository"
            assert current_mb["repo_info"]["name"] == "test-repo"
            
            # Verify that the repository service methods were called
            mock_detect.assert_awaited_with("/path/to/repo")
    
    @pytest.mark.asyncio
    async def test_create_project(self, context_service):
        """Test creating a new project."""
        # Call the method
        result = await context_service.create_project(
            "new-project",
            "A new test project"
        )
        
        # Verify that the storage service methods were called
        context_service.storage_service.create_project_memory_bank.assert_awaited_once()
        
        # Verify that the current memory bank was updated
        current_mb = await context_service.get_current_memory_bank()
        assert current_mb["type"] == "project"
        assert current_mb["project"] == "new-project"
    
    @pytest.mark.asyncio
    async def test_get_context(self, context_service):
        """Test getting a specific context file."""
        # Call the method
        content = await context_service.get_context("project_brief")
        
        # Verify that the storage service method was called
        context_service.storage_service.get_context_file.assert_awaited_once()
        
        # Verify the content
        assert "Test Context" in content
    
    @pytest.mark.asyncio
    async def test_bulk_update_context(self, context_service):
        """Test updating multiple context files at once."""
        # Set up the mock to match the expected verification process
        updates = {
            "project_brief": "# New Project Brief",
            "progress": "# New Progress"
        }
        
        # Make get_context_file return the expected updated content to pass verification
        def mock_get_context_file(path, file):
            if file == "projectbrief.md":
                return updates["project_brief"]
            elif file == "progress.md":
                return updates["progress"]
            else:
                return "Default content"
                
        context_service.storage_service.get_context_file = AsyncMock(side_effect=mock_get_context_file)
        
        # Call the method
        await context_service.bulk_update_context(updates)
        
        # Verify that the storage service method was called for each update
        assert context_service.storage_service.update_context_file.await_count == len(updates)
    
    # Deprecated method tests removed:
    # - test_update_context (replaced by bulk_update_context)
    # - test_search_context (removed functionality)
    # - test_auto_summarize_context (removed functionality)
