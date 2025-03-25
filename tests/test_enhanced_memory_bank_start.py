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
from unittest.mock import MagicMock, patch

# Import core functionality
from memory_bank_server.core.memory_bank import start_memory_bank
from memory_bank_server.core.memory_bank import select_memory_bank

class TestEnhancedMemoryBankStart(unittest.TestCase):
    """Test cases for the enhanced memory-bank-start functionality."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a mock context service
        self.context_service = MagicMock()
        self.context_service.get_current_memory_bank.return_value = {"type": "global"}
        self.context_service.get_all_context.return_value = {}
        
        # Make all async method returns non-awaitable
        self.context_service.set_memory_bank = lambda **kwargs: {"type": kwargs.get("type", "global"), "project": kwargs.get("project_name"), "repo_info": {"path": kwargs.get("repository_path")}}
        self.context_service.repository_service = MagicMock()
        self.context_service.repository_service.detect_repository = lambda path: None
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock repository directory
        self.repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.repo_dir)
        
        # Initialize mock repository
        self._init_mock_repo(self.repo_dir)
    
    def tearDown(self):
        """Clean up after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def _init_mock_repo(self, repo_path):
        """Initialize a mock Git repository for testing."""
        os.makedirs(repo_path, exist_ok=True)
        os.chdir(repo_path)
        
        # Initialize Git repository
        subprocess.run(["git", "init"], check=True, capture_output=True)
        
        # Create a dummy file
        with open(os.path.join(repo_path, "README.md"), "w") as f:
            f.write("# Test Repository")
        
        # Add and commit the file
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)
    
    async def _async_test_global_memory_bank(self):
        """Test starting with global memory bank."""
        # Mock necessary functionality
        self.context_service.set_memory_bank.return_value = {"type": "global"}
        self.context_service.get_current_memory_bank.return_value = {"type": "global"}
        
        # Make repository_service.detect_repository return a non-awaitable result
        self.context_service.repository_service.detect_repository = lambda path: None
        
        # Call start_memory_bank with no parameters
        result = await start_memory_bank(self.context_service)
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "global")
        return True
    
    async def _async_test_repository_detection(self):
        """Test repository detection and initialization."""
        # Mock repository detection
        mock_repo_info = {
            "name": "test_repo",
            "path": self.repo_dir,
            "branch": "main",
            "memory_bank_path": None
        }
        # Override the lambda with a specific return value for this test
        self.context_service.repository_service.detect_repository = lambda path: mock_repo_info if path == self.repo_dir else None
        
        # Call start_memory_bank with repository path
        result = await start_memory_bank(
            self.context_service,
            current_path=self.repo_dir
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "repository")
        self.assertIn("Detected repository", " ".join(result["actions_taken"]))
        return True
    
    async def _async_test_project_creation(self):
        """Test project creation without repository."""
        # Override the set_memory_bank lambda for this test
        self.context_service.set_memory_bank = lambda **kwargs: {
            "type": "project",
            "project": "test_project"
        } if kwargs.get("type") == "project" and kwargs.get("project_name") == "test_project" else {"type": "global"}
        
        # Call start_memory_bank with project parameters
        result = await start_memory_bank(
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
        # Mock repository detection
        mock_repo_info = {
            "name": "test_repo",
            "path": self.repo_dir,
            "branch": "main",
            "memory_bank_path": None
        }
        self.context_service.repository_service.detect_repository = lambda path: mock_repo_info if path == self.repo_dir else None
        
        # Override the set_memory_bank lambda for this test
        self.context_service.set_memory_bank = lambda **kwargs: {
            "type": "project",
            "project": "test_project"
        } if kwargs.get("type") == "project" and kwargs.get("project_name") == "test_project" else {"type": "global"}
        
        # Call start_memory_bank with project parameters and repository path
        result = await start_memory_bank(
            self.context_service,
            current_path=self.repo_dir,
            project_name="test_project",
            project_description="A test project"
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "project")
        actions = " ".join(result["actions_taken"])
        self.assertIn("Created project", actions)
        self.assertIn("Associated project with repository", actions)
        return True
    
    async def _async_test_existing_repository_memory_bank(self):
        """Test detection of existing repository memory bank."""
        # Mock repository detection with existing memory bank
        mock_repo_info = {
            "name": "test_repo",
            "path": self.repo_dir,
            "branch": "main",
            "memory_bank_path": os.path.join(self.repo_dir, ".claude-memory")
        }
        self.context_service.repository_service.detect_repository = lambda path: mock_repo_info if path == self.repo_dir else None
        
        # Create fake memory bank path
        os.makedirs(os.path.join(self.repo_dir, ".claude-memory"), exist_ok=True)
        
        # Override the set_memory_bank lambda for this test
        self.context_service.set_memory_bank = lambda **kwargs: {
            "type": "repository",
            "repo_info": mock_repo_info
        } if kwargs.get("type") == "repository" and kwargs.get("repository_path") == self.repo_dir else {"type": "global"}
        
        # Call start_memory_bank with repository path
        result = await start_memory_bank(
            self.context_service,
            current_path=self.repo_dir
        )
        
        # Verify result
        self.assertEqual(result["selected_memory_bank"]["type"], "repository")
        self.assertIn("Using existing repository memory bank", " ".join(result["actions_taken"]))
        return True
    
    async def _async_test_force_type(self):
        """Test forced memory bank type selection."""
        # Override the set_memory_bank lambda for this test
        self.context_service.set_memory_bank = lambda **kwargs: {"type": "global"}
        
        # Call start_memory_bank with forced global type
        result = await start_memory_bank(
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
