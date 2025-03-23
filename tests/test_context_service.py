"""
Unit tests for the context service.
"""

import os
import pytest
from unittest.mock import MagicMock, patch
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
        storage.initialize_global_memory_bank.return_value = "/path/to/global"
        storage.get_context_file.return_value = "# Test Context\n\nThis is test context content."
        storage.update_context_file.return_value = None
        storage.get_project_memory_banks.return_value = ["project1", "project2"]
        storage.get_project_metadata.return_value = {
            "name": "project1",
            "description": "Test project",
            "created": "2023-01-01T00:00:00Z",
            "lastModified": "2023-01-01T00:00:00Z"
        }
        storage.get_project_path.return_value = "/path/to/project"
        storage.create_project_memory_bank.return_value = "/path/to/project"
        storage.get_repositories.return_value = [
            {"name": "repo1", "path": "/path/to/repo1"},
            {"name": "repo2", "path": "/path/to/repo2"}
        ]
        storage.get_repository_memory_bank_path.return_value = "/path/to/repo-mb"
        
        return storage
    
    @pytest.fixture
    def mock_repository_service(self):
        """Create a mock repository service."""
        repo_service = MagicMock(spec=RepositoryService)
        
        # Mock methods that will be called
        repo_service.detect_repository.return_value = {
            "name": "test-repo",
            "path": "/path/to/repo",
            "branch": "main"
        }
        repo_service.initialize_repository_memory_bank.return_value = {
            "type": "repository",
            "path": "/path/to/repo-mb",
            "repo_info": {
                "name": "test-repo",
                "path": "/path/to/repo",
                "branch": "main"
            }
        }
        repo_service.is_git_repository.return_value = True
        
        return repo_service
    
    @pytest.fixture
    def context_service(self, mock_storage_service, mock_repository_service):
        """Create a context service with mock dependencies."""
        return ContextService(mock_storage_service, mock_repository_service)
    
    @pytest.mark.asyncio
    async def test_initialize(self, context_service):
        """Test initializing the context service."""
        await context_service.initialize()
        
        # Verify that the global memory bank was initialized
        context_service.storage_service.initialize_global_memory_bank.assert_called_once()
        
        # Verify that the current memory bank is set to global
        current_mb = await context_service.get_current_memory_bank()
        assert current_mb["type"] == "global"
    
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
        context_service.storage_service.get_project_memory_banks.assert_called_once()
        context_service.storage_service.get_project_metadata.assert_called()
        context_service.storage_service.get_repositories.assert_called_once()
    
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
        context_service.storage_service.get_project_path.assert_called_with("project1")
        context_service.storage_service.get_project_metadata.assert_called_with("project1")
    
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
            mock_detect.assert_called_with("/path/to/repo")
    
    @pytest.mark.asyncio
    async def test_create_project(self, context_service):
        """Test creating a new project."""
        # Call the method
        result = await context_service.create_project(
            "new-project",
            "A new test project"
        )
        
        # Verify that the storage service methods were called
        context_service.storage_service.create_project_memory_bank.assert_called_once()
        
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
        context_service.storage_service.get_context_file.assert_called_once()
        
        # Verify the content
        assert "Test Context" in content
    
    @pytest.mark.asyncio
    async def test_update_context(self, context_service):
        """Test updating a specific context file."""
        # Call the method
        await context_service.update_context("project_brief", "# New Content")
        
        # Verify that the storage service method was called
        context_service.storage_service.update_context_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_context(self, context_service):
        """Test searching context files."""
        # Mock the get_context_file method to return different content for different files
        context_service.storage_service.get_context_file.side_effect = lambda path, file: (
            "This is a test with search term" if file == "projectbrief.md" else
            "This doesn't match" if file == "activeContext.md" else
            "Another file with search term" if file == "progress.md" else
            "No match here"
        )
        
        # Call the method
        results = await context_service.search_context("search term")
        
        # Verify the results
        assert "project_brief" in results
        assert "progress" in results
        assert "active_context" not in results
    
    @pytest.mark.asyncio
    async def test_bulk_update_context(self, context_service):
        """Test updating multiple context files at once."""
        # Call the method
        updates = {
            "project_brief": "# New Project Brief",
            "progress": "# New Progress"
        }
        await context_service.bulk_update_context(updates)
        
        # Verify that the storage service method was called for each update
        assert context_service.storage_service.update_context_file.call_count == len(updates)
    
    @pytest.mark.asyncio
    async def test_auto_summarize_context(self, context_service):
        """Test automatically extracting context from conversation."""
        # Prepare test data
        conversation = """
        The project purpose is to create a memory bank system.
        
        The goals include maintaining context across conversations.
        
        We need to implement the architecture with clean separation.
        
        Current progress: refactoring is complete.
        """
        
        # Mock get_all_context to return empty contexts
        context_service.get_all_context = MagicMock(return_value={
            "project_brief": "# Project Brief\n\n",
            "active_context": "# Active Context\n\n",
            "progress": "# Progress\n\n"
        })
        
        # Call the method
        results = await context_service.auto_summarize_context(conversation)
        
        # Verify that context extraction happened
        assert "project_brief" in results
        assert "progress" in results
        
        # Verify that the extracted content contains the expected data
        assert "purpose" in results["project_brief"].lower()
        assert "goals" in results["project_brief"].lower()
        assert "progress" in results["progress"].lower()
