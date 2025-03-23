"""
Unit tests for the repository service.
"""

import os
import pytest
import tempfile
import shutil
import subprocess
from unittest.mock import MagicMock, patch

from memory_bank_server.services.storage_service import StorageService
from memory_bank_server.services.repository_service import RepositoryService

class TestRepositoryService:
    """Test case for the repository service."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def mock_storage_service(self):
        """Create a mock storage service."""
        storage = MagicMock(spec=StorageService)
        
        # Mock methods that will be called
        storage.get_repository_record.return_value = {"name": "test-repo", "path": "/path/to/repo"}
        storage.get_repository_memory_bank_path.return_value = "/path/to/memory-bank"
        storage.create_repository_memory_bank.return_value = "/path/to/memory-bank"
        storage.register_repository.return_value = None
        
        return storage
    
    @pytest.fixture
    def repository_service(self, mock_storage_service):
        """Create a repository service with mock storage."""
        return RepositoryService(mock_storage_service)
    
    @pytest.fixture
    def git_repo(self, temp_dir):
        """Create a temporary Git repository for testing."""
        repo_path = os.path.join(temp_dir, "test-repo")
        os.makedirs(repo_path)
        
        # Initialize Git repository
        try:
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            # Create a test file and commit it
            with open(os.path.join(repo_path, "test.txt"), "w") as f:
                f.write("Test content")
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)
            return repo_path
        except (subprocess.SubprocessError, OSError):
            # Skip Git tests if Git is not available
            pytest.skip("Git not available")
    
    def test_is_git_repository(self, repository_service, git_repo):
        """Test detecting if a path is a Git repository."""
        # Test with a valid Git repository
        assert repository_service.is_git_repository(git_repo) is True
        
        # Test with a non-Git directory
        non_git_dir = os.path.dirname(git_repo)
        assert repository_service.is_git_repository(non_git_dir) is False
    
    def test_find_repository_root(self, repository_service, git_repo):
        """Test finding the root of a Git repository."""
        # Test with a Git repository root
        assert repository_service.find_repository_root(git_repo) == git_repo
        
        # Test with a subdirectory
        subdir = os.path.join(git_repo, "subdir")
        os.makedirs(subdir)
        assert repository_service.find_repository_root(subdir) == git_repo
        
        # Test with a non-Git directory
        non_git_dir = os.path.dirname(git_repo)
        assert repository_service.find_repository_root(non_git_dir) is None
    
    def test_get_repository_info(self, repository_service, git_repo):
        """Test getting repository information."""
        # Test with a valid Git repository
        repo_info = repository_service.get_repository_info(git_repo)
        
        assert repo_info["name"] == os.path.basename(git_repo)
        assert repo_info["path"] == git_repo
        assert "branch" in repo_info
    
    @pytest.mark.asyncio
    async def test_detect_repository(self, repository_service, git_repo):
        """Test detecting a repository from a path."""
        # Mock the detect_repository method to avoid subprocess calls
        with patch.object(repository_service, 'find_repository_root', return_value=git_repo):
            with patch.object(repository_service, 'get_repository_info', return_value={
                "name": "test-repo",
                "path": git_repo,
                "branch": "main"
            }):
                repo_info = await repository_service.detect_repository(git_repo)
                
                assert repo_info is not None
                assert repo_info["name"] == "test-repo"
                assert repo_info["path"] == git_repo
                assert repo_info["branch"] == "main"
    
    @pytest.mark.asyncio
    async def test_initialize_repository_memory_bank(self, repository_service, git_repo):
        """Test initializing a repository memory bank."""
        # Mock the is_git_repository method to avoid subprocess calls
        with patch.object(repository_service, 'is_git_repository', return_value=True):
            with patch.object(repository_service, 'get_repository_info', return_value={
                "name": "test-repo",
                "path": git_repo,
                "branch": "main"
            }):
                # Call the method
                memory_bank = await repository_service.initialize_repository_memory_bank(git_repo)
                
                # Verify that the memory bank was created
                assert memory_bank is not None
                assert memory_bank["type"] == "repository"
                assert memory_bank["path"] == "/path/to/memory-bank"
                assert memory_bank["repo_info"]["name"] == "test-repo"
                
                # Verify that the storage service methods were called
                repository_service.storage_service.create_repository_memory_bank.assert_called_once()
                repository_service.storage_service.register_repository.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_repository_memory_bank_not_git(self, repository_service):
        """Test initializing a repository memory bank for a non-Git directory."""
        # Mock the is_git_repository method to return False
        with patch.object(repository_service, 'is_git_repository', return_value=False):
            # Call the method and expect a ValueError
            with pytest.raises(ValueError):
                await repository_service.initialize_repository_memory_bank("/not/a/git/repo")
