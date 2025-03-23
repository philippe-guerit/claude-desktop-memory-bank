"""
Unit tests for the storage service.
"""

import os
import pytest
import tempfile
import asyncio
from pathlib import Path

from memory_bank_server.services.storage_service import StorageService

class TestStorageService:
    """Test case for the storage service."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def storage_service(self, temp_dir):
        """Create a storage service for testing."""
        return StorageService(temp_dir)
    
    @pytest.mark.asyncio
    async def test_initialize_templates(self, storage_service):
        """Test template initialization."""
        await storage_service.initialize_templates()
        
        # Check that the templates directory exists
        assert os.path.exists(storage_service.templates_path)
        
        # Check that the default templates were created
        template_files = ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                         "techContext.md", "activeContext.md", "progress.md"]
        
        for template_file in template_files:
            assert os.path.exists(os.path.join(storage_service.templates_path, template_file))
    
    @pytest.mark.asyncio
    async def test_initialize_global_memory_bank(self, storage_service):
        """Test global memory bank initialization."""
        await storage_service.initialize_templates()
        global_path = await storage_service.initialize_global_memory_bank()
        
        # Check that the global memory bank exists
        assert os.path.exists(global_path)
        
        # Check that the global memory bank contains the expected files
        files = ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                "techContext.md", "activeContext.md", "progress.md"]
        
        for file_name in files:
            assert os.path.exists(os.path.join(global_path, file_name))
    
    @pytest.mark.asyncio
    async def test_create_project_memory_bank(self, storage_service):
        """Test creating a project memory bank."""
        await storage_service.initialize_templates()
        
        # Create a test project
        project_name = "test-project"
        metadata = {
            "name": project_name,
            "description": "Test project",
            "created": "2023-01-01T00:00:00Z",
            "lastModified": "2023-01-01T00:00:00Z"
        }
        
        project_path = await storage_service.create_project_memory_bank(project_name, metadata)
        
        # Check that the project memory bank exists
        assert os.path.exists(project_path)
        
        # Check that the project metadata file exists
        assert os.path.exists(os.path.join(project_path, "project.json"))
        
        # Check that the project memory bank contains the expected files
        files = ["projectbrief.md", "productContext.md", "systemPatterns.md", 
                "techContext.md", "activeContext.md", "progress.md"]
        
        for file_name in files:
            assert os.path.exists(os.path.join(project_path, file_name))
    
    @pytest.mark.asyncio
    async def test_get_context_file(self, storage_service):
        """Test getting a context file."""
        await storage_service.initialize_templates()
        global_path = await storage_service.initialize_global_memory_bank()
        
        # Get a context file
        content = await storage_service.get_context_file(global_path, "projectbrief.md")
        
        # Check that the content is a string
        assert isinstance(content, str)
        assert "Project Brief" in content
    
    @pytest.mark.asyncio
    async def test_update_context_file(self, storage_service):
        """Test updating a context file."""
        await storage_service.initialize_templates()
        global_path = await storage_service.initialize_global_memory_bank()
        
        # Update a context file
        new_content = "# Updated Project Brief\n\nThis is an updated project brief."
        await storage_service.update_context_file(global_path, "projectbrief.md", new_content)
        
        # Check that the file was updated
        content = await storage_service.get_context_file(global_path, "projectbrief.md")
        assert content == new_content
    
    @pytest.mark.asyncio
    async def test_register_repository(self, storage_service):
        """Test registering a repository."""
        # Create a test repository record
        repo_path = "/path/to/repo"
        repo_name = "test-repo"
        
        await storage_service.register_repository(repo_path, repo_name)
        
        # Check that the repository record file exists
        record_path = storage_service.repositories_path / f"{repo_name}.json"
        assert os.path.exists(record_path)
        
        # Check that the repository record contains the expected data
        repo_record = await storage_service.get_repository_record(repo_name)
        assert repo_record["path"] == repo_path
        assert repo_record["name"] == repo_name
    
    @pytest.mark.asyncio
    async def test_get_repositories(self, storage_service):
        """Test getting all repositories."""
        # Create test repository records
        repos = [
            ("/path/to/repo1", "test-repo1"),
            ("/path/to/repo2", "test-repo2")
        ]
        
        for repo_path, repo_name in repos:
            await storage_service.register_repository(repo_path, repo_name)
        
        # Get all repositories
        repositories = await storage_service.get_repositories()
        
        # Check that the repositories were returned
        assert len(repositories) == len(repos)
        repo_names = [repo["name"] for repo in repositories]
        assert set(repo_names) == set([name for _, name in repos])
