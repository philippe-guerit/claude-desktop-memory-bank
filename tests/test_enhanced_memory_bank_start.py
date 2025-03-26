"""
Test cases for the enhanced memory-bank-start tool.

This test suite validates that the enhanced memory-bank-start function
properly handles all initialization scenarios including project creation
and repository initialization.
"""

import os
import asyncio
import tempfile
import shutil
import subprocess
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

# Import core functionality
from memory_bank_server.core.memory_bank import activate
from memory_bank_server.core.memory_bank import select

class TestEnhancedMemoryBankStart(unittest.TestCase):
    """Test cases for the enhanced memory-bank-start functionality."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a mock context service
        self.context_service = MagicMock()
        
        # Set up mock repository service
        self.repository_service = MagicMock()
        self.repository_service.detect_repository = AsyncMock()
        self.repository_service.detect_repository.return_value = None
        self.repository_service.initialize_repository_memory_bank = AsyncMock()
        self.repository_service.initialize_repository_memory_bank.return_value = {
            "type": "repository",
            "repo_info": {
                "name": "test_repo",
                "path": "/path/to/repo",
                "branch": "main",
                "memory_bank_path": "/path/to/memory-bank"
            }
        }
        self.context_service.repository_service = self.repository_service
        
        # Set up AsyncMock for context service methods
        self.context_service.get_current_memory_bank = AsyncMock()
        self.context_service.get_current_memory_bank.return_value = {"type": "global"}
        
        self.context_service.get_all_context = AsyncMock()
        self.context_service.get_all_context.return_value = {}
        
        self.context_service.set_memory_bank = AsyncMock()
        self.context_service.set_memory_bank.return_value = {"type": "global"}
        
        self.context_service.create_project = AsyncMock()
        self.context_service.create_project.return_value = {
            "name": "test_project",
            "description": "A test project",
            "repository_path": None
        }
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock repository directory
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        
        # Initialize mock repository
        try:
            self._init_mock_repo(self.repo_dir)
        except (subprocess.SubprocessError, OSError):
            # Skip if Git not available
            pass
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def _init_mock_repo(self, repo_path):
        """Initialize a mock Git repository for testing."""
        os.makedirs(repo_path, exist_ok=True)
        os.chdir(repo_path)
        
        # Initialize Git repository
        try:
            subprocess.run(["git", "init"], check=True, capture_output=True)
            
            # Create a dummy file
            with open(os.path.join(repo_path, "README.md"), "w") as f:
                f.write("# Test Repository")
            
            # Add and commit the file
            subprocess.run(["git", "add", "."], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
        except (subprocess.SubprocessError, OSError):
            # Skip if Git not available
            pass
    
    async def _async_test_global_memory_bank(self):
        """Test starting with global memory bank."""
        # Set up mocks for specific test
        self.context_service.set_memory_bank.return_value = {"type": "global"}
        self.context_service.get_current_memory_bank.return_value = {"type": "global"}
        self.context_service.repository_service.detect_repository.return_value = None
        
        # Call activate with no parameters
        result = await activate(self.context_service)
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "global")
        return True
    
    async def _async_test_repository_detection(self):
        """Test repository detection and initialization."""
        # Set up mocks for repository detection
        mock_repo_info = {
            "name": "test_repo",
            "path": self.repo_dir,
            "branch": "main",
            "memory_bank_path": None
        }
        self.context_service.repository_service.detect_repository.return_value = mock_repo_info
        
        # Set up mocks for repository memory bank initialization
        self.repository_service.initialize_repository_memory_bank.return_value = {
            "type": "repository",
            "repo_info": mock_repo_info
        }
        
        # Set up mock for set_memory_bank
        self.context_service.set_memory_bank.return_value = {
            "type": "repository",
            "repo_info": mock_repo_info
        }
        
        # Call activate with repository path
        result = await activate(
            self.context_service,
            current_path=self.repo_dir
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "repository")
        self.assertIn("Detected repository", " ".join(result["actions_taken"]))
        return True
    
    async def _async_test_project_creation(self):
        """Test project creation without repository."""
        # Set up mocks for repository detection
        self.context_service.repository_service.detect_repository.return_value = None
        
        # Set up mocks for project creation
        self.context_service.create_project.return_value = {
            "name": "test_project",
            "description": "A test project",
            "repository_path": None
        }
        
        # Set up mock for set_memory_bank
        self.context_service.set_memory_bank.return_value = {
            "type": "project",
            "project": "test_project"
        }
        
        # Call activate with project parameters
        result = await activate(
            self.context_service,
            project_name="test_project",
            project_description="A test project"
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "project")
        self.assertIn("Created project", " ".join(result["actions_taken"]))
        return True
    
    async def _async_test_project_with_repository(self):
        """Test project creation associated with repository."""
        # Set up mocks for repository detection
        mock_repo_info = {
            "name": "test_repo",
            "path": self.repo_dir,
            "branch": "main",
            "memory_bank_path": None
        }
        self.context_service.repository_service.detect_repository.return_value = mock_repo_info
        
        # Set up mocks for project creation
        self.context_service.create_project.return_value = {
            "name": "test_project",
            "description": "A test project",
            "repository_path": self.repo_dir
        }
        
        # Set up mock for set_memory_bank
        self.context_service.set_memory_bank.return_value = {
            "type": "project",
            "project": "test_project"
        }
        
        # Call activate with project parameters and repository path
        result = await activate(
            self.context_service,
            current_path=self.repo_dir,
            project_name="test_project",
            project_description="A test project"
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "project")
        actions = " ".join(result["actions_taken"])
        self.assertIn("Created project", actions)
        self.assertIn("project with repository", actions)
        return True
    
    async def _async_test_existing_repository_memory_bank(self):
        """Test detection of existing repository memory bank."""
        # Set up mocks for repository detection with existing memory bank
        memory_bank_path = os.path.join(self.repo_dir, ".claude-memory")
        os.makedirs(memory_bank_path, exist_ok=True)
        
        mock_repo_info = {
            "name": "test_repo",
            "path": self.repo_dir,
            "branch": "main",
            "memory_bank_path": memory_bank_path
        }
        self.context_service.repository_service.detect_repository.return_value = mock_repo_info
        
        # Set up mock for set_memory_bank
        self.context_service.set_memory_bank.return_value = {
            "type": "repository",
            "repo_info": mock_repo_info
        }
        
        # Call activate with repository path
        result = await activate(
            self.context_service,
            current_path=self.repo_dir
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "repository")
        actions = " ".join(result["actions_taken"])
        self.assertIn("existing repository memory bank", actions)
        return True
    
    async def _async_test_force_type(self):
        """Test forced memory bank type selection."""
        # Set up mock for set_memory_bank
        self.context_service.set_memory_bank.return_value = {"type": "global"}
        
        # Call activate with forced global type
        result = await activate(
            self.context_service,
            force_type="global"
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "global")
        self.assertIn("Forced selection of global memory bank", " ".join(result["actions_taken"]))
        return True
    
    def test_global_memory_bank(self):
        """Test starting with global memory bank."""
        result = asyncio.run(self._async_test_global_memory_bank())
        self.assertTrue(result)
    
    def test_repository_detection(self):
        """Test repository detection and initialization."""
        result = asyncio.run(self._async_test_repository_detection())
        self.assertTrue(result)
    
    def test_project_creation(self):
        """Test project creation without repository."""
        result = asyncio.run(self._async_test_project_creation())
        self.assertTrue(result)
    
    def test_project_with_repository(self):
        """Test project creation associated with repository."""
        result = asyncio.run(self._async_test_project_with_repository())
        self.assertTrue(result)
    
    def test_existing_repository_memory_bank(self):
        """Test detection of existing repository memory bank."""
        result = asyncio.run(self._async_test_existing_repository_memory_bank())
        self.assertTrue(result)
    
    def test_force_type(self):
        """Test forced memory bank type selection."""
        result = asyncio.run(self._async_test_force_type())
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
