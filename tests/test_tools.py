import os
import unittest
import tempfile
import shutil
import asyncio
import json
import subprocess
from pathlib import Path

# Try to import memory_bank modules, skip tests if dependencies are missing
try:
    from memory_bank_server.repository_utils import RepositoryUtils
    from memory_bank_server.storage_manager import StorageManager
    from memory_bank_server.memory_bank_selector import MemoryBankSelector
    from memory_bank_server.context_manager import ContextManager
    from memory_bank_server.server import MemoryBankServer
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Skipping tests due to missing dependency: {e}")
    DEPENDENCIES_AVAILABLE = False

@unittest.skipIf(not DEPENDENCIES_AVAILABLE, "One or more dependencies not available")
class TestMemoryBankTools(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create storage structure
        self.storage_path = os.path.join(self.temp_dir, "storage")
        os.makedirs(os.path.join(self.storage_path, "global"))
        os.makedirs(os.path.join(self.storage_path, "projects"))
        os.makedirs(os.path.join(self.storage_path, "repositories"))
        os.makedirs(os.path.join(self.storage_path, "templates"))
        
        # Create template files
        template_files = {
            "projectbrief.md": "# Project Brief\n\n## Purpose\n\n## Goals\n\n## Requirements\n\n## Scope\n",
            "productContext.md": "# Product Context\n\n## Problem\n\n## Solution\n\n## User Experience\n\n## Stakeholders\n",
            "systemPatterns.md": "# System Patterns\n\n## Architecture\n\n## Patterns\n\n## Decisions\n\n## Relationships\n",
            "techContext.md": "# Technical Context\n\n## Technologies\n\n## Setup\n\n## Constraints\n\n## Dependencies\n",
            "activeContext.md": "# Active Context\n\n## Current Focus\n\n## Recent Changes\n\n## Next Steps\n\n## Active Decisions\n",
            "progress.md": "# Progress\n\n## Completed\n\n## In Progress\n\n## Pending\n\n## Issues\n"
        }
        
        for filename, content in template_files.items():
            with open(os.path.join(self.storage_path, "templates", filename), 'w') as f:
                f.write(content)
        
        # Initialize components
        self.storage_manager = StorageManager(self.storage_path)
        self.memory_bank_selector = MemoryBankSelector(self.storage_manager)
        self.context_manager = ContextManager(self.storage_manager, self.memory_bank_selector)
        
        # Initialize the server
        self.server = MemoryBankServer(self.storage_path)
        
        # Initialize async components
        asyncio.run(self.async_setup())
        
        # Create test git repository
        self.repo_dir = os.path.join(self.temp_dir, "test-repo")
        os.makedirs(self.repo_dir)
        self.init_git_repo(self.repo_dir)
    
    def init_git_repo(self, repo_path):
        """Initialize a git repository for testing."""
        try:
            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            
            # Create a test file
            with open(os.path.join(repo_path, "README.md"), "w") as f:
                f.write("# Test Repository\n\nThis is a test repository for Memory Bank tests.")
            
            # Add and commit the file
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to initialize git repository: {e}")
            # Mark as not a git repo for tests
            self.git_available = False
        else:
            self.git_available = True
    
    async def async_setup(self):
        # Initialize the memory bank
        await self.server.initialize()
    
    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_select_memory_bank_global(self):
        """Test selecting global memory bank."""
        # Access the tool handler directly from the context manager
        result = asyncio.run(self.context_manager.set_memory_bank())
        
        # Verify the result
        self.assertEqual(result["type"], "global")
    
    def test_select_memory_bank_project(self):
        """Test selecting project memory bank."""
        # First create a project
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Then select it
        result = asyncio.run(self.context_manager.set_memory_bank(
            claude_project="test-project"
        ))
        
        # Verify the result
        self.assertEqual(result["type"], "project")
        self.assertEqual(result["project"], "test-project")
    
    def test_select_memory_bank_repository(self):
        """Test selecting repository memory bank."""
        # Skip if git is not available
        if not self.git_available:
            self.skipTest("Git not available")
        
        # First initialize repository memory bank
        asyncio.run(self.context_manager.initialize_repository_memory_bank(
            self.repo_dir
        ))
        
        # Then select it
        result = asyncio.run(self.context_manager.set_memory_bank(
            repository_path=self.repo_dir
        ))
        
        # Verify the result
        self.assertEqual(result["type"], "repository")
        repo_info = result.get("repo_info", {})
        self.assertEqual(repo_info.get("name", ""), "test-repo")
    
    def test_create_project(self):
        """Test creating a new project."""
        project = asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Verify the result
        self.assertEqual(project["name"], "test-project")
        self.assertEqual(project["description"], "Test project description")
        
        # Check that project files were created
        project_path = os.path.join(self.storage_path, "projects", "test-project")
        self.assertTrue(os.path.exists(project_path))
        self.assertTrue(os.path.exists(os.path.join(project_path, "projectbrief.md")))
    
    def test_create_project_with_repository(self):
        """Test creating a new project with repository."""
        # Skip if git is not available
        if not self.git_available:
            self.skipTest("Git not available")
        
        project = asyncio.run(self.context_manager.create_project(
            "test-project-repo", 
            "Test project with repository",
            self.repo_dir
        ))
        
        # Verify the result
        self.assertEqual(project["name"], "test-project-repo")
        self.assertEqual(project["description"], "Test project with repository")
        self.assertEqual(project["repository"], self.repo_dir)
    
    def test_list_memory_banks(self):
        """Test listing all memory banks."""
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # If git is available, create a repository memory bank
        if self.git_available:
            asyncio.run(self.context_manager.initialize_repository_memory_bank(
                self.repo_dir
            ))
        
        memory_banks = asyncio.run(self.context_manager.get_memory_banks())
        
        # Verify global memory banks
        self.assertIn("global", memory_banks)
        self.assertTrue(len(memory_banks["global"]) > 0)
        
        # Verify project memory banks
        self.assertIn("projects", memory_banks)
        project_names = [p["name"] for p in memory_banks["projects"]]
        self.assertIn("test-project", project_names)
        
        # Verify repository memory banks if git is available
        if self.git_available:
            self.assertIn("repositories", memory_banks)
            repo_names = [r["name"] for r in memory_banks["repositories"]]
            self.assertIn("test-repo", repo_names)
    
    def test_detect_repository(self):
        """Test detecting a Git repository."""
        # Skip if git is not available
        if not self.git_available:
            self.skipTest("Git not available")
        
        repo_info = asyncio.run(self.context_manager.detect_repository(
            self.repo_dir
        ))
        
        # Verify the result
        self.assertIsNotNone(repo_info)
        self.assertEqual(repo_info["name"], "test-repo")
        self.assertEqual(repo_info["path"], self.repo_dir)
    
    def test_detect_repository_negative(self):
        """Test detecting a directory that is not a Git repository."""
        non_repo_dir = os.path.join(self.temp_dir, "not-a-repo")
        os.makedirs(non_repo_dir)
        
        repo_info = asyncio.run(self.context_manager.detect_repository(
            non_repo_dir
        ))
        
        # Verify the result - should be None for non-repository
        self.assertIsNone(repo_info)
    
    def test_initialize_repository_memory_bank(self):
        """Test initializing a repository memory bank."""
        # Skip if git is not available
        if not self.git_available:
            self.skipTest("Git not available")
        
        memory_bank = asyncio.run(self.context_manager.initialize_repository_memory_bank(
            self.repo_dir
        ))
        
        # Verify the result
        self.assertEqual(memory_bank["type"], "repository")
        repo_info = memory_bank.get("repo_info", {})
        self.assertEqual(repo_info.get("name", ""), "test-repo")
        
        # Check that memory bank files were created
        # Get memory bank path from the result
        memory_bank_path = memory_bank["path"]
        self.assertTrue(os.path.exists(memory_bank_path))
        self.assertTrue(os.path.exists(os.path.join(memory_bank_path, "projectbrief.md")))
    
    def test_initialize_repository_with_project(self):
        """Test initializing a repository memory bank with a project."""
        # Skip if git is not available
        if not self.git_available:
            self.skipTest("Git not available")
        
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        memory_bank = asyncio.run(self.context_manager.initialize_repository_memory_bank(
            self.repo_dir,
            "test-project"
        ))
        
        # Verify the result
        self.assertEqual(memory_bank["type"], "repository")
        self.assertEqual(memory_bank["project"], "test-project")
    
    def test_update_context(self):
        """Test updating a context file."""
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Update context
        new_content = "# Updated Project Brief\n\n## Purpose\nTest purpose\n\n## Goals\nTest goals\n"
        memory_bank = asyncio.run(self.context_manager.update_context(
            "project_brief",
            new_content
        ))
        
        # Verify the result
        self.assertEqual(memory_bank["type"], "project")
        self.assertEqual(memory_bank["project"], "test-project")
        
        # Verify content was updated
        updated_content = asyncio.run(self.context_manager.get_context("project_brief"))
        self.assertEqual(updated_content, new_content)
    
    def test_search_context(self):
        """Test searching through context files."""
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Update context with searchable content
        asyncio.run(self.context_manager.update_context(
            "project_brief",
            "# Project Brief\n\n## Purpose\nTest SEARCHABLE content\n\n## Goals\nMore test content\n"
        ))
        
        # Search for content
        results = asyncio.run(self.context_manager.search_context(
            "searchable"
        ))
        
        # Verify the result
        self.assertIn("project_brief", results)
        self.assertTrue(any("searchable" in line.lower() for line in results["project_brief"]))
    
    def test_bulk_update_context(self):
        """Test updating multiple context files in one operation."""
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Prepare updates
        updates = {
            "project_brief": "# Updated Project Brief\n\n## Purpose\nTest purpose\n\n## Goals\nTest goals\n",
            "tech_context": "# Updated Technical Context\n\n## Technologies\nTest technologies\n\n## Dependencies\nTest dependencies\n"
        }
        
        # Execute bulk update
        memory_bank = asyncio.run(self.context_manager.bulk_update_context(updates))
        
        # Verify the result
        self.assertEqual(memory_bank["type"], "project")
        self.assertEqual(memory_bank["project"], "test-project")
        
        # Verify content was updated
        brief_content = asyncio.run(self.context_manager.get_context("project_brief"))
        tech_content = asyncio.run(self.context_manager.get_context("tech_context"))
        
        self.assertEqual(brief_content, updates["project_brief"])
        self.assertEqual(tech_content, updates["tech_context"])
    
    def test_auto_summarize_context(self):
        """Test automatically extracting and updating context from conversation."""
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Prepare test conversation
        conversation = """
Let's discuss the project requirements and goals.
We need to build a system that can handle user authentication.
This is a requirement from the stakeholders.

For the technical setup, we'll use Python with Flask.
We should also consider using MongoDB as our database.

The current focus should be on setting up the authentication system.
We've recently changed our approach to use JWT for tokens.

We've completed the initial database schema design.
The API documentation is currently in progress.
"""
        
        # Execute auto summarization
        suggested_updates = asyncio.run(self.context_manager.auto_summarize_context(conversation))
        
        # Verify that relevant contexts were identified and content looks correct
        self.assertTrue(len(suggested_updates) > 0)
        
        # Apply the suggested updates
        memory_bank = asyncio.run(self.context_manager.bulk_update_context(suggested_updates))
        
        # Verify content was updated with relevant information
        if "project_brief" in suggested_updates:
            brief_content = asyncio.run(self.context_manager.get_context("project_brief"))
            self.assertIn("requirement", brief_content.lower())
        
        if "tech_context" in suggested_updates:
            tech_content = asyncio.run(self.context_manager.get_context("tech_context"))
            self.assertIn("python", tech_content.lower())
    
    def test_prune_context(self):
        """Test removing outdated information from context files."""
        # Create a project first
        asyncio.run(self.context_manager.create_project(
            "test-project", 
            "Test project description"
        ))
        
        # Add dated content to a context file
        from datetime import datetime, timedelta
        
        today = datetime.utcnow()
        date_old = (today - timedelta(days=120)).strftime("%Y-%m-%d")
        date_recent = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        
        content = f"""# Test Content

## Main Section
This is the main content.

## Update {date_old}
This is an old update that should be pruned.

## Update {date_recent}
This is a recent update that should be preserved.
"""
        
        # Update context with dated content
        asyncio.run(self.context_manager.update_context(
            "project_brief",
            content
        ))
        
        # Execute pruning
        pruning_results = asyncio.run(self.context_manager.prune_context(max_age_days=90))
        
        # Verify results if any sections were pruned
        if "project_brief" in pruning_results:
            self.assertGreater(pruning_results["project_brief"].get("pruned_sections", 0), 0)
        
        # Verify old content was pruned
        pruned_content = asyncio.run(self.context_manager.get_context("project_brief"))
        
        self.assertIn("## Main Section", pruned_content)
        self.assertIn(f"## Update {date_recent}", pruned_content)
        self.assertNotIn(f"## Update {date_old}", pruned_content)

if __name__ == '__main__':
    unittest.main()
